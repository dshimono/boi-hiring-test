import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AdPlatform, ad_platform_enum


class AdComment(Base):
    __tablename__ = "ad_comments"
    __table_args__ = (
        Index("idx_ad_comments_ad_id", "ad_id"),
        Index("idx_ad_comments_date", "date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    ad_id: Mapped[str] = mapped_column(ForeignKey("ads.ad_id", ondelete="RESTRICT"), nullable=False)
    platform: Mapped[AdPlatform] = mapped_column(ad_platform_enum, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
