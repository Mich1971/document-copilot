"""Unit tests for retrieval queries with mocked DB."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.queries import _filter_stop_words, _prepare_websearch_query, lexical_search, semantic_search


def test_prepare_websearch_query_preserves_numbers():
    assert _prepare_websearch_query("10-K revenue growth") == "10-K revenue growth"


def test_prepare_websearch_query_collapses_whitespace():
    assert _prepare_websearch_query("  Apple   10-K  ") == "Apple 10-K"


def test_prepare_websearch_query_removes_stop_words():
    assert _prepare_websearch_query("What are the risks") == "risks"


def test_prepare_websearch_query_empty_after_filter():
    assert _prepare_websearch_query("the a an") == ""


def test_prepare_websearch_query_empty_string():
    assert _prepare_websearch_query("") == ""


def test_filter_stop_words_basic():
    assert _filter_stop_words("the quick brown fox") == "quick brown fox"


def _make_mock_row(row_id, score):
    mock_row = MagicMock()
    mock_row.__getitem__.side_effect = lambda idx: [row_id, score][idx]
    return mock_row


def test_semantic_search_returns_scores(monkeypatch):
    chunk_id = uuid.uuid4()
    mock_row = _make_mock_row(chunk_id, 0.85)

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
    mock_row = _make_mock_row(chunk_id, 1.5)

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
