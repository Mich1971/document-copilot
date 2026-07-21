"""Unit tests for Docling chunking logic and metadata extraction."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from docling_core.types.doc import DoclingDocument

from data.ingest_docling_documents import chunk_docling_document

FIXTURE_DIR = Path(__file__).resolve().parents[3] / "data" / "doclingdocuments"
SAMPLE_DOC = FIXTURE_DIR / "faq_transacciones.json"


def _load_sample_doc() -> DoclingDocument:
    if not SAMPLE_DOC.is_file():
        pytest.skip(f"Missing fixture: {SAMPLE_DOC}")
    data = json.loads(SAMPLE_DOC.read_text(encoding="utf-8"))
    return DoclingDocument.model_validate(data)


def test_chunk_docling_document_returns_non_empty_chunks():
    doc = _load_sample_doc()
    chunks = chunk_docling_document(doc)
    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk["text"].strip()


def test_chunk_metadata_contains_page_and_section():
    doc = _load_sample_doc()
    chunks = chunk_docling_document(doc)
    assert len(chunks) > 0
    found_page = False
    found_section = False
    for chunk in chunks:
        if chunk.get("page") is not None:
            found_page = True
        if chunk.get("section") is not None:
            found_section = True
    assert found_page, "No chunk contained page metadata"
    assert found_section, "No chunk contained section metadata"


def test_chunk_metadata_heading_resolution():
    doc = _load_sample_doc()
    chunks = chunk_docling_document(doc)
    assert len(chunks) > 0
    headings = [c["section"] for c in chunks if c.get("section")]
    assert len(headings) > 0, "No headings were resolved"


def test_chunk_docling_document_empty_document():
    empty_doc = DoclingDocument(
        name="empty",
        schema_name="DoclingDocument",
        version="1.0.0",
        texts=[],
        tables=[],
        pictures=[],
        groups=[],
    )
    chunks = chunk_docling_document(empty_doc)
    assert chunks == []


def test_chunk_docling_document_preserves_table_text():
    doc = _load_sample_doc()
    chunks = chunk_docling_document(doc)
    assert len(chunks) > 0
    has_table_content = any("$" in c["text"] or "USD" in c["text"] for c in chunks)
    assert has_table_content, "Table content not preserved in chunks"
