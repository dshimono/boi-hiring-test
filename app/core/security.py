import hashlib
import secrets
from datetime import timedelta

import jwt

from app.core.config import settings
from app.utils.datetime import utc_now


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    """Issue a signed JWT access token for the given subject (the user ID)."""
    expire = utc_now() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    payload = {"sub": subject, "exp": expire, "iat": utc_now(), "type": "access"}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Verify and decode a JWT access token; raises jwt.PyJWTError if invalid."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])


def generate_magic_link_token() -> str:
    """Generate a cryptographically random single-use magic link token."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Hash a raw token for storage; only the hash is ever persisted."""
    return hashlib.sha256(raw_token.encode()).hexdigest()
