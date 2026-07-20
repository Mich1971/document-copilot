"""Chat API routes."""

import json
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.chat.persistence import (
    add_message,
    create_chat_thread,
    get_chat_thread,
    get_or_create_user,
    list_chat_threads,
    persist_assistant_reply,
)
from app.chat.schemas import (
    CreateThreadRequest,
    StreamChatRequest,
    ThreadDetailSchema,
    ThreadSchema,
    UIMessageOut,
)
from app.database.base import get_session
from app.database.models.message_role import MessageRole

router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/threads", response_model=ThreadSchema, status_code=status.HTTP_201_CREATED)
async def create_thread(
    body: CreateThreadRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ThreadSchema:
    """Create a new chat thread."""
    # Ensure user row exists
    user = await get_or_create_user(session, current_user.id, current_user.email)

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
    """Get a chat thread with all its messages in AI SDK UIMessage shape."""
    await get_or_create_user(session, current_user.id, current_user.email)

    thread = await get_chat_thread(session, thread_id, current_user.id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found",
        )

    messages = [UIMessageOut.from_db(msg) for msg in thread.messages]

    return ThreadDetailSchema(
        id=thread.id,
        title=thread.title,
        created_at=thread.created_at,
        updated_at=thread.updated_at,
        message_count=len(thread.messages),
        messages=messages,
    )


async def _stream_assistant_reply(user_content: str):
    """Generate a stubbed assistant streaming response.

    Yields (chunk_type, text) tuples that the route maps to AI SDK NDJSON.
    """
    reply = f"Echo: {user_content}"
    yield ("start", "")
    for word in reply.split(" "):
        yield ("delta", word + " ")
    yield ("end", "")


@router.post("/stream")
async def stream_chat(
    body: StreamChatRequest,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """
    Stream a chat response in the AI SDK Data Stream Protocol (NDJSON).

    Accepts AI SDK message format, streams a stubbed assistant reply, and
    persists the user message (before streaming) and the assistant message
    (after streaming completes, via a background task).
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

    # thread_id is required (frontend creates the thread first). Enforce ownership.
    thread = await get_chat_thread(session, body.thread_id, current_user.id)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Thread not found or access denied",
        )

    # Persist the user message up front, committed before streaming.
    await add_message(session, body.thread_id, MessageRole.USER, last_user_message.content)
    await session.commit()

    assistant_id = uuid.uuid4()
    buffer: list[str] = []

    async def stream_generator():
        async for chunk_type, text in _stream_assistant_reply(last_user_message.content):
            if chunk_type == "start":
                yield _chunk("text-start", assistant_id)
            elif chunk_type == "delta":
                buffer.append(text)
                yield _chunk("text-delta", assistant_id, text)
            elif chunk_type == "end":
                yield _chunk("text-end", assistant_id)
        yield "\n"

    async def _save_assistant() -> None:
        await persist_assistant_reply(body.thread_id, "".join(buffer))

    background_tasks.add_task(_save_assistant)

    return StreamingResponse(
        stream_generator(),
        media_type="application/x-ndjson",
    )


def _chunk(chunk_type: str, message_id: uuid.UUID, delta: str | None = None) -> str:
    """Serialize an AI SDK UIMessageChunk to a single NDJSON line."""
    payload: dict = {"type": chunk_type, "id": str(message_id)}
    if delta is not None:
        payload["delta"] = delta
    return json.dumps(payload) + "\n"
