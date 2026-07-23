"""Hybrid retrieval queries: semantic (pgvector) and lexical (full-text)."""

from __future__ import annotations

import re
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.document_chunk import DocumentChunk
from app.ingest.embeddings import get_embedding_client, embed_text


async def semantic_search(
    session: AsyncSession,
    query: str,
    *,
    k: int = 50,
) -> list[tuple[uuid.UUID, float]]:
    """Return top-k chunks by cosine similarity to the query embedding.

    Uses the halfvec(2048) functional index for pgvector compatibility.
    """
    client = get_embedding_client()
    embedding_result = await embed_text(client, query)
    query_vec = embedding_result.vector

    stmt = (
        select(
            DocumentChunk.id,
            text("1 - (embedding <=> :vec)"),
        )
        .where(text("embedding IS NOT NULL"))
        .order_by(text("embedding <=> :vec"))
        .limit(k)
    )

    result = await session.execute(stmt, {"vec": str(query_vec)})
    rows = result.all()
    return [(row[0], float(row[1])) for row in rows]


def _sanitize_query(query: str) -> str:
    """Sanitize query for to_tsquery: keep only word characters, lowercase, add prefix."""
    words = re.findall(r"[^\W\d_]+", query, flags=re.UNICODE)
    if not words:
        return ""
    sanitized = " & ".join(f"{word.lower()}:*" for word in words)
    return sanitized


async def lexical_search(
    session: AsyncSession,
    query: str,
    *,
    k: int = 50,
) -> list[tuple[uuid.UUID, float]]:
    """Return top-k chunks by Postgres full-text search rank.

    Uses the spanish-configured search_vector and GIN index.
    """
    sanitized = _sanitize_query(query)
    if not sanitized:
        return []

    stmt = (
        select(
            DocumentChunk.id,
            text("ts_rank(search_vector, to_tsquery('spanish', :query))"),
        )
        .where(text("search_vector @@ to_tsquery('spanish', :query)"))
        .order_by(text("ts_rank(search_vector, to_tsquery('spanish', :query)) DESC"))
        .limit(k)
    )

    result = await session.execute(stmt, {"query": sanitized})
    rows = result.all()
    return [(row[0], float(row[1])) for row in rows]
