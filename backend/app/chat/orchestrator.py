"""Turn orchestrator: retrieval → agent → validation → stream."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.assistant.agent import agent
from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.auth.dependencies import CurrentUser
from app.grounding.validator import GroundingValidator
from app.retrieval.retriever import DocumentRetriever
from app.retrieval.schemas import Passage, RetrievalResult


@dataclass
class TurnState:
    answer: GroundedAnswer | None = None
    passages: list[Passage] | None = None
    retrieval: RetrievalResult | None = None


async def run_turn_stream(
    user_message: str,
    thread_id: uuid.UUID,
    current_user: CurrentUser,
    session: AsyncSession,
    state: TurnState,
) -> AsyncIterator[str]:
    retriever = DocumentRetriever(session)
    state.retrieval = await retriever.search(user_message)

    deps = DocumentAgentDeps(
        user_id=current_user.id,
        thread_id=thread_id,
        retriever=retriever,
        passages=state.retrieval.passages,
        session=session,
    )

    async with agent.run_stream(user_message, deps=deps) as result:
        async for text in result.stream_text():
            yield text

    state.answer = result.get_output()
    GroundingValidator().validate(state.answer, state.retrieval.passages)
    state.passages = state.retrieval.passages
