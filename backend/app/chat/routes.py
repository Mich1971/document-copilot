"""Chat API routes."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.chat.persistence import (
    add_message,
    create_chat_thread,
    get_chat_thread,
    get_or_create_user,
    get_thread_messages,
    list_chat_threads,
)
from app.chat.schemas import (
    CreateThreadRequest,
    MessageSchema,
    SendMessageRequest,
    ThreadDetailSchema,
    ThreadSchema,
)
from app.database.base import get_session
from app.database.models.message_role import MessageRole

router = APIRouter(prefix="/chats", tags=["chats"])
logger = logging.getLogger(__name__)


@router.post("/threads", response_model=ThreadSchema)
async def create_thread(
    body: CreateThreadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadSchema:
    """Create a new chat thread."""
    # Ensure user row exists
    user = await get_or_create_user(session, current_user.id, current_user.email)
    logger.info("User %s created thread", user.email)

    # Create thread
    thread = await create_chat_thread(session, user.id, body.title)
    await session.commit()

    return ThreadSchema(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
    )


@router.get("/threads", response_model=list[ThreadSchema])
async def list_threads(
    limit: int = 50,
    offset: int = 0,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ThreadSchema]:
    """List chat threads for the current user."""
    await get_or_create_user(session, current_user.id, current_user.email)

    threads = await list_chat_threads(session, current_user.id, limit, offset)
    return [
        ThreadSchema(
            id=t.id,
            title=t.title,
            created_at=t.created_at,
            updated_at=t.updated_at,
            message_count=len(t.messages),
        )
        for t in threads
    ]


@router.get("/threads/{thread_id}", response_model=ThreadDetailSchema)
async def get_thread(
    thread_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadDetailSchema:
    """Get a chat thread with all its messages."""
    await get_or_create_user(session, current_user.id, current_user.email)

    thread = await get_chat_thread(session, thread_id, current_user.id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    messages = [
        MessageSchema(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            sequence=msg.sequence,
        )
        for msg in thread.messages
    ]

    return ThreadDetailSchema(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        message_count=len(thread.messages),
        messages=messages,
    )


@router.post("/threads/{thread_id}/messages", response_model=MessageSchema)
async def send_message(
    thread_id: uuid.UUID,
    body: SendMessageRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MessageSchema:
    """Send a message to a chat thread."""
    await get_or_create_user(session, current_user.id, current_user.email)

    # Verify thread ownership
    thread = await get_chat_thread(session, thread_id, current_user.id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    logger.info("User %s sending message in thread %s", current_user.email, thread_id)

    # Add user message
    user_message = await add_message(
        session, thread_id, MessageRole.USER, body.content
    )
    await session.commit()

    return MessageSchema(
        id=user_message.id,
        role=user_message.role,
        content=user_message.content,
        created_at=user_message.created_at,
        sequence=user_message.sequence,
    )
