import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import UserNotFoundError
from app.repositories.user import UserRepository


@pytest.mark.asyncio
async def test_get_current_user_returns_bypass_user_when_auth_disabled(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    user = await UserRepository(db_session).create("bypass@example.com")

    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "auth_bypass_user_id", user.id)

    result = await get_current_user(credentials=None, db=db_session)

    assert result.id == user.id


@pytest.mark.asyncio
async def test_get_current_user_raises_when_bypass_user_missing(
    db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "auth_bypass_user_id", uuid.uuid4())

    with pytest.raises(UserNotFoundError):
        await get_current_user(credentials=None, db=db_session)
