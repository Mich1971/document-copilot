"""Unit tests for assistant output models."""

from __future__ import annotations

import uuid
from datetime import date

from app.assistant.outputs import Citation, GroundedAnswer, SourcePassage


def test_grounded_answer_roundtrip():
    cid = uuid.uuid4()
    answer = GroundedAnswer(
        answer="respuesta",
        citations=[
            Citation(
                chunk_id=cid,
                excerpt="excerpt",
                ticker="AAPL",
                company_name="Apple",
                form="10-K",
                filing_date=date(2024, 1, 1),
                page="1",
                section="Risk",
            )
        ],
        cited_passages=[
            SourcePassage(
                chunk_id=cid,
                text="text",
                ticker="AAPL",
                form="10-K",
                filing_date=date(2024, 1, 1),
            )
        ],
    )
    data = answer.model_dump(mode="json")
    assert data["answer"] == "respuesta"
    assert len(data["citations"]) == 1
    assert data["citations"][0]["ticker"] == "AAPL"
