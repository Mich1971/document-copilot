"""
Diagnóstico rápido: prueba semantic_search y lexical_search directamente
contra la base de datos, para la query que produjo la respuesta sin sentido.

Uso:
    python -m app.scripts.diagnose_retrieval
"""

from __future__ import annotations

import asyncio
import selectors
import sys

from app.database.base import SessionLocal  # ajusta el import a tu SessionLocal real
from app.retrieval.queries import (
    _filter_stop_words,
    _prepare_websearch_query,
    lexical_search,
    semantic_search,
)

QUERIES = [
    "¿Cuáles son las comisiones y cargos aplicables en FiduciaPay?",
    "What are the risks mentioned in Apple's 10-K annual report?",
    "NVDA generative AI margins",
    "revenue growth 2024",
]


async def run_query(session, query: str) -> None:
    prepared = _prepare_websearch_query(query)
    filtered = _filter_stop_words(query)
    print(f"Query original:      {query!r}")
    print(f"Query preparada:     {prepared!r}")
    print(f"Query sin stopwords: {filtered!r}")
    print()

    semantic = await semantic_search(session, query, k=50)
    lexical = await lexical_search(session, query, k=50)

    print(f"  semantic_search -> {len(semantic)} resultados")
    for chunk_id, score in semantic[:5]:
        print(f"    {chunk_id}  score={score:.4f}")

    print(f"  lexical_search  -> {len(lexical)} resultados")
    for chunk_id, score in lexical[:5]:
        print(f"    {chunk_id}  score={score:.4f}")

    if not semantic and not lexical:
        print("  ⚠️  AMBAS búsquedas devolvieron 0 resultados")
    elif not lexical:
        print("  ⚠️  lexical_search devolvió 0 — revisa search_vector/GIN index")
    print()


async def main() -> None:
    async with SessionLocal() as session:
        for query in QUERIES:
            await run_query(session, query)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
