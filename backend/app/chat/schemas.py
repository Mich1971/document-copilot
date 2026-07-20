"""Pydantic schemas for chat operations."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.message_role import MessageRole


class MessageSchema(BaseModel):
    id: uuid.UUID
    role: MessageRole
    content: str | None = None
    created_at: datetime
    sequence: int

    model_config = ConfigDict(from_attributes=True)


class ThreadSchema(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# --- AI SDK UIMessage wire format ---

class UITextPart(BaseModel):
    type: str = "text"
    text: str


class UIMessageOut(BaseModel):
    """AI SDK UIMessage shape expected by the frontend chat primitives."""
    id: str
    role: str
    parts: list[UITextPart]
    created_at: datetime | None = None

    @classmethod
    def from_db(cls, msg: object) -> "UIMessageOut":
        """Convert a ChatMessage ORM row to UIMessage wire format."""
        from app.database.models.chat_message import ChatMessage
        row: ChatMessage = msg  # type: ignore[assignment]
        text = row.content or ""
        return cls(
            id=str(row.id),
            role=row.role.value,
            parts=[UITextPart(type="text", text=text)],
            created_at=row.created_at,
        )


class ThreadDetailSchema(ThreadSchema):
    messages: list[UIMessageOut] = Field(default_factory=list)


class CreateThreadRequest(BaseModel):
    title: str = Field(default="New chat", min_length=1, max_length=255)


class AIMessage(BaseModel):
    """AI SDK message format sent by the frontend transport."""
    role: str  # "user" | "assistant" | "system"
    content: str


class StreamChatRequest(BaseModel):
    """Request body for streaming chat endpoint.

    thread_id is required — the frontend always creates a thread first via
    POST /chats/threads before opening a stream.
    """
    messages: list[AIMessage]
    thread_id: uuid.UUID
