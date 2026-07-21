"""Unit tests for PydanticAI agent configuration."""

from __future__ import annotations

from app.assistant.agent import agent
from app.assistant.outputs import GroundedAnswer


def test_agent_output_type_is_grounded_answer():
    assert agent.output_type is GroundedAnswer


def test_agent_has_toolsets():
    assert len(agent.toolsets) > 0
