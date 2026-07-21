"""PydanticAI agent definition for grounded document Q&A."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent, RunContext, ModelAPIError
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.fallback import FallbackModel

from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument
from app.retrieval.schemas import Passage
from sqlalchemy import select

INSTRUCTIONS_PATH = Path(__file__).with_name("instructions.md")


def _load_instructions() -> str:
    return INSTRUCTIONS_PATH.read_text(encoding="utf-8")


def _is_bad_response(response: object) -> bool:
    if not isinstance(response, ModelResponse):
        return False
    text = response.text or ""
    return not text.strip() or len(text) < 10


model = FallbackModel(
    "openrouter:nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter:openai/gpt-oss-20b:free",
    fallback_on=(
        ModelAPIError,
        _is_bad_response,
    ),
)


agent = Agent[DocumentAgentDeps, GroundedAnswer](
    model=model,
    instructions=_load_instructions(),
    output_type=GroundedAnswer,
)


@agent.tool
async def search_filings(ctx: RunContext[DocumentAgentDeps], query: str) -> str:
    passages: list[Passage] = ctx.deps.passages
    if not passages:
        return "No se encontraron pasajes relevantes en el corpus."
    lines = []
    for p in passages[:5]:
        lines.append(f"[{p.ticker}] {p.form} ({p.filing_date}): {p.text[:500]}")
    return "\n\n".join(lines)


@agent.tool
async def read_chunk(ctx: RunContext[DocumentAgentDeps], chunk_id: str) -> str:
    try:
        import uuid as uuid_mod
        cid = uuid_mod.UUID(chunk_id)
    except ValueError:
        return "ID de chunk inválido."

    session = ctx.deps.session
    stmt = (
        select(DocumentChunk.text, SourceDocument.ticker, SourceDocument.form)
        .join(SourceDocument, DocumentChunk.document_id == SourceDocument.id)
        .where(DocumentChunk.id == cid)
    )
    result = await session.execute(stmt)
    row = result.first()
    if row is None:
        return "Chunk no encontrado."
    return f"[{row.ticker}] {row.form}: {row.text}"


@agent.tool
async def read_surrounding_chunks(ctx: RunContext[DocumentAgentDeps], chunk_id: str) -> str:
    try:
        import uuid as uuid_mod
        cid = uuid_mod.UUID(chunk_id)
    except ValueError:
        return "ID de chunk inválido."

    session = ctx.deps.session
    stmt = select(DocumentChunk.document_id, DocumentChunk.chunk_index).where(DocumentChunk.id == cid)
    result = await session.execute(stmt)
    row = result.first()
    if row is None:
        return "Chunk no encontrado."

    doc_id, idx = row.document_id, row.chunk_index

    neighbor_stmt = (
        select(DocumentChunk.chunk_index, DocumentChunk.text)
        .where(DocumentChunk.document_id == doc_id)
        .where(DocumentChunk.chunk_index.in_([idx - 1, idx + 1]))
        .order_by(DocumentChunk.chunk_index)
    )
    result = await session.execute(neighbor_stmt)
    rows = result.all()
    if not rows:
        return "No hay chunks vecinos."

    lines = []
    for r in rows:
        lines.append(f"Chunk {r.chunk_index}: {r.text[:300]}")
    return "\n\n".join(lines)
