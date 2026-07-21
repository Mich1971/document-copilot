"""Unit tests for Reciprocal Rank Fusion."""

from __future__ import annotations

import uuid

import pytest

from app.retrieval.fusion import reciprocal_rank_fusion


def _chunk_id(index: int) -> uuid.UUID:
    return uuid.UUID(f"00000000-0000-0000-0000-{index:012d}")


def test_rrf_merges_disjoint_lists():
    semantic = [(_chunk_id(1), 0.9), (_chunk_id(2), 0.8)]
    lexical = [(_chunk_id(3), 0.7), (_chunk_id(4), 0.6)]

    result = reciprocal_rank_fusion(semantic, lexical, k=60)

    assert len(result) == 4
    ids = [chunk_id for chunk_id, _score in result]
    assert set(ids) == {_chunk_id(1), _chunk_id(2), _chunk_id(3), _chunk_id(4)}
    assert ids[0] == _chunk_id(1)
    assert ids[1] == _chunk_id(3)


def test_rrf_combines_duplicate_ids():
    semantic = [(_chunk_id(1), 0.9)]
    lexical = [(_chunk_id(1), 0.5)]

    result = reciprocal_rank_fusion(semantic, lexical, k=60)

    assert len(result) == 1
    assert result[0][0] == _chunk_id(1)
    expected = 1.0 / (60 + 1) + 1.0 / (60 + 1)
    assert abs(result[0][1] - expected) < 1e-9


def test_rrf_empty_lists():
    assert reciprocal_rank_fusion([], []) == []
    assert reciprocal_rank_fusion([(_chunk_id(1), 0.9)], []) == [(_chunk_id(1), 1.0 / (60 + 1))]
    assert reciprocal_rank_fusion([], [(_chunk_id(2), 0.8)]) == [(_chunk_id(2), 1.0 / (60 + 1))]


def test_rrf_k_parameter_influence():
    semantic = [(_chunk_id(1), 0.9)]
    lexical = [(_chunk_id(1), 0.5)]

    result_k1 = reciprocal_rank_fusion(semantic, lexical, k=1)
    result_k100 = reciprocal_rank_fusion(semantic, lexical, k=100)

    assert result_k1[0][1] > result_k100[0][1]
