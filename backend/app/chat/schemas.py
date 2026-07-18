"""Pydantic schemas for chat operations."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.database.models.message_role import MessageRole


class MessageSchema(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str | None = None
    created_at: datetime
    sequence: int

    class Config:
        from_attributes = True


class ThreadSchema(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    class Config:
        from_attributes = True


class ThreadDetailSchema(ThreadSchema):
    messages: list[MessageSchema] = Field(default_factory=list)


class CreateThreadRequest(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=255)


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)


class StreamingMessageChunk(BaseModel):
    """A chunk of a streaming message response."""

    type: str  # "start", "content", "end"
    content: str | None = None
    message_id: uuid.UUID | None = None


class AIMessage(BaseModel):
    """AI SDK compatible message format."""

    role: str  # "user" | "assistant" | "system"
    content: str


class StreamChatRequest(BaseModel):
    """Request body for streaming chat endpoint."""

    messages: list[AIMessage]
    thread_id: uuid.UUID | None = None
