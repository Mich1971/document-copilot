"""Unit tests for grounding validator."""

from __future__ import annotations

import uuid
from datetime import date

import pytest

from app.assistant.outputs import Citation, GroundedAnswer
from app.grounding.validator import GroundingValidator
from app.retrieval.schemas import Passage


def _make_passage(chunk_id: uuid.UUID) -> Passage:
    return Passage(
        chunk_id=chunk_id,
        document_id=uuid.uuid4(),
        text="sample",
        score=1.0,
        rank=1,
        ticker="AAPL",
        form="10-K",
        filing_date=date(2024, 1, 1),
        accession_number="ACC",
        source_url="https://example.com",
    )


def test_validator_accepts_valid_citations():
    cid = uuid.uuid4()
    answer = GroundedAnswer(
        answer="test",
        citations=[Citation(chunk_id=cid, excerpt="ex", ticker="A", form="F", filing_date=date(2024, 1, 1))],
        cited_passages=[],
    )
    retrieved = [_make_passage(cid)]
    assert GroundingValidator().validate(answer, retrieved) is answer


def test_validator_rejects_unknown_citation():
    cid = uuid.uuid4()
    answer = GroundedAnswer(
        answer="test",
        citations=[Citation(chunk_id=cid, excerpt="ex", ticker="A", form="F", filing_date=date(2024, 1, 1))],
        cited_passages=[],
    )
    retrieved = [_make_passage(uuid.uuid4())]
    with pytest.raises(ValueError, match="not in retrieved passages"):
        GroundingValidator().validate(answer, retrieved)
