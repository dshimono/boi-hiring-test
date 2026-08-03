from datetime import date

from pydantic import BaseModel


class AdOut(BaseModel):
    ad_id: str
    title: str
    body: str | None
    image_url: str | None


class PlatformMetrics(BaseModel):
    platform: str
    impressions: int
    clicks: int
    engagements: int
    ctr: float


class CommentOut(BaseModel):
    date: date
    platform: str
    comment: str


class AdDetail(BaseModel):
    ad_id: str
    title: str
    body: str | None
    image_url: str | None
    ocr_headline: str | None
    ocr_body: str | None
    ocr_cta: str | None
    vision_description: str | None
    impressions: int
    clicks: int
    engagements: int
    ctr: float
    engagement_rate: float
    platforms: list[PlatformMetrics]
    comments: list[CommentOut]
