"""Integration tests for the repository layer against a real database session."""

from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import generate_magic_link_token, hash_token
from app.repositories.magic_link import MagicLinkRepository
from app.repositories.user import UserRepository
from app.utils.datetime import utc_now


@pytest.mark.asyncio
async def test_create_and_fetch_user(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)

    user = await users.create("alice@example.com")
    await db_session.commit()

    by_id = await users.get_by_id(user.id)
    by_email = await users.get_by_email("alice@example.com")

    assert by_id is not None
    assert by_id.id == user.id
    assert by_email is not None
    assert by_email.id == user.id
    assert by_id.is_active is True
    assert by_id.is_verified is False


@pytest.mark.asyncio
async def test_get_by_email_returns_none_for_unknown_email(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    assert await users.get_by_email("nobody@example.com") is None


@pytest.mark.asyncio
async def test_user_email_is_unique(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    await users.create("dup@example.com")
    await db_session.commit()

    with pytest.raises(IntegrityError):
        await users.create("dup@example.com")


@pytest.mark.asyncio
async def test_mark_verified_persists(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create("verify-me@example.com")
    await db_session.commit()

    await users.mark_verified(user)
    await db_session.commit()

    refreshed = await users.get_by_id(user.id)
    assert refreshed is not None
    assert refreshed.is_verified is True


@pytest.mark.asyncio
async def test_create_and_fetch_magic_link(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    magic_links = MagicLinkRepository(db_session)

    user = await users.create("link@example.com")
    token_hash = hash_token(generate_magic_link_token())
    expires_at = utc_now() + timedelta(minutes=15)

    created = await magic_links.create(
        user_id=user.id, token_hash=token_hash, expires_at=expires_at
    )
    await db_session.commit()

    fetched = await magic_links.get_by_token_hash(token_hash)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.user_id == user.id
    assert fetched.is_used is False
    assert fetched.is_expired is False


@pytest.mark.asyncio
async def test_get_by_token_hash_returns_none_for_unknown_hash(db_session: AsyncSession) -> None:
    magic_links = MagicLinkRepository(db_session)
    assert await magic_links.get_by_token_hash("does-not-exist") is None


@pytest.mark.asyncio
async def test_token_hash_is_unique(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    magic_links = MagicLinkRepository(db_session)

    user = await users.create("dup-token@example.com")
    token_hash = hash_token(generate_magic_link_token())
    expires_at = utc_now() + timedelta(minutes=15)

    await magic_links.create(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
    await db_session.commit()

    with pytest.raises(IntegrityError):
        await magic_links.create(user_id=user.id, token_hash=token_hash, expires_at=expires_at)


@pytest.mark.asyncio
async def test_mark_used_sets_used_at(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    magic_links = MagicLinkRepository(db_session)

    user = await users.create("used@example.com")
    token_hash = hash_token(generate_magic_link_token())
    magic_link = await magic_links.create(
        user_id=user.id, token_hash=token_hash, expires_at=utc_now() + timedelta(minutes=15)
    )
    await db_session.commit()
    assert magic_link.is_used is False

    await magic_links.mark_used(magic_link)
    await db_session.commit()

    refreshed = await magic_links.get_by_token_hash(token_hash)
    assert refreshed is not None
    assert refreshed.is_used is True


@pytest.mark.asyncio
async def test_expired_magic_link_reports_expired(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    magic_links = MagicLinkRepository(db_session)

    user = await users.create("expired@example.com")
    token_hash = hash_token(generate_magic_link_token())
    magic_link = await magic_links.create(
        user_id=user.id, token_hash=token_hash, expires_at=utc_now() - timedelta(minutes=1)
    )
    await db_session.commit()

    assert magic_link.is_expired is True


@pytest.mark.asyncio
async def test_deleting_user_cascades_to_magic_links(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    magic_links = MagicLinkRepository(db_session)

    user = await users.create("cascade@example.com")
    token_hash = hash_token(generate_magic_link_token())
    await magic_links.create(
        user_id=user.id, token_hash=token_hash, expires_at=utc_now() + timedelta(minutes=15)
    )
    await db_session.commit()

    await db_session.delete(user)
    await db_session.commit()

    assert await magic_links.get_by_token_hash(token_hash) is None
