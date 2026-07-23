"""Unit tests for PydanticAI agent configuration."""

from __future__ import annotations

from pydantic_ai.exceptions import ModelHTTPError

from app.assistant.agent import _is_groq_tool_choice_error, agent
from app.assistant.outputs import GroundedAnswer


def test_agent_output_type_is_grounded_answer():
    assert agent.output_type is GroundedAnswer


def test_agent_has_toolsets():
    assert len(agent.toolsets) > 0


def test_is_groq_tool_choice_error_true():
    exc = ModelHTTPError(
        status_code=400,
        model_name="openai/gpt-oss-120b",
        body={
            "error": {
                "message": "Tool choice is required, but model did not call a tool",
            }
        },
    )
    assert _is_groq_tool_choice_error(exc) is True


def test_is_groq_tool_choice_error_false_on_wrong_status():
    exc = ModelHTTPError(
        status_code=500,
        model_name="openai/gpt-oss-120b",
        body={
            "error": {
                "message": "Tool choice is required, but model did not call a tool",
            }
        },
    )
    assert _is_groq_tool_choice_error(exc) is False


def test_is_groq_tool_choice_error_false_on_wrong_model():
    exc = ModelHTTPError(
        status_code=400,
        model_name="openrouter:nvidia/nemotron-3-super-120b-a12b:free",
        body={
            "error": {
                "message": "Tool choice is required, but model did not call a tool",
            }
        },
    )
    assert _is_groq_tool_choice_error(exc) is False


def test_is_groq_tool_choice_error_false_on_non_model_http_error():
    assert _is_groq_tool_choice_error(ValueError("unexpected")) is False


def test_is_groq_tool_choice_error_false_on_missing_error_body():
    exc = ModelHTTPError(
        status_code=400,
        model_name="openai/gpt-oss-120b",
        body={},
    )
    assert _is_groq_tool_choice_error(exc) is False
