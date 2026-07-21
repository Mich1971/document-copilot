# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "docling>=2.112.0",
#     "openai>=2.44.0",
#     "transformers>=5.8.0",
# ]
# ///
"""Smoke test: ingest ONE chunk from ONE document, verify in Supabase."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

if sys.platform == "win32" and isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database.base import get_session
from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument
from app.database.models.uploaded_document import UploadedDocument
from app.ingest.embeddings import get_embedding_client, embed_text

DOCLING_DIR = Path(__file__).resolve().parent / "doclingdocuments"
TEST_DOC = "faq_transacciones.json"


async def main() -> None:
    docling_path = DOCLING_DIR / TEST_DOC
    if not docling_path.is_file():
        raise FileNotFoundError(f"Missing {docling_path}")

    doc_data = json.loads(docling_path.read_text(encoding="utf-8"))
    from docling_core.types.doc import DoclingDocument
    docling_doc = DoclingDocument.model_validate(doc_data)

    from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
    from transformers import BertTokenizer

    tokenizer = HuggingFaceTokenizer(
        tokenizer=BertTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2"),
        max_tokens=800,
    )
    chunker = HybridChunker(tokenizer=tokenizer)
    chunks = list(chunker.chunk(docling_doc))
    if not chunks:
        raise RuntimeError("No chunks produced")

    chunk = chunks[0]
    chunk_text = chunk.text.strip()
    print(f"Chunk text ({len(chunk_text)} chars): {chunk_text[:200]}")

    client = get_embedding_client()
    result = await embed_text(client, chunk_text)
    print(f"Embedding model: {result.model}")
    print(f"Embedding dimensions: {result.dimensions}")
    print(f"Embedding first 5 values: {result.vector[:5]}")

    async for session in get_session():
        # Clean up any previous test data for this doc
        from sqlalchemy import delete as sa_delete
        await session.execute(sa_delete(DocumentChunk).where(DocumentChunk.text == chunk_text))
        await session.commit()

        uploaded = UploadedDocument(
            source_filename=TEST_DOC,
            docling_document=TEST_DOC,
            source_type="local-upload",
            converted_at_utc=datetime.now(UTC),
            status="converted",
        )
        session.add(uploaded)
        await session.flush()

        source = SourceDocument(
            ticker="GENERIC",
            cik="0000000000",
            company_name="Faq Transacciones",
            form="UPLOAD",
            filing_date=datetime.now(UTC).date(),
            report_date=datetime.now(UTC).date(),
            fiscal_year=2026,
            accession_number=f"UP-{uploaded.id.hex[:8]}",
            primary_document=TEST_DOC,
            source_url="local-upload",
            markdown_content=chunk_text,
            ingested_at=datetime.now(UTC),
        )
        session.add(source)
        await session.flush()

        chunk_obj = DocumentChunk(
            document_id=source.id,
            chunk_index=0,
            text=chunk_text,
            page=None,
            section=None,
            token_count=len(chunk_text.split()),
            embedding=result.vector,
            chunk_metadata={"source": "local-upload", "filename": TEST_DOC, "chunker": "hybrid"},
        )
        session.add(chunk_obj)
        uploaded.status = "ingested"
        await session.commit()
        print("Inserted test chunk into Supabase")
        break

    # Verify
    async for session in get_session():
        result2 = await session.execute(
            text("SELECT id, text, token_count, vector_dims(embedding) FROM document_chunks WHERE text = :t LIMIT 1"),
            {"t": chunk_text},
        )
        row = result2.fetchone()
        if row is None:
            raise RuntimeError("Chunk not found in Supabase")
        print(f"Verified in DB: id={row[0]}, text={row[1][:50]}, tokens={row[2]}, dims={row[3]}")
        if row[3] != 2048:
            raise RuntimeError(f"Expected 2048 dims, got {row[3]}")
        print("Smoke test PASSED")
        break


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    asyncio.run(main())
