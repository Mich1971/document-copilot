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


STOP_WORDS = {
    "a", "an", "the", "are", "is", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just",
    "because", "but", "and", "or", "if", "while", "about", "up", "what",
    "which", "who", "whom", "this", "that", "these", "those", "i", "me",
    "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
    "he", "him", "his", "she", "her", "hers", "it", "its", "they", "them",
    "their", "theirs", "am",
    "el", "la", "los", "las", "un", "una", "unos", "unas", "y", "o", "pero",
    "si", "no", "por", "que", "qué", "quién", "cuál", "cómo", "cuándo",
    "dónde", "por qué", "este", "esta", "estos", "estas", "ese", "esa",
    "esos", "esas", "aquel", "aquella", "aquellos", "aquellas", "al", "del",
    "de", "del", "la", "las", "lo", "los", "en", "entre", "hacia", "hasta",
    "para", "por", "según", "sin", "sobre", "tras", "me", "te", "se", "le",
    "les", "nos", "os", "mi", "tu", "su", "nuestro", "vuestro", "mío",
    "tuyo", "suyo", "nuestro", "vuestro", "mía", "tuya", "suya", "míos",
    "tuyos", "suyos", "mías", "tuyas", "suyas", "yo", "tú", "él", "ella",
    "nosotros", "vosotros", "ellos", "ellas", "mismo", "misma", "mismos",
    "mismas", "quien", "cuyo", "cuya", "cuyos", "cuyas", "donde", "cuando",
    "como", "es", "son", "era", "eran", "fue", "fueron", "hay", "había",
    "haya", "hubo", "ser", "siendo", "sido", "estar", "estando", "estado",
    "tener", "teniendo", "tenido", "hacer", "haciendo", "hecho", "poder",
    "puede", "puedo", "podemos", "pueden", "querer", "quiere", "quiero",
    "saber", "sabe", "sé", "ver", "ve", "veo", "vamos", "ir", "va", "voy",
    "dar", "da", "doy", "decir", "dice", "digo", "decía", "dijo",
}


def _filter_stop_words(query: str) -> str:
    """Remove common English and Spanish stop words to reduce AND noise."""
    tokens = query.split()
    filtered = [t for t in tokens if t.lower() not in STOP_WORDS]
    return " ".join(filtered)


def _prepare_websearch_query(query: str) -> str:
    """Minimal cleanup for websearch_to_tsquery.

    - Strip surrounding whitespace.
    - Collapse internal whitespace.
    - Remove common stop words.
    - Return empty string if nothing meaningful remains.
    """
    cleaned = " ".join(query.split())
    cleaned = _filter_stop_words(cleaned)
    return cleaned.strip()


async def lexical_search(
    session: AsyncSession,
    query: str,
    *,
    k: int = 50,
) -> list[tuple[uuid.UUID, float]]:
    """Return top-k chunks by Postgres full-text search rank.

    Uses the spanish-configured search_vector and GIN index.
    """
    prepared = _prepare_websearch_query(query)
    if not prepared:
        return []

    stmt = (
        select(
            DocumentChunk.id,
            text("ts_rank(search_vector, websearch_to_tsquery('spanish', :query))"),
        )
        .where(
            text(
                "search_vector @@ COALESCE(websearch_to_tsquery('spanish', :query), ''::tsquery)"
            )
        )
        .order_by(text("ts_rank(search_vector, websearch_to_tsquery('spanish', :query)) DESC"))
        .limit(k)
    )

    result = await session.execute(stmt, {"query": prepared})
    rows = result.all()
    return [(row[0], float(row[1])) for row in rows]
