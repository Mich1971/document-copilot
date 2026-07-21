# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "docling>=2.112.0",
#     "openai>=2.44.0",
#     "transformers>=5.8.0",
# ]
# ///
"""Ingest converted DoclingDocument JSON files into the Postgres database.

Reads data/doclingdocuments/manifest.json, uses Docling's HybridChunker to
create structured chunks, generates embeddings via OpenRouter, and stores
them in Supabase.

Run:
    cd backend
    PYTHONPATH=.. uv run python ../data/ingest_docling_documents.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Windows async Postgres fix: psycopg needs SelectorEventLoop on Windows.
if sys.platform == "win32" and isinstance(asyncio.get_event_loop_policy(), asyncio.WindowsProactorEventLoopPolicy):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import delete, text

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.database.base import get_session
from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument
from app.database.models.uploaded_document import UploadedDocument
from app.ingest.embeddings import get_embedding_client, embed_batch

DATA_DIR = Path(__file__).resolve().parent
DOCLING_DIR = DATA_DIR / "doclingdocuments"
MANIFEST_PATH = DOCLING_DIR / "manifest.json"
CHUNK_MAX_TOKENS = 800
CHUNK_OVERLAP = 200
EMBEDDING_BATCH_SIZE = 10


def _build_item_lookup(doc: Any) -> dict[str, Any]:
    """Build a lookup from self_ref -> DocItem for page/section resolution."""
    lookup: dict[str, Any] = {}
    for item in getattr(doc, "texts", []):
        lookup[item.self_ref] = item
    for item in getattr(doc, "tables", []):
        lookup[item.self_ref] = item
    for item in getattr(doc, "pictures", []):
        lookup[item.self_ref] = item
    return lookup


def _resolve_page_number(item: Any, lookup: dict[str, Any]) -> int | None:
    """Resolve page number from a DocItem's provenance."""
    if hasattr(item, "prov") and item.prov:
        return item.prov[0].page_no
    return None


def _resolve_heading(item: Any, lookup: dict[str, Any], doc: Any) -> str | None:
    """Walk up parent chain to find the nearest SectionHeaderItem or TitleItem."""
    current = item
    visited: set[str] = set()
    while current is not None:
        current_ref = getattr(current, "self_ref", None)
        if current_ref is None or current_ref in visited:
            break
        visited.add(current_ref)
        label = getattr(current, "label", None)
        if label and str(label) in ("section_header", "title"):
            return getattr(current, "text", None)
        parent_ref = getattr(current, "parent", None)
        if parent_ref is None:
            break
        parent_cref = getattr(parent_ref, "cref", None)
        if parent_cref is None:
            break
        current = lookup.get(parent_cref)
    return None


def chunk_docling_document(doc: Any) -> list[dict[str, Any]]:
    """Chunk a DoclingDocument using HybridChunker with metadata."""
    from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
    from transformers import BertTokenizer

    tokenizer = HuggingFaceTokenizer(
        tokenizer=BertTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2"),
        max_tokens=CHUNK_MAX_TOKENS,
    )
    chunker = HybridChunker(tokenizer=tokenizer)
    chunks = list(chunker.chunk(doc))

    lookup = _build_item_lookup(doc)
    results: list[dict[str, Any]] = []

    for chunk in chunks:
        text = chunk.text.strip()
        if not text:
            continue

        # Resolve page number from first doc item
        page_no = None
        heading = None
        if chunk.meta.doc_items:
            first_ref = chunk.meta.doc_items[0].self_ref
            first_item = lookup.get(first_ref)
            if first_item is not None:
                page_no = _resolve_page_number(first_item, lookup)
                heading = _resolve_heading(first_item, lookup, doc)

        # Use chunk.meta.headings if available and heading not resolved
        if heading is None and getattr(chunk.meta, "headings", None):
            heading = chunk.meta.headings[0] if chunk.meta.headings else None

        results.append(
            {
                "text": text,
                "page": page_no,
                "section": heading,
                "token_count": len(text.split()),
            }
        )

    return results


async def ingest_docling_documents() -> dict:
    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"Missing {MANIFEST_PATH}")

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    documents = manifest.get("documents", [])
    if not documents:
        raise ValueError(f"No documents listed in {MANIFEST_PATH}")

    stats = {
        "source": manifest.get("source", "local-uploads"),
        "ingested_at_utc": datetime.now(UTC).isoformat(),
        "uploaded_count": 0,
        "source_documents_created": 0,
        "chunks_created": 0,
        "skipped": 0,
        "errors": [],
    }

    embedding_client = get_embedding_client()

    async for session in get_session():
        for doc in documents:
            docling_filename = doc["docling_document"]
            source_filename = doc["source_filename"]
            docling_path = DOCLING_DIR / docling_filename

            if not docling_path.is_file():
                stats["errors"].append(f"Missing docling file: {docling_filename}")
                continue

            try:
                doc_data = json.loads(docling_path.read_text(encoding="utf-8"))
                from docling_core.types.doc import DoclingDocument
                docling_doc = DoclingDocument.model_validate(doc_data)
            except Exception as exc:
                stats["errors"].append(f"Failed to load {docling_filename}: {exc}")
                continue

            chunks = chunk_docling_document(docling_doc)
            if not chunks:
                stats["errors"].append(f"No chunks produced for {docling_filename}")
                continue

            # Check if already ingested
            existing_uploaded = await session.scalar(
                __import__("sqlalchemy").select(UploadedDocument).where(
                    UploadedDocument.docling_document == docling_filename
                )
            )
            if existing_uploaded and existing_uploaded.status == "ingested":
                source_doc = await session.scalar(
                    __import__("sqlalchemy").select(SourceDocument).where(
                        SourceDocument.primary_document == docling_filename
                    )
                )
                if source_doc is None:
                    stats["errors"].append(f"Source document missing for {docling_filename}")
                    continue
                await session.execute(
                    delete(DocumentChunk).where(
                        DocumentChunk.document_id == source_doc.id
                    )
                )
                uploaded_doc = existing_uploaded
                uploaded_doc.status = "converted"
            else:
                # Create new uploaded document record
                uploaded_doc = UploadedDocument(
                    source_filename=source_filename,
                    docling_document=docling_filename,
                    source_type="local-upload",
                    converted_at_utc=datetime.now(UTC),
                    status="converted",
                )
                session.add(uploaded_doc)
                await session.flush()

                # Create source document
                full_text = "\n\n".join(c["text"] for c in chunks)
                source_doc = SourceDocument(
                    ticker="GENERIC",
                    cik="0000000000",
                    company_name=source_filename.replace("_", " ").replace(".pdf", "").title(),
                    form="UPLOAD",
                    filing_date=datetime.now(UTC).date(),
                    report_date=datetime.now(UTC).date(),
                    fiscal_year=datetime.now(UTC).year,
                    accession_number=f"UP-{uploaded_doc.id.hex[:8]}",
                    primary_document=docling_filename,
                    source_url="local-upload",
                    markdown_content=full_text,
                    ingested_at=datetime.now(UTC),
                )
                session.add(source_doc)
                await session.flush()

            # Generate embeddings in batches
            texts = [c["text"] for c in chunks]
            all_embeddings: list[list[float]] = []
            for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
                batch = texts[i : i + EMBEDDING_BATCH_SIZE]
                results = await embed_batch(embedding_client, batch)
                all_embeddings.extend(r.vector for r in results)

            # Insert chunks
            document_id = source_doc.id
            for idx, chunk_info in enumerate(chunks):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    text=chunk_info["text"],
                    page=str(chunk_info["page"]) if chunk_info["page"] is not None else None,
                    section=chunk_info["section"],
                    token_count=chunk_info["token_count"],
                    embedding=all_embeddings[idx],
                    chunk_metadata={
                        "source": "local-upload",
                        "filename": source_filename,
                        "chunker": "hybrid",
                    },
                )
                session.add(chunk)

            uploaded_doc.status = "ingested"
            uploaded_doc.ingested_at = datetime.now(UTC)
            await session.commit()

            stats["uploaded_count"] += 1
            stats["source_documents_created"] += 1
            stats["chunks_created"] += len(chunks)
            print(f"Ingested {source_filename}: {len(chunks)} chunks with embeddings")

        break

    return stats


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    result = asyncio.run(ingest_docling_documents())
    print(json.dumps(result, indent=2, ensure_ascii=False))
