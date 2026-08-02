"""End-to-end coverage of the magic-link flow through the public HTTP API only.

Never reaches into the database directly — that's what tests/integration/test_db.py
and test_auth_flow.py are for. This file exercises the full sign-in journey and the
AUTH_ENABLED/AUTH_BYPASS_USER_ID kill switch as a caller of the API would experience it.
"""

from unittest.mock import AsyncMock
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.user import UserRepository
from app.services.email import EmailService


@pytest.fixture
def captured_magic_link(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Capture the magic-link URL EmailService would have sent."""
    mock = AsyncMock(return_value=None)
    monkeypatch.setattr(EmailService, "send_magic_link", mock)
    return mock


def _token_from_magic_link(mock: AsyncMock) -> str:
    magic_link_url = mock.call_args.kwargs["magic_link_url"]
    return parse_qs(urlparse(magic_link_url).query)["token"][0]


@pytest.mark.asyncio
async def test_magic_link_sign_in_grants_access_to_protected_resources(
    client: AsyncClient, captured_magic_link: AsyncMock
) -> None:
    email = "e2e@example.com"

    request_response = await client.post("/api/v1/auth/magic-link", json={"email": email})
    assert request_response.status_code == 200
    token = _token_from_magic_link(captured_magic_link)

    verify_response = await client.post("/api/v1/auth/verify", json={"token": token})
    assert verify_response.status_code == 200
    access_token = verify_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    me_response = await client.get("/api/v1/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email
    assert me_response.json()["is_verified"] is True

    ads_response = await client.get("/api/v1/ads", headers=headers)
    assert ads_response.status_code == 200


@pytest.mark.asyncio
async def test_reusing_a_magic_link_token_is_rejected(
    client: AsyncClient, captured_magic_link: AsyncMock
) -> None:
    await client.post("/api/v1/auth/magic-link", json={"email": "reuse@example.com"})
    token = _token_from_magic_link(captured_magic_link)

    first = await client.post("/api/v1/auth/verify", json={"token": token})
    assert first.status_code == 200

    second = await client.post("/api/v1/auth/verify", json={"token": token})
    assert second.status_code == 400


@pytest.mark.asyncio
async def test_protected_resource_rejects_missing_credentials(client: AsyncClient) -> None:
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_resource_allows_bypass_user_when_auth_disabled(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Distinct from the seeded AUTH_BYPASS_USER_ID row (bypass@example.com from the
    # alembic seed migration) which already exists in this shared database.
    user = await UserRepository(db_session).create("bypass-test@example.com")
    await db_session.commit()

    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "auth_bypass_user_id", user.id)

    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["email"] == "bypass-test@example.com"


@pytest.mark.asyncio
async def test_bypass_flag_overrides_any_supplied_credentials(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """AUTH_ENABLED=False must short-circuit before credentials are even inspected."""
    user = await UserRepository(db_session).create("bypass-test@example.com")
    await db_session.commit()

    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "auth_bypass_user_id", user.id)

    response = await client.get(
        "/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "bypass-test@example.com"


@pytest.mark.asyncio
async def test_protected_resource_still_requires_credentials_when_bypass_user_set_but_auth_enabled(
    client: AsyncClient, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Configuring AUTH_BYPASS_USER_ID alone must not bypass auth; the flag must be off too."""
    user = await UserRepository(db_session).create("bypass-test@example.com")
    await db_session.commit()

    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_bypass_user_id", user.id)

    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401
