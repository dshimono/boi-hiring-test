from datetime import timedelta

import structlog
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import InvalidTokenError, TokenAlreadyUsedError, TokenExpiredError
from app.core.security import create_access_token, generate_magic_link_token, hash_token
from app.repositories.magic_link import MagicLinkRepository
from app.repositories.user import UserRepository
from app.schemas.auth import Token
from app.services.email import EmailService
from app.utils.datetime import utc_now

logger = structlog.get_logger(__name__)


class AuthService:
    """Orchestrates the magic-link request/verify flow end to end."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.magic_links = MagicLinkRepository(session)
        self.email_service = EmailService()

    async def request_magic_link(self, email: str, background_tasks: BackgroundTasks) -> None:
        """Create the user if needed, issue a token, and queue the sign-in email."""
        user = await self.users.get_by_email(email)
        if user is None:
            user = await self.users.create(email)

        raw_token = generate_magic_link_token()
        expires_at = utc_now() + timedelta(minutes=settings.magic_link_expire_minutes)
        await self.magic_links.create(
            user_id=user.id, token_hash=hash_token(raw_token), expires_at=expires_at
        )
        await self.session.commit()

        magic_link_url = f"{settings.frontend_url}/auth/verify?token={raw_token}"
        background_tasks.add_task(self._send_magic_link_email, user.email, magic_link_url)

    async def _send_magic_link_email(self, to: str, magic_link_url: str) -> None:
        # Runs after the response is sent, once get_db has already closed self.session —
        # fine since sending email doesn't need the DB.
        try:
            await self.email_service.send_magic_link(to=to, magic_link_url=magic_link_url)
        except Exception:
            logger.exception("Failed to send magic-link email.", to=to)

    async def verify_magic_link(self, raw_token: str) -> Token:
        """Redeem a magic link token and return a JWT access token."""
        magic_link = await self.magic_links.get_by_token_hash(hash_token(raw_token))
        if magic_link is None:
            raise InvalidTokenError()
        if magic_link.is_used:
            raise TokenAlreadyUsedError()
        if magic_link.is_expired:
            raise TokenExpiredError()

        await self.magic_links.mark_used(magic_link)

        user = await self.users.get_by_id(magic_link.user_id)
        assert user is not None
        if not user.is_verified:
            await self.users.mark_verified(user)

        await self.session.commit()

        access_token = create_access_token(subject=str(user.id))
        return Token(access_token=access_token)
