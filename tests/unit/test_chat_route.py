import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.user import UserRepository


class _FakeChatService:
    def __init__(self, session: AsyncSession) -> None:
        pass

    async def ask(self, message: str, history: list) -> str:
        return "mocked answer"


class _FailingChatService:
    def __init__(self, session: AsyncSession) -> None:
        pass

    async def ask(self, message: str, history: list) -> str:
        raise RuntimeError("boom: sensitive provider detail, e.g. an api key")


@pytest_asyncio.fixture
async def authed_client(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> AsyncClient:
    user = await UserRepository(db_session).create("chat-tester@example.com")
    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "auth_bypass_user_id", user.id)
    return client


@pytest.mark.asyncio
async def test_chat_route_returns_answer(
    authed_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.routes.chat.ChatService", _FakeChatService)

    response = await authed_client.post("/api/v1/chat", json={"message": "hi", "history": []})

    assert response.status_code == 200
    assert response.json() == {"message": "mocked answer"}


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
async def test_chat_route_provider_failure_returns_generic_502(
    authed_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("app.api.routes.chat.ChatService", _FailingChatService)

    response = await authed_client.post("/api/v1/chat", json={"message": "hi", "history": []})

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert "boom" not in detail
    assert "api key" not in detail
