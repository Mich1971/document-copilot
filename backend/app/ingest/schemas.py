"""Pydantic schemas for the ingestion / uploaded-documents API."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DocumentStatus(str, Enum):
    CONVERTED = "converted"
    INGESTED = "ingested"
    FAILED = "failed"


class UploadedDocumentCreate(BaseModel):
    source_filename: str = Field(..., max_length=255)
    docling_document: str = Field(..., max_length=255)
    source_type: str = Field("local-upload", max_length=32)
    converted_at_utc: datetime | None = None
    status: DocumentStatus = DocumentStatus.CONVERTED
    error: str | None = None


class UploadedDocumentUpdate(BaseModel):
    status: DocumentStatus | None = None
    ingested_at: datetime | None = None
    error: str | None = None


class UploadedDocumentOut(BaseModel):
    id: uuid.UUID
    source_filename: str
    docling_document: str
    source_type: str
    converted_at_utc: datetime | None = None
    ingested_at: datetime | None = None
    status: str
    error: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {
        "from_attributes": True,
    }
