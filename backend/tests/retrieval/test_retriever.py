"""Unit tests for DocumentRetriever with mocked DB."""

from __future__ import annotations

import asyncio
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.retriever import DocumentRetriever
from app.retrieval.schemas import RetrievalResult


def _make_chunk_row(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "document_id": uuid.uuid4(),
        "chunk_index": 0,
        "text": "Sample text",
        "page": "1",
        "section": "Section",
        "token_count": 10,
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "form": "10-K",
        "filing_date": date(2024, 1, 1),
        "accession_number": "ACC-001",
        "source_url": "https://example.com",
    }
    defaults.update(overrides)
    return MagicMock(**defaults)


def test_retriever_returns_result(monkeypatch):
    chunk_id = uuid.uuid4()
    chunk_row = _make_chunk_row(id=chunk_id, chunk_index=0)

    mock_session = MagicMock(spec=AsyncSession)

    semantic_rows = [(chunk_id, 0.9)]
    lexical_rows = [(chunk_id, 0.8)]

    async def mock_semantic(session, query, *, k=50):
        return semantic_rows

    async def mock_lexical(session, query, *, k=50):
        return lexical_rows

    monkeypatch.setattr("app.retrieval.retriever.semantic_search", mock_semantic)
    monkeypatch.setattr("app.retrieval.retriever.lexical_search", mock_lexical)

    mock_result = MagicMock()
    mock_result.all.return_value = [chunk_row]
    mock_session.execute = AsyncMock(return_value=mock_result)

    retriever = DocumentRetriever(mock_session)
    result = asyncio.run(retriever.search("test query", top_k=10))

    assert isinstance(result, RetrievalResult)
    assert result.query == "test query"
    assert len(result.passages) == 1
    assert result.passages[0].chunk_id == chunk_id
    assert result.passages[0].rank == 1


def test_retriever_neighbor_expansion(monkeypatch):
    chunk_id = uuid.uuid4()
    chunk_row = _make_chunk_row(id=chunk_id, chunk_index=1)
    neighbor_row = _make_chunk_row(id=uuid.uuid4(), chunk_index=2)

    mock_session = MagicMock(spec=AsyncSession)

    semantic_rows = [(chunk_id, 0.9)]
    lexical_rows = []

    call_count = 0

    async def mock_semantic(session, query, *, k=50):
        return semantic_rows

    async def mock_lexical(session, query, *, k=50):
        return lexical_rows

    async def mock_execute(stmt):
        nonlocal call_count
        call_count += 1
        mock_result = MagicMock()
        if call_count == 1:
            mock_result.all.return_value = [chunk_row]
        else:
            mock_result.all.return_value = [neighbor_row]
        return mock_result

    monkeypatch.setattr("app.retrieval.retriever.semantic_search", mock_semantic)
    monkeypatch.setattr("app.retrieval.retriever.lexical_search", mock_lexical)
    mock_session.execute = mock_execute

    retriever = DocumentRetriever(mock_session)
    result = asyncio.run(retriever.search("test query", top_k=10))

    assert call_count == 2
    passage_ids = {p.chunk_id for p in result.passages}
    assert chunk_id in passage_ids
