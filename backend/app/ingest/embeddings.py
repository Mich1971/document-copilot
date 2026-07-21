"""OpenRouter-backed embedding client for the ingestion pipeline."""

from __future__ import annotations

from typing import Sequence

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings


class EmbeddingResult(BaseModel):
    model: str
    dimensions: int
    vector: list[float]
    text: str


def get_embedding_client() -> AsyncOpenAI:
    """Return an async OpenAI client configured for OpenRouter."""
    api_key = settings.openrouter_api_key.get_secret_value() if settings.openrouter_api_key else settings.openai_api_key.get_secret_value()
    return AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
    )


async def embed_text(
    client: AsyncOpenAI,
    text: str,
    *,
    model: str | None = None,
    dimensions: int | None = None,
) -> EmbeddingResult:
    """Call the embeddings API for a single text input."""
    model = model or settings.openai_embedding_model
    dimensions = dimensions or settings.openai_embedding_dimensions

    response = await client.embeddings.create(
        model=model,
        input=text,
        encoding_format="float",
        dimensions=dimensions,
    )
    vector = response.data[0].embedding
    return EmbeddingResult(
        model=response.model,
        dimensions=len(vector),
        vector=vector,
        text=text,
    )


async def embed_batch(
    client: AsyncOpenAI,
    texts: Sequence[str],
    *,
    model: str | None = None,
    dimensions: int | None = None,
) -> list[EmbeddingResult]:
    """Call the embeddings API for a batch of texts."""
    if not texts:
        return []
    model = model or settings.openai_embedding_model
    dimensions = dimensions or settings.openai_embedding_dimensions

    response = await client.embeddings.create(
        model=model,
        input=list(texts),
        encoding_format="float",
        dimensions=dimensions,
    )
    results: list[EmbeddingResult] = []
    for item in response.data:
        results.append(
            EmbeddingResult(
                model=response.model,
                dimensions=len(item.embedding),
                vector=item.embedding,
                text=texts[item.index],
            )
        )
    return results
