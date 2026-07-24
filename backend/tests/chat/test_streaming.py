"""Unit tests for SSE streaming helpers."""

from __future__ import annotations

import json
import uuid
from datetime import date

from app.assistant.outputs import Citation
from app.chat.streaming import (
    stream_citation,
    stream_error,
    stream_text_delta,
    stream_text_end,
    stream_text_start,
)


def _parse_sse(line: str) -> dict:
    return json.loads(line.split("data: ", 1)[1].strip())


def test_stream_text_start():
    mid = uuid.uuid4()
    line = stream_text_start(mid)
    payload = _parse_sse(line)
    assert payload == {"type": "text-start", "id": str(mid)}


def test_stream_text_delta():
    mid = uuid.uuid4()
    line = stream_text_delta(mid, "hello")
    payload = _parse_sse(line)
    assert payload == {"type": "text-delta", "id": str(mid), "delta": "hello"}


def test_stream_text_end():
    mid = uuid.uuid4()
    line = stream_text_end(mid)
    payload = _parse_sse(line)
    assert payload == {"type": "text-end", "id": str(mid)}


def test_stream_error():
    line = stream_error("boom")
    payload = _parse_sse(line)
    assert payload == {"type": "error", "errorText": "boom"}


def test_stream_citation():
    mid = uuid.uuid4()
    citation = Citation(
        chunk_id=uuid.uuid4(),
        excerpt="test excerpt",
        ticker="AAPL",
        form="10-K",
        filing_date=date(2024, 1, 1),
    )
    line = stream_citation(mid, citation)
    payload = _parse_sse(line)
    assert payload["type"] == "data-citation"
    assert payload["id"] == str(mid)
    assert payload["data"]["excerpt"] == "test excerpt"
    assert payload["data"]["ticker"] == "AAPL"
