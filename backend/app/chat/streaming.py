"""AI SDK-compatible NDJSON streaming helpers."""

from __future__ import annotations

import json
import uuid

from app.assistant.outputs import Citation


def stream_text_start(message_id: uuid.UUID) -> str:
    return json.dumps({"type": "text-start", "id": str(message_id)}) + "\n"


def stream_text_delta(message_id: uuid.UUID, delta: str) -> str:
    return json.dumps({"type": "text-delta", "id": str(message_id), "delta": delta}) + "\n"


def stream_text_end(message_id: uuid.UUID) -> str:
    return json.dumps({"type": "text-end", "id": str(message_id)}) + "\n"


def stream_error(message_id: uuid.UUID, error: str) -> str:
    return json.dumps({"type": "error", "id": str(message_id), "error": error}) + "\n"


def stream_citation(message_id: uuid.UUID, citation: Citation) -> str:
    return json.dumps({
        "type": "citation",
        "id": str(message_id),
        "citation": citation.model_dump(mode="json"),
    }) + "\n"


def stream_status(message_id: uuid.UUID, stage: str, progress: float, message: str) -> str:
    return json.dumps({
        "type": "status",
        "id": str(message_id),
        "stage": stage,
        "progress": progress,
        "message": message,
    }) + "\n"
