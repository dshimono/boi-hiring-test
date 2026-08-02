import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserNotFoundError
from app.models.user import User
from app.repositories.user import UserRepository


class UserService:
    """User lookups that translate a missing row into a domain error."""

    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)

    async def get_by_id(self, user_id: uuid.UUID) -> User:
        """Fetch a user by ID or raise UserNotFoundError."""
        user = await self.users.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        return user
