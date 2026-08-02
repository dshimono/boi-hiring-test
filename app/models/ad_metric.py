import uuid
from datetime import date as date_type
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import AdPlatform, ad_platform_enum


class AdMetric(Base):
    __tablename__ = "ad_metrics"
    __table_args__ = (
        UniqueConstraint("date", "ad_id", "platform"),
        CheckConstraint("impressions >= 0", name="ad_metrics_impressions_check"),
        CheckConstraint("clicks >= 0", name="ad_metrics_clicks_check"),
        CheckConstraint("engagements >= 0", name="ad_metrics_engagements_check"),
        Index("idx_ad_metrics_date", "date"),
        Index("idx_ad_metrics_ad_id", "ad_id"),
        Index("idx_ad_metrics_platform", "platform"),
        Index("idx_ad_metrics_ad_date", "ad_id", "date"),
        Index("idx_ad_metrics_platform_date", "platform", "date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("uuidv7()")
    )
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    ad_id: Mapped[str] = mapped_column(
        ForeignKey("ads.ad_id", ondelete="RESTRICT"), nullable=False
    )
    platform: Mapped[AdPlatform] = mapped_column(ad_platform_enum, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False)
    engagements: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
