from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_magic_link_token, hash_token
from app.repositories.magic_link import MagicLinkRepository
from app.repositories.user import UserRepository
from app.utils.datetime import utc_now


@pytest.mark.asyncio
async def test_magic_link_request_creates_user(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    response = await client.post("/api/v1/auth/magic-link", json={"email": "new@example.com"})
    assert response.status_code == 200

    user = await UserRepository(db_session).get_by_email("new@example.com")
    assert user is not None


@pytest.mark.asyncio
async def test_verify_magic_link_returns_access_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    user = await UserRepository(db_session).create("verify@example.com")
    raw_token = generate_magic_link_token()
    await MagicLinkRepository(db_session).create(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=utc_now() + timedelta(minutes=15),
    )
    await db_session.commit()

    response = await client.post("/api/v1/auth/verify", json={"token": raw_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_verify_invalid_token_fails(client: AsyncClient) -> None:
    response = await client.post("/api/v1/auth/verify", json={"token": "not-a-real-token"})
    assert response.status_code == 400
