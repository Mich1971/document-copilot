"""Reciprocal Rank Fusion for hybrid retrieval."""

from __future__ import annotations

import uuid
from collections import defaultdict


def reciprocal_rank_fusion(
    semantic: list[tuple[uuid.UUID, float]],
    lexical: list[tuple[uuid.UUID, float]],
    *,
    k: int = 60,
) -> list[tuple[uuid.UUID, float]]:
    """Fuse two ranked lists using Reciprocal Rank Fusion.

    Args:
        semantic: Ranked list of (chunk_id, score) from dense retrieval.
        lexical: Ranked list of (chunk_id, score) from lexical retrieval.
        k: RRF constant. Higher k reduces the impact of individual ranks.

    Returns:
        Sorted list of (chunk_id, rrf_score) descending by score.
    """
    scores: dict[uuid.UUID, float] = defaultdict(float)

    for rank, (chunk_id, _score) in enumerate(semantic, start=1):
        scores[chunk_id] += 1.0 / (k + rank)

    for rank, (chunk_id, _score) in enumerate(lexical, start=1):
        scores[chunk_id] += 1.0 / (k + rank)

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return ranked
