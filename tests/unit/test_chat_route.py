from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.user import UserRepository


def _parse_sse(body: str) -> list[dict]:
    events = []
    for line in body.strip().split("\n\n"):
        assert line.startswith("data: ")
        events.append(__import__("json").loads(line.removeprefix("data: ")))
    return events


class _FakeChatService:
    def __init__(self, session: AsyncSession) -> None:
        pass

    async def ask_stream(self, message: str, history: list) -> AsyncGenerator[str]:
        for word in ["mocked ", "answer"]:
            yield word


class _FailingChatService:
    def __init__(self, session: AsyncSession) -> None:
        pass

    async def ask_stream(self, message: str, history: list) -> AsyncGenerator[str]:
        raise RuntimeError("boom: sensitive provider detail, e.g. an api key")
        yield  # pragma: no cover - makes this an async generator


@pytest_asyncio.fixture
async def authed_client(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> AsyncClient:
    user = await UserRepository(db_session).create("chat-tester@example.com")
    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "auth_bypass_user_id", user.id)
    return client


@pytest.mark.asyncio
async def test_chat_route_streams_tokens_then_done(
    authed_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.routes.chat.ChatService", _FakeChatService)

    response = await authed_client.post("/api/v1/chat", json={"message": "hi", "history": []})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(response.text)
    assert events == [
        {"type": "token", "text": "mocked "},
        {"type": "token", "text": "answer"},
        {"type": "done"},
    ]


@pytest.mark.asyncio
async def test_chat_route_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/chat", json={"message": "hi"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_chat_route_rejects_oversized_message(authed_client: AsyncClient) -> None:
    response = await authed_client.post("/api/v1/chat", json={"message": "x" * 1001})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_route_rejects_too_much_history(authed_client: AsyncClient) -> None:
    history = [{"role": "user", "content": "hi"} for _ in range(11)]

    response = await authed_client.post("/api/v1/chat", json={"message": "hi", "history": history})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_route_accepts_long_assistant_answer_in_history(
    authed_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A prior streamed assistant answer can run well past 1000 chars; sending
    it back as history (as the frontend does) must not 422."""
    monkeypatch.setattr("app.api.routes.chat.ChatService", _FakeChatService)
    history = [{"role": "assistant", "content": "x" * 3000}]

    response = await authed_client.post(
        "/api/v1/chat", json={"message": "follow up", "history": history}
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_chat_route_provider_failure_emits_error_event(
    authed_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.routes.chat.ChatService", _FailingChatService)

    response = await authed_client.post("/api/v1/chat", json={"message": "hi", "history": []})

    assert response.status_code == 200
    events = _parse_sse(response.text)
    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "boom" not in events[0]["message"]
    assert "api key" not in events[0]["message"]
