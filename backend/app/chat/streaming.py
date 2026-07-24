"""AI SDK v5-compatible SSE streaming helpers.

Corrige dos problemas respecto a la versión anterior:

1. Formato: AI SDK v5 espera Server-Sent Events real (prefijo "data: " y
   doble salto de línea "\\n\\n" como delimitador de evento), no NDJSON
   crudo. Sin esto, DefaultChatTransport en el cliente no logra parsear
   los chunks y el mensaje del asistente queda vacío durante el streaming.

2. Tipos de data parts personalizados: cualquier chunk que no sea uno de
   los tipos nativos del protocolo (text-start/delta/end, start, finish,
   error, etc.) DEBE usar el prefijo "data-" en su "type" (ej. "data-citation",
   "data-status"). Un tipo custom sin ese prefijo (como "citation" o
   "status" en la versión anterior) hace que el SDK lance un error al
   parsear el mensaje, rompiendo el stream completo apenas llega ese chunk.

Uso esperado en el endpoint (StreamingResponse de FastAPI):

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"x-vercel-ai-ui-message-stream": "v1"},
    )

Y dentro del generador, la secuencia típica por mensaje es:

    yield stream_start()
    yield stream_text_start(message_id)
    for delta in ...:
        yield stream_text_delta(message_id, delta)
    for citation in ...:
        yield stream_citation(message_id, citation)
    yield stream_text_end(message_id)
    yield stream_finish()
"""

from __future__ import annotations

import json
import uuid

from app.assistant.outputs import Citation


def _sse(payload: dict) -> str:
    """Formatea un dict como un evento SSE válido para AI SDK v5."""
    return f"data: {json.dumps(payload)}\n\n"


def stream_start() -> str:
    """Marca el inicio del mensaje. Envíalo una vez, antes de cualquier texto."""
    return _sse({"type": "start"})


def stream_finish() -> str:
    """Marca el fin del mensaje. Envíalo una vez, al terminar todo el streaming."""
    return _sse({"type": "finish"})


def stream_text_start(message_id: uuid.UUID) -> str:
    return _sse({"type": "text-start", "id": str(message_id)})


def stream_text_delta(message_id: uuid.UUID, delta: str) -> str:
    return _sse({"type": "text-delta", "id": str(message_id), "delta": delta})


def stream_text_end(message_id: uuid.UUID) -> str:
    return _sse({"type": "text-end", "id": str(message_id)})


def stream_error(error: str) -> str:
    return _sse({"type": "error", "errorText": error})


def stream_citation(message_id: uuid.UUID, citation: Citation) -> str:
    """
    Data part personalizado para una citación. El tipo usa el prefijo
    "data-" requerido por el protocolo, y el payload va anidado bajo "data"
    (así lo espera useChat: message.parts con type "data-citation" y
    campo .data con el contenido).
    """
    return _sse({
        "type": "data-citation",
        "id": str(message_id),
        "data": citation.model_dump(mode="json"),
    })


def stream_status(message_id: uuid.UUID, stage: str, progress: float, message: str) -> str:
    """
    Data part personalizado de estado del pipeline (retrieval/generation/
    grounding/complete). Al reutilizar el mismo "id" en llamadas sucesivas,
    el cliente reconcilia automáticamente el part en vez de acumular varios.
    """
    return _sse({
        "type": "data-status",
        "id": str(message_id),
        "data": {
            "stage": stage,
            "progress": progress,
            "message": message,
        },
    })
