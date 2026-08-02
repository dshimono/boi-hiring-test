import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.magic_link import MagicLink
from app.utils.datetime import utc_now


class MagicLinkRepository:
    """Query and persist MagicLink rows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self, *, user_id: uuid.UUID, token_hash: str, expires_at: datetime
    ) -> MagicLink:
        magic_link = MagicLink(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self.session.add(magic_link)
        await self.session.flush()
        return magic_link

    async def get_by_token_hash(self, token_hash: str) -> MagicLink | None:
        result = await self.session.execute(
            select(MagicLink).where(MagicLink.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_used(self, magic_link: MagicLink) -> MagicLink:
        magic_link.used_at = utc_now()
        await self.session.flush()
        return magic_link
