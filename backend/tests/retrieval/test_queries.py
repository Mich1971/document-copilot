"""Unit tests for retrieval queries with mocked DB."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.queries import _sanitize_query, lexical_search, semantic_search


def test_sanitize_query_basic():
    assert _sanitize_query("Hola mundo") == "hola:* & mundo:*"


def test_sanitize_query_empty():
    assert _sanitize_query("") == ""


def test_sanitize_query_special_chars():
    assert _sanitize_query("¿Cómo estás?") == "cómo:* & estás:*"


def test_semantic_search_returns_scores(monkeypatch):
    chunk_id = uuid.uuid4()
    mock_row = MagicMock()
    mock_row.id = chunk_id
    mock_row.score = 0.85

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def mock_embed_text(client, text, **kwargs):
        mock_result = MagicMock()
        mock_result.vector = [0.1] * 2048
        return mock_result

    monkeypatch.setattr(
        "app.retrieval.queries.get_embedding_client",
        lambda: MagicMock(),
    )
    monkeypatch.setattr(
        "app.retrieval.queries.embed_text",
        mock_embed_text,
    )

    results = asyncio.run(semantic_search(mock_session, "test query", k=10))

    assert len(results) == 1
    assert results[0] == (chunk_id, 0.85)


def test_lexical_search_returns_scores(monkeypatch):
    chunk_id = uuid.uuid4()
    mock_row = MagicMock()
    mock_row.id = chunk_id
    mock_row.score = 1.5

    mock_result = MagicMock()
    mock_result.all.return_value = [mock_row]

    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(return_value=mock_result)

    results = asyncio.run(lexical_search(mock_session, "test query", k=10))

    assert len(results) == 1
    assert results[0] == (chunk_id, 1.5)


def test_lexical_search_empty_query(monkeypatch):
    results = asyncio.run(lexical_search(MagicMock(spec=AsyncSession), "", k=10))
    assert results == []
