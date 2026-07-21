"""Unit tests for chat orchestrator with mocked agent/retriever."""

from __future__ import annotations

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.outputs import Citation, GroundedAnswer, SourcePassage
from app.auth.dependencies import CurrentUser
from app.chat.orchestrator import TurnState, run_turn_stream
from app.retrieval.schemas import Passage, RetrievalResult


def _make_passage(chunk_id: uuid.UUID) -> Passage:
    return Passage(
        chunk_id=chunk_id,
        document_id=uuid.uuid4(),
        text="sample text",
        score=1.0,
        rank=1,
        ticker="AAPL",
        form="10-K",
        filing_date=date(2024, 1, 1),
        accession_number="ACC",
        source_url="https://example.com",
    )


def test_orchestrator_streams_text_and_validates(monkeypatch):
    user = CurrentUser(id=uuid.uuid4(), email="test@example.com")
    session = MagicMock(spec=AsyncSession)
    passage = _make_passage(uuid.uuid4())
    retrieval = RetrievalResult(
        passages=[passage],
        query="query",
        semantic_count=1,
        lexical_count=1,
    )

    async def mock_search(query, top_k=10):
        return retrieval

    monkeypatch.setattr("app.chat.orchestrator.DocumentRetriever", lambda s: MagicMock(search=mock_search))

    answer = GroundedAnswer(
        answer="respuesta",
        citations=[
            Citation(
                chunk_id=passage.chunk_id,
                excerpt="excerpt",
                ticker="AAPL",
                form="10-K",
                filing_date=date(2024, 1, 1),
            )
        ],
        cited_passages=[
            SourcePassage(
                chunk_id=passage.chunk_id,
                text="text",
                ticker="AAPL",
                form="10-K",
                filing_date=date(2024, 1, 1),
            )
        ],
    )

    def mock_run_stream(prompt, deps):
        result = MagicMock()

        async def _stream_text():
            yield "hola "
            yield "mundo"

        result.stream_text = _stream_text
        result.get_output.return_value = answer

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=result)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        return mock_cm

    monkeypatch.setattr("app.chat.orchestrator.agent.run_stream", mock_run_stream)

    state = TurnState()

    async def _collect():
        parts = []
        async for delta in run_turn_stream("query", uuid.uuid4(), user, session, state):
            parts.append(delta)
        return parts, state

    parts, final_state = asyncio.run(_collect())
    assert parts == ["hola ", "mundo"]
    assert final_state.answer is answer
    assert final_state.passages == [passage]


def test_orchestrator_validation_failure_stops_stream(monkeypatch):
    user = CurrentUser(id=uuid.uuid4(), email="test@example.com")
    session = MagicMock(spec=AsyncSession)
    passage = _make_passage(uuid.uuid4())
    retrieval = RetrievalResult(
        passages=[passage],
        query="query",
        semantic_count=1,
        lexical_count=1,
    )

    async def mock_search(query, top_k=10):
        return retrieval

    monkeypatch.setattr("app.chat.orchestrator.DocumentRetriever", lambda s: MagicMock(search=mock_search))

    answer = GroundedAnswer(
        answer="respuesta",
        citations=[
            Citation(
                chunk_id=uuid.uuid4(),
                excerpt="excerpt",
                ticker="AAPL",
                form="10-K",
                filing_date=date(2024, 1, 1),
            )
        ],
        cited_passages=[],
    )

    def mock_run_stream(prompt, deps):
        result = MagicMock()

        async def _stream_text():
            yield "hola"

        result.stream_text = _stream_text
        result.get_output.return_value = answer

        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=result)
        mock_cm.__aexit__ = AsyncMock(return_value=False)
        return mock_cm

    monkeypatch.setattr("app.chat.orchestrator.agent.run_stream", mock_run_stream)

    state = TurnState()

    parts = []
    async def _collect():
        async for delta in run_turn_stream("query", uuid.uuid4(), user, session, state):
            parts.append(delta)
        return parts

    with pytest.raises(ValueError, match="not in retrieved passages"):
        asyncio.run(_collect())
    assert parts == ["hola"]
