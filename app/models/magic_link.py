import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from uuid6 import uuid7

from app.db.base import Base
from app.utils.datetime import utc_now

if TYPE_CHECKING:
    from app.models.user import User


class MagicLink(Base):
    """A single-use, expiring sign-in token; only its hash is stored."""

    __tablename__ = "magic_links"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid7)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="magic_links")

    @property
    def is_used(self) -> bool:
        """Whether this token has already been redeemed."""
        return self.used_at is not None

    @property
    def is_expired(self) -> bool:
        """Whether this token is past its expiry, tolerating naive DB reads."""
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            # SQLite drops tz info even on DateTime(timezone=True) columns; the
            # value is always written in UTC, so treat naive reads as UTC.
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at < utc_now()
