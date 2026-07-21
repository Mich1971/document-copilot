"""Runtime dependencies for the PydanticAI document agent."""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.retrieval.retriever import DocumentRetriever
from app.retrieval.schemas import Passage


@dataclass
class DocumentAgentDeps:
    user_id: uuid.UUID
    thread_id: uuid.UUID
    retriever: DocumentRetriever
    passages: list[Passage]
    session: AsyncSession
