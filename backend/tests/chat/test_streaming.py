"""Unit tests for NDJSON streaming helpers."""

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


def test_stream_text_start():
    mid = uuid.uuid4()
    line = stream_text_start(mid)
    payload = json.loads(line)
    assert payload == {"type": "text-start", "id": str(mid)}


def test_stream_text_delta():
    mid = uuid.uuid4()
    line = stream_text_delta(mid, "hello")
    payload = json.loads(line)
    assert payload == {"type": "text-delta", "id": str(mid), "delta": "hello"}


def test_stream_text_end():
    mid = uuid.uuid4()
    line = stream_text_end(mid)
    payload = json.loads(line)
    assert payload == {"type": "text-end", "id": str(mid)}


def test_stream_error():
    mid = uuid.uuid4()
    line = stream_error(mid, "boom")
    payload = json.loads(line)
    assert payload == {"type": "error", "id": str(mid), "error": "boom"}


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
    payload = json.loads(line)
    assert payload["type"] == "citation"
    assert payload["id"] == str(mid)
    assert payload["citation"]["excerpt"] == "test excerpt"
    assert payload["citation"]["ticker"] == "AAPL"
