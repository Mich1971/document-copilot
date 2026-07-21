"""Typed outputs for the PydanticAI document agent."""

from __future__ import annotations

import uuid
from datetime import date

from pydantic import BaseModel


class Citation(BaseModel):
    chunk_id: uuid.UUID
    chunk_index: int | None = None
    excerpt: str
    ticker: str
    company_name: str | None = None
    form: str
    filing_date: date
    page: str | None = None
    section: str | None = None


class SourcePassage(BaseModel):
    chunk_id: uuid.UUID
    text: str
    ticker: str
    company_name: str | None = None
    form: str
    filing_date: date
    page: str | None = None
    section: str | None = None


class GroundedAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    cited_passages: list[SourcePassage]
