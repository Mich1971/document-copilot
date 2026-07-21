"""Chat API routes."""

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, get_current_user
from app.chat import orchestrator
from app.chat.persistence import (
    SessionLocal,
    add_message,
    create_chat_thread,
    get_chat_thread,
    get_or_create_user,
    list_chat_threads,
    persist_citations,
)
from app.chat.schemas import (
    CitationOut,
    CreateThreadRequest,
    StreamChatRequest,
    ThreadDetailSchema,
    ThreadSchema,
    UIMessageOut,
)
from app.chat.streaming import stream_citation, stream_error, stream_status, stream_text_delta, stream_text_end, stream_text_start
from app.database.base import get_session
from app.database.models.chat_message import ChatMessage
from app.database.models.chat_thread import ChatThread
from app.database.models.document_chunk import DocumentChunk
from app.database.models.message_citation import MessageCitation
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
    turn_state = orchestrator.TurnState()

    async def stream_generator():
        yield stream_text_start(assistant_id)
        yield stream_status(assistant_id, "retrieval", 0.1, "Buscando en los filings…")
        yield stream_status(assistant_id, "generation", 0.4, "Generando respuesta…")
        try:
            async for delta in orchestrator.run_turn_stream(
                last_user_message.content,
                body.thread_id,
                current_user,
                session,
                turn_state,
            ):
                buffer.append(delta)
                yield stream_text_delta(assistant_id, delta)
        except ValueError as exc:
            yield stream_error(assistant_id, str(exc))
            return
        yield stream_text_end(assistant_id)
        yield stream_status(assistant_id, "grounding", 0.9, "Validando citas…")

        if turn_state.answer and turn_state.answer.citations:
            for citation in turn_state.answer.citations:
                yield stream_citation(assistant_id, citation)


    async def _save_assistant_with_citations() -> None:
        async with SessionLocal() as session:
            message = await add_message(session, body.thread_id, MessageRole.ASSISTANT, "".join(buffer))
            await session.commit()
            if turn_state.answer and turn_state.answer.citations:
                await persist_citations(session, message.id, turn_state.answer.citations)
                await session.commit()

    background_tasks.add_task(_save_assistant_with_citations)

    return StreamingResponse(
        stream_generator(),
        media_type="application/x-ndjson",
    )


@router.get("/messages/{message_id}/citations", response_model=list[CitationOut])
async def get_message_citations(
    message_id: uuid.UUID,
    current_user: CurrentUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[CitationOut]:
    stmt = (
        select(
            MessageCitation.chunk_id,
            DocumentChunk.chunk_index,
            MessageCitation.excerpt,
            MessageCitation.ticker,
            MessageCitation.company_name,
            MessageCitation.form,
            MessageCitation.filing_date,
            MessageCitation.page,
            MessageCitation.section,
        )
        .join(ChatMessage, MessageCitation.message_id == ChatMessage.id)
        .join(ChatThread, ChatMessage.thread_id == ChatThread.id)
        .join(DocumentChunk, MessageCitation.chunk_id == DocumentChunk.id)
        .where(MessageCitation.message_id == message_id)
        .where(ChatThread.user_id == current_user.id)
        .order_by(MessageCitation.citation_index)
    )
    result = await session.execute(stmt)
    rows = result.all()
    return [
        CitationOut(
            chunk_id=row.chunk_id,
            chunk_index=row.chunk_index,
            excerpt=row.excerpt,
            ticker=row.ticker,
            company_name=row.company_name,
            form=row.form,
            filing_date=row.filing_date,
            page=row.page,
            section=row.section,
        )
        for row in rows
    ]


