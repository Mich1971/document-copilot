"""PydanticAI agent definition for grounded document Q&A."""

from __future__ import annotations

from pathlib import Path

from openai import APIError
from pydantic_ai import Agent, RunContext, ModelAPIError
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from app.assistant.deps import DocumentAgentDeps
from app.assistant.outputs import GroundedAnswer
from app.config import get_settings
from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument
from app.retrieval.schemas import Passage
from sqlalchemy import select

settings = get_settings()
INSTRUCTIONS_PATH = Path(__file__).with_name("instructions.md")


def _load_instructions() -> str:
    return INSTRUCTIONS_PATH.read_text(encoding="utf-8")


def _is_bad_response(response: object) -> bool:
    if not isinstance(response, ModelResponse):
        return False
    text = response.text or ""
    return not text.strip() or len(text) < 10


def _is_groq_tool_choice_error(exc: Exception) -> bool:
    if not isinstance(exc, ModelHTTPError):
        return False
    if exc.status_code != 400:
        return False
    model_name = exc.model_name or ""
    if not model_name.startswith("openai/gpt-oss-120b"):
        return False
    body = exc.body
    if not isinstance(body, dict):
        return False
    error_body = body.get("error")
    if not isinstance(error_body, dict):
        return False
    message = error_body.get("message", "")
    if not isinstance(message, str):
        return False
    normalized = message.lower()
    return "tool choice is required" in normalized and "did not call a tool" in normalized


def _build_groq_model() -> OpenAIChatModel | None:
    if settings.groq_api_key is None:
        return None
    return OpenAIChatModel(
        "openai/gpt-oss-120b",
        provider=OpenAIProvider(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key.get_secret_value(),
        ),
    )


groq_model = _build_groq_model()
fallback_models = [
    "openrouter:nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter:openai/gpt-oss-20b:free",
]
if groq_model is not None:
    fallback_models.append(groq_model)

model = FallbackModel(
    *fallback_models,
    fallback_on=(
        ModelAPIError,
        APIError,
        _is_bad_response,
        _is_groq_tool_choice_error,
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
        lines.append(
            f"chunk_id={p.chunk_id} | [{p.ticker}] {p.form} ({p.filing_date}): {p.text[:500]}"
        )
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
