import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Query and persist User rows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Look up a user by primary key, or None if none matches."""
        return await self.session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        """Look up a user by email, or None if none matches."""
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, email: str) -> User:
        """Create a new, unverified user for the given email."""
        user = User(email=email)
        self.session.add(user)
        await self.session.flush()
        return user

    async def mark_verified(self, user: User) -> User:
        """Flip is_verified on, e.g. after a first successful magic-link redemption."""
        user.is_verified = True
        await self.session.flush()
        return user
