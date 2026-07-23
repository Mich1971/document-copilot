"""Turn orchestrator: retrieval → agent → validation → stream."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import AsyncIterator

from openai import APIError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic_ai import ModelAPIError

from app.assistant.agent import agent
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.auth.dependencies import CurrentUser
from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever
from app.retrieval.schemas import Passage, RetrievalResult


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
        async with agent.run_stream(user_message, deps=deps) as result:
            streamed = False
            prev_text = ""
            async for pa in result.stream_output():
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
    except (ModelAPIError, APIError):
        yield "No pude generar la respuesta en este momento. Por favor vuelve a intentarlo."
        return

    state.answer = await result.get_output()
    GroundingValidator().validate(state.answer, state.retrieval.passages)
    state.passages = state.retrieval.passages
