"""Citation grounding enforcement."""

from __future__ import annotations

from app.assistant.outputs import GroundedAnswer
from app.retrieval.schemas import Passage


class GroundingValidator:
    """Fail closed if any citation is not backed by a retrieved passage."""

    def validate(self, answer: GroundedAnswer, retrieved: list[Passage]) -> GroundedAnswer:
        retrieved_ids = {p.chunk_id for p in retrieved}
        for citation in answer.citations:
            if citation.chunk_id not in retrieved_ids:
                raise ValueError(
                    f"Citation {citation.chunk_id} not in retrieved passages"
                )
        return answer
