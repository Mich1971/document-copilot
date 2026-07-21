"""Ingestion API routes for uploaded PDF documents."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.database.base import get_session
from app.database.models.uploaded_document import UploadedDocument
from app.ingest.schemas import UploadedDocumentCreate, UploadedDocumentOut, UploadedDocumentUpdate

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("/documents", response_model=list[UploadedDocumentOut])
async def list_uploaded_documents(
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[UploadedDocumentOut]:
    """List all uploaded documents for the current user."""
    result = await session.scalars(
        select(UploadedDocument).order_by(UploadedDocument.created_at.desc())
    )
    documents = result.all()
    return [UploadedDocumentOut.model_validate(doc) for doc in documents]


@router.post("/documents", response_model=UploadedDocumentOut, status_code=status.HTTP_201_CREATED)
async def create_uploaded_document(
    body: UploadedDocumentCreate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UploadedDocumentOut:
    """Register a new uploaded document."""
    document = UploadedDocument(
        source_filename=body.source_filename,
        docling_document=body.docling_document,
        source_type=body.source_type,
        converted_at_utc=body.converted_at_utc,
        status=body.status.value,
        error=body.error,
    )
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return UploadedDocumentOut.model_validate(document)


@router.get("/documents/{document_id}", response_model=UploadedDocumentOut)
async def get_uploaded_document(
    document_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UploadedDocumentOut:
    """Get a single uploaded document by ID."""
    result = await session.scalar(
        select(UploadedDocument).where(UploadedDocument.id == document_id)
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return UploadedDocumentOut.model_validate(result)


@router.patch("/documents/{document_id}", response_model=UploadedDocumentOut)
async def update_uploaded_document(
    document_id: uuid.UUID,
    body: UploadedDocumentUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UploadedDocumentOut:
    """Update an uploaded document's status or error info."""
    result = await session.scalar(
        select(UploadedDocument).where(UploadedDocument.id == document_id)
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    update_data = body.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = update_data["status"].value if hasattr(update_data["status"], "value") else update_data["status"]

    await session.execute(
        update(UploadedDocument)
        .where(UploadedDocument.id == document_id)
        .values(**update_data)
    )
    await session.commit()
    await session.refresh(result)
    return UploadedDocumentOut.model_validate(result)
