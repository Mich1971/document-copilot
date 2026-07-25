"""Unit tests for PydanticAI agent configuration and tools."""

from __future__ import annotations

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic_ai.exceptions import ModelHTTPError

from app.assistant.agent import _is_groq_tool_choice_error, agent, read_chunks
from app.assistant.outputs import GroundedAnswer


def test_agent_output_type_is_grounded_answer():
    assert agent.output_type is GroundedAnswer


def test_agent_has_toolsets():
    assert len(agent.toolsets) > 0


def test_is_groq_tool_choice_error_true():
    exc = ModelHTTPError(
        status_code=400,
        model_name="llama-3.3-70b-versatile",
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
        model_name="llama-3.3-70b-versatile",
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
        model_name="llama-3.3-70b-versatile",
        body={},
    )
    assert _is_groq_tool_choice_error(exc) is False


def _make_mock_row(chunk_id, ticker, form, text):
    row = MagicMock()
    row.id = chunk_id
    row.ticker = ticker
    row.form = form
    row.text = text
    return row


def test_read_chunks_empty_list():
    session = MagicMock()
    result = asyncio.run(read_chunks(MagicMock(deps=MagicMock(session=session)), []))
    assert result == "Ningún ID de chunk válido fue proporcionado."


def test_read_chunks_mixed_valid_invalid_ids():
    valid_id = uuid.uuid4()
    invalid_id = "not-a-uuid"
    session = MagicMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [_make_mock_row(valid_id, "AAPL", "10-K", "text")]
    session.execute = AsyncMock(return_value=mock_result)

    result = asyncio.run(read_chunks(MagicMock(deps=MagicMock(session=session)), [str(valid_id), invalid_id]))
    assert "[AAPL] 10-K: text" in result
    assert "not-a-uuid" in result
    assert "IDs inválidos" in result


def test_read_chunks_some_ids_not_found():
    found_id = uuid.uuid4()
    missing_id = uuid.uuid4()
    session = MagicMock()
    mock_result = MagicMock()
    mock_result.all.return_value = [_make_mock_row(found_id, "MSFT", "10-Q", "found text")]
    session.execute = AsyncMock(return_value=mock_result)

    result = asyncio.run(read_chunks(MagicMock(deps=MagicMock(session=session)), [str(found_id), str(missing_id)]))
    assert "found text" in result
    assert str(missing_id) in result
    assert "No encontrados" in result
