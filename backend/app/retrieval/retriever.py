"""Hybrid document retriever: semantic + lexical search fused with RRF."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.document_chunk import DocumentChunk
from app.database.models.source_document import SourceDocument
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.queries import lexical_search, semantic_search
from app.retrieval.schemas import Passage, RetrievalResult


class DocumentRetriever:
    """Hybrid retriever over document_chunks with neighbor expansion."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def search(self, query: str, top_k: int = 10) -> RetrievalResult:
        semantic = await semantic_search(self._session, query, k=50)
        lexical = await lexical_search(self._session, query, k=50)

        fused = reciprocal_rank_fusion(semantic, lexical, k=60)
        top_fused = fused[:top_k]

        if not top_fused:
            return RetrievalResult(
                passages=[],
                query=query,
                semantic_count=len(semantic),
                lexical_count=len(lexical),
            )

        selected_ids = [chunk_id for chunk_id, _score in top_fused]

        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.chunk_index,
                DocumentChunk.text,
                DocumentChunk.page,
                DocumentChunk.section,
                DocumentChunk.token_count,
                SourceDocument.ticker,
                SourceDocument.company_name,
                SourceDocument.form,
                SourceDocument.filing_date,
                SourceDocument.accession_number,
                SourceDocument.source_url,
            )
            .join(SourceDocument, DocumentChunk.document_id == SourceDocument.id)
            .where(DocumentChunk.id.in_(selected_ids))
        )

        result = await self._session.execute(stmt)
        rows = result.all()

        chunk_map = {row.id: row for row in rows}

        doc_ids = {row.document_id for row in rows if row.id in chunk_map}
        chunk_indices_by_doc: dict[uuid.UUID, list[int]] = {}
        for row in rows:
            if row.id in chunk_map:
                chunk_indices_by_doc.setdefault(row.document_id, []).append(row.chunk_index)

        neighbor_indices = set()
        for doc_id, indices in chunk_indices_by_doc.items():
            for idx in indices:
                neighbor_indices.add((doc_id, idx - 1))
                neighbor_indices.add((doc_id, idx + 1))

        neighbor_pairs = [(doc_id, idx) for doc_id, idx in neighbor_indices if idx >= 0]

        if neighbor_pairs:
            neighbor_conditions = []
            for doc_id, idx in neighbor_pairs:
                neighbor_conditions.append(
                    (DocumentChunk.document_id == doc_id, DocumentChunk.chunk_index == idx)
                )

            neighbor_stmt = (
                select(
                    DocumentChunk.id,
                    DocumentChunk.document_id,
                    DocumentChunk.chunk_index,
                    DocumentChunk.text,
                    DocumentChunk.page,
                    DocumentChunk.section,
                    DocumentChunk.token_count,
                    SourceDocument.ticker,
                    SourceDocument.company_name,
                    SourceDocument.form,
                    SourceDocument.filing_date,
                    SourceDocument.accession_number,
                    SourceDocument.source_url,
                )
                .join(SourceDocument, DocumentChunk.document_id == SourceDocument.id)
            )

            from sqlalchemy import or_
            neighbor_stmt = neighbor_stmt.where(or_(*[
                (DocumentChunk.document_id == doc_id) & (DocumentChunk.chunk_index == idx)
                for doc_id, idx in neighbor_pairs
            ]))

            neighbor_result = await self._session.execute(neighbor_stmt)
            neighbor_rows = neighbor_result.all()

            for row in neighbor_rows:
                if row.id not in chunk_map:
                    chunk_map[row.id] = row

        score_map = {chunk_id: score for chunk_id, score in top_fused}
        for chunk_id, _score in fused[top_k:]:
            if chunk_id in chunk_map:
                score_map[chunk_id] = _score

        passages = []
        for chunk_id, score in top_fused:
            row = chunk_map.get(chunk_id)
            if row is None:
                continue

            passages.append(
                Passage(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    text=row.text,
                    score=score,
                    rank=len(passages) + 1,
                    page=row.page,
                    section=row.section,
                    token_count=row.token_count,
                    ticker=row.ticker,
                    company_name=row.company_name,
                    form=row.form,
                    filing_date=row.filing_date,
                    accession_number=row.accession_number,
                    source_url=row.source_url,
                )
            )

        passages.sort(key=lambda p: p.rank)

        return RetrievalResult(
            passages=passages,
            query=query,
            semantic_count=len(semantic),
            lexical_count=len(lexical),
        )
