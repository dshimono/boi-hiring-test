import uuid

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotAuthenticatedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.services.user import UserService

__all__ = ["get_db", "get_current_user"]

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """FastAPI dependency: resolve the caller's User from a Bearer JWT."""
    if not settings.auth_enabled:
        return await UserService(db).get_by_id(settings.auth_bypass_user_id)

    if credentials is None:
        raise NotAuthenticatedError()

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise NotAuthenticatedError() from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise NotAuthenticatedError()

    return await UserService(db).get_by_id(uuid.UUID(user_id))
