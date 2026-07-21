"""Pydantic schemas for retrieval results."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel


class Passage(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    text: str
    score: float
    rank: int
    page: str | None = None
    section: str | None = None
    token_count: int | None = None
    ticker: str
    company_name: str | None = None
    form: str
    filing_date: date
    accession_number: str
    source_url: str


class RetrievalResult(BaseModel):
    passages: list[Passage]
    query: str
    semantic_count: int
    lexical_count: int
