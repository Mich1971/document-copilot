"""Unit tests for the chat routes using a mocked auth + in-memory DB."""

import json
import uuid

from app.chat.schemas import CreateThreadRequest, StreamChatRequest


def test_create_thread_returns_201(client):
    resp = client.post("/chats/threads", json=CreateThreadRequest(title="Hello").model_dump())
    assert resp.status_code == 201
    body = resp.json()
    assert uuid.UUID(body["id"])
    assert body["title"] == "Hello"


def test_list_threads_returns_message_count(client):
    create = client.post("/chats/threads", json={"title": "T1"})
    assert create.status_code == 201

    resp = client.get("/chats/threads")
    assert resp.status_code == 200
    threads = resp.json()
    assert isinstance(threads, list)
    assert len(threads) >= 1
    assert "message_count" in threads[0]


def test_get_thread_returns_ui_message_format(client):
    create = client.post("/chats/threads", json={"title": "T2"})
    thread_id = create.json()["id"]

    resp = client.get(f"/chats/threads/{thread_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == thread_id
    # Empty thread still serializes `messages` as a list (AI SDK UIMessage shape).
    assert body["messages"] == []


def test_stream_returns_valid_ndjson_text_chunks(client):
    create = client.post("/chats/threads", json={"title": "Stream"})
    thread_id = create.json()["id"]

    payload = StreamChatRequest(
        messages=[{"role": "user", "content": "Hi there"}],
        thread_id=uuid.UUID(thread_id),
    ).model_dump(mode="json")

    resp = client.post("/chats/stream", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/x-ndjson")

    lines = [line for line in resp.text.splitlines() if line.strip()]
    assert len(lines) >= 3

    start = json.loads(lines[0])
    delta = json.loads(lines[1])
    end = json.loads(lines[-1])

    assert start["type"] == "text-start"
    assert "id" in start
    assert delta["type"] == "text-delta"
    assert delta["id"] == start["id"]
    assert "delta" in delta and delta["delta"]
    assert end["type"] == "text-end"
    assert end["id"] == start["id"]


def test_stream_persists_user_and_assistant_messages(client):
    create = client.post("/chats/threads", json={"title": "Persist"})
    thread_id = create.json()["id"]

    payload = StreamChatRequest(
        messages=[{"role": "user", "content": "Remember me"}],
        thread_id=uuid.UUID(thread_id),
    ).model_dump(mode="json")

    resp = client.post("/chats/stream", json=payload)
    assert resp.status_code == 200

    detail = client.get(f"/chats/threads/{thread_id}").json()
    roles = [m["role"] for m in detail["messages"]]
    assert "user" in roles
    assert "assistant" in roles


def test_access_other_users_thread_returns_403(client):
    # Create a thread owned by the (mocked) test user.
    create = client.post("/chats/threads", json={"title": "Private"})
    thread_id = create.json()["id"]

    # A thread id that does not belong to the user resolves to 403 in the
    # stream endpoint (ownership enforced via get_chat_thread).
    other_id = str(uuid.uuid4())
    assert other_id != thread_id

    payload = StreamChatRequest(
        messages=[{"role": "user", "content": "hack"}],
        thread_id=other_id,
    ).model_dump(mode="json")

    resp = client.post("/chats/stream", json=payload)
    assert resp.status_code == 403
