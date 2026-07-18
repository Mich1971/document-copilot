"""Chat API routes."""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
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
    AIMessage,
    CreateThreadRequest,
    MessageSchema,
    SendMessageRequest,
    StreamChatRequest,
    StreamingMessageChunk,
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


async def _stub_assistant_stream(thread_id: uuid.UUID, user_content: str):
    """Generate a stubbed assistant streaming response."""
    # Simulate streaming with a simple response
    response = f"Echo: {user_content}"
    # Yield start chunk
    yield StreamingMessageChunk(type="start", content="", message_id=None)
    # Yield content chunks (simulate streaming)
    for char in response:
        yield StreamingMessageChunk(type="content", content=char, message_id=None)
    # Yield end chunk
    yield StreamingMessageChunk(type="end", content="", message_id=None)


@router.post("/stream")
async def stream_chat(
    body: StreamChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """
    Stream a chat response (AI SDK compatible).
    Accepts AI SDK message format, streams a stubbed assistant reply.
    Persists user + assistant messages after stream completes.
    """
    await get_or_create_user(session, current_user.id, current_user.email)

    # Extract the last user message
    user_messages = [m for m in body.messages if m.role == "user"]
    if not user_messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No user message found",
        )
    last_user_message = user_messages[-1]

    # Determine thread: use provided thread_id or create new
    thread_id = body.thread_id
    if thread_id:
        # Verify thread ownership
        thread = await get_chat_thread(session, thread_id, current_user.id)
        if not thread:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Thread not found or access denied",
            )
    else:
        # Create new thread with first user message as title
        title = last_user_message.content[:50] + ("..." if len(last_user_message.content) > 50 else "")
        thread = await create_chat_thread(session, current_user.id, title)
        thread_id = thread.id

    # Persist user message
    user_msg = await add_message(session, thread_id, MessageRole.USER, last_user_message.content)
    await session.commit()

    # Stream assistant response
    async def stream_generator():
        full_response = ""
        async for chunk in _stub_assistant_stream(thread_id, last_user_message.content):
            full_response += chunk.content or ""
            # Convert to AI SDK data stream format
            if chunk.type == "start":
                yield f'0:"{chunk.content}"\n'
            elif chunk.type == "content":
                yield f'0:"{chunk.content}"\n'
            elif chunk.type == "end":
                yield 'd:{"finishReason":"stop"}\n'

        # Persist assistant message after streaming
        assistant_msg = await add_message(session, thread_id, MessageRole.ASSISTANT, full_response)
        await session.commit()

    return StreamingResponse(
        stream_generator(),
        media_type="text/plain; charset=utf-8",
    )


