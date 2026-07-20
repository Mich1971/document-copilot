"""Database persistence helpers for chat operations."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.base import SessionLocal
from app.database.models.chat_message import ChatMessage
from app.database.models.chat_thread import ChatThread
from app.database.models.message_role import MessageRole
from app.database.models.user import User


async def get_or_create_user(
    session: AsyncSession, user_id: uuid.UUID, email: str
) -> User:
    """Get or upsert a user row linked to Supabase auth.

    Uses INSERT ... ON CONFLICT DO NOTHING so concurrent first-logins
    cannot produce duplicate-key errors.
    """
    stmt = (
        pg_insert(User)
        .values(id=user_id, email=email)
        .on_conflict_do_nothing(index_elements=["id"])
    )
    await session.execute(stmt)

    user = await session.scalar(select(User).where(User.id == user_id))
    assert user is not None  # guaranteed — either inserted or already existed
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
    """Get a chat thread if it belongs to the user (enforces ownership)."""
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
    """List chat threads for a user, with message count available in-memory."""
    stmt = (
        select(ChatThread)
        .where(ChatThread.user_id == user_id)
        .order_by(ChatThread.updated_at.desc())
        .options(selectinload(ChatThread.messages))
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
    """Append a message to a thread.

    The sequence number is computed as MAX(sequence)+1 in a single scalar
    subquery to avoid race conditions when multiple messages are added
    concurrently to the same thread.
    """
    next_seq_subq = (
        select(func.coalesce(func.max(ChatMessage.sequence) + 1, 0))
        .where(ChatMessage.thread_id == thread_id)
        .scalar_subquery()
    )
    sequence = await session.scalar(select(next_seq_subq))

    message = ChatMessage(
        thread_id=thread_id,
        role=role,
        content=content,
        sequence=sequence,
    )
    session.add(message)
    await session.flush()
    return message


async def get_thread_messages(
    session: AsyncSession, thread_id: uuid.UUID
) -> list[ChatMessage]:
    """Get all messages in a thread, ordered by sequence."""
    stmt = (
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.sequence)
    )
    result = await session.scalars(stmt)
    return list(result)


async def persist_assistant_reply(thread_id: uuid.UUID, content: str) -> None:
    """Persist the assistant reply after a stream completes.

    Opens a fresh session so it is safe to run from a background task, after
    the request's own session has been closed.
    """
    async with SessionLocal() as session:
        await add_message(session, thread_id, MessageRole.ASSISTANT, content)
        await session.commit()
