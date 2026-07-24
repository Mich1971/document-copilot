"""Turn orchestrator: retrieval → agent → validation → stream."""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import AsyncIterator

from openai import APIError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_ai import ModelAPIError
from pydantic_ai.exceptions import FallbackExceptionGroup, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits

from app.assistant.agent import agent
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.auth.dependencies import CurrentUser
from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever
from app.retrieval.schemas import Passage, RetrievalResult

logger = logging.getLogger(__name__)

# Tiempo máximo de INACTIVIDAD entre chunks del stream (no el tiempo total
# del turno, que puede ser largo legítimamente en respuestas extensas).
# Si el proveedor deja de emitir bytes por más de esto sin cerrar la
# conexión ni lanzar una excepción, lo tratamos como un stall y abortamos.
STREAM_IDLE_TIMEOUT_SECONDS = 45

# Límite de llamadas a herramientas/requests al modelo por turno, para
# evitar que un loop de tool calls (search_filings/read_chunk/...) deje
# la conexión "pensando" indefinidamente sin generar una respuesta final.
MAX_REQUESTS_PER_TURN = 8


class TurnTimeoutError(Exception):
    """El turno se estancó: no llegaron más datos del modelo a tiempo."""


@dataclass
class TurnState:
    answer: GroundedAnswer | None = None
    passages: list[Passage] | None = None
    retrieval: RetrievalResult | None = None


async def run_turn_stream(
    user_message: str,
    thread_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession,
    state: TurnState,
) -> AsyncIterator[str]:
    retriever = DocumentRetriever(session)
    state.retrieval = await retriever.search(user_message)

    deps = DocumentAgentDeps(
        user_id=current_user.id,
        thread_id=thread_id,
        retriever=retriever,
        passages=state.retrieval.passages,
        session=session,
    )

    try:
        async with agent.run_stream(
            user_message,
            deps=deps,
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS_PER_TURN),
        ) as result:
            streamed = False
            prev_text = ""
            stream_iter = result.stream_output().__aiter__()
            while True:
                try:
                    pa = await asyncio.wait_for(
                        stream_iter.__anext__(), timeout=STREAM_IDLE_TIMEOUT_SECONDS
                    )
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    raise TurnTimeoutError(
                        f"Sin actividad del modelo por más de {STREAM_IDLE_TIMEOUT_SECONDS}s"
                    )
                streamed = True
                text = pa.answer or ""
                if text.startswith(prev_text) and len(text) > len(prev_text):
                    yield text[len(prev_text):]
                    prev_text = text

            if not streamed:
                answer = await result.get_output()
                text = answer.answer or ""
                if text:
                    yield text
    except FallbackExceptionGroup:
        yield "No pude generar la respuesta en este momento. Por favor vuelve a intentarlo."
        return
    except (ModelAPIError, APIError):
        yield "No pude generar la respuesta en este momento. Por favor vuelve a intentarlo."
        return
    except TurnTimeoutError:
        yield "La generación tardó demasiado y fue interrumpida. Por favor vuelve a intentarlo."
        return
    except UsageLimitExceeded:
        yield "La respuesta requirió demasiados pasos internos y fue interrumpida. Por favor vuelve a intentarlo."
        return

    state.answer = await result.get_output()

    if not (state.answer.answer or "").strip():
        # El turno terminó sin excepción (200 OK en tus logs), pero el
        # campo `answer` llegó vacío — el modelo devolvió un GroundedAnswer
        # técnicamente válido pero sin contenido de texto. Sin este check,
        # el stream se cierra en silencio (text-start → text-end → finish,
        # cero deltas) y la UI se queda con una burbuja vacía indefinidamente,
        # aunque el backend nunca reporte ningún error.
        try:
            used_model = result.all_messages()[-1].model_name  # type: ignore[union-attr]
        except Exception:
            used_model = "desconocido"
        logger.warning(
            "El modelo (%s) devolvió un GroundedAnswer con 'answer' vacío para el turno del thread %s",
            used_model,
            thread_id,
        )
        raise ValueError(
            "El modelo no generó contenido de respuesta. Por favor vuelve a intentar tu pregunta."
        )

    GroundingValidator().validate(state.answer, state.retrieval.passages)
    state.passages = state.retrieval.passages
