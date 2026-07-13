"""Database persistence helpers for chat operations."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import select

from app.database.models.chat_message import ChatMessage
from app.database.models.chat_thread import ChatThread
from app.database.models.message_role import MessageRole
from app.database.models.user import User


async def get_or_create_user(
    session: AsyncSession, user_id: uuid.UUID, email: str
) -> User:
    """Get or create a user row linked to Supabase auth."""
    stmt = select(User).where(User.id == user_id)
    user = await session.scalar(stmt)

    if user:
        return user

    user = User(id=user_id, email=email)
    session.add(user)
    await session.flush()
    return user


async def create_chat_thread(
    session: AsyncSession, user_id: uuid.UUID, title: str
) -> ChatThread:
    """Create a new chat thread for a user."""
    thread = ChatThread(user_id=user_id, title=title)
    session.add(thread)
    await session.flush()
    return thread


async def get_chat_thread(
    session: AsyncSession, thread_id: uuid.UUID, user_id: uuid.UUID
) -> ChatThread | None:
    """Get a chat thread if it belongs to the user."""
    stmt = (
        select(ChatThread)
        .where(ChatThread.id == thread_id)
        .where(ChatThread.user_id == user_id)
        .options(selectinload(ChatThread.messages))
    )
    return await session.scalar(stmt)


async def list_chat_threads(
    session: AsyncSession, user_id: uuid.UUID, limit: int = 50, offset: int = 0
) -> list[ChatThread]:
    """List chat threads for a user."""
    stmt = (
        select(ChatThread)
        .where(ChatThread.user_id == user_id)
        .order_by(ChatThread.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.scalars(stmt)
    return list(result)


async def add_message(
    session: AsyncSession,
    thread_id: uuid.UUID,
    role: MessageRole,
    content: str | None = None,
) -> ChatMessage:
    """Add a message to a chat thread."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.sequence.desc())
    )
    last_msg = await session.scalar(stmt)
    next_sequence = (last_msg.sequence + 1) if last_msg else 0

    message = ChatMessage(
        thread_id=thread_id,
        role=role,
        content=content,
        sequence=next_sequence,
    )
    session.add(message)
    await session.flush()
    return message


async def get_thread_messages(
    session: AsyncSession, thread_id: uuid.UUID
) -> list[ChatMessage]:
    """Get all messages in a thread."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.sequence)
    )
    result = await session.scalars(stmt)
    return list(result)
