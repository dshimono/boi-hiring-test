"""Assembles a single ad's detail view: per-platform metrics, comments, and totals."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Ad, AdComment, AdMetric
from app.schemas.ad import AdDetail, CommentOut, PlatformMetrics


def _percentage(numerator: int, denominator: int) -> float:
    """Numerator/denominator as a percentage rounded to 2 decimals, or 0.0 if denominator is 0."""
    return round(numerator / denominator * 100, 2) if denominator else 0.0


async def get_ad_detail(session: AsyncSession, ad_id: str) -> AdDetail:
    """Fetch an ad with its per-platform metrics and comments, or raise NotFoundError."""
    ad = await session.scalar(select(Ad).where(Ad.ad_id == ad_id))
    if ad is None:
        raise NotFoundError(f"Ad '{ad_id}' not found")

    metrics_result = await session.execute(
        select(
            AdMetric.platform,
            func.sum(AdMetric.impressions),
            func.sum(AdMetric.clicks),
            func.sum(AdMetric.engagements),
        )
        .where(AdMetric.ad_id == ad_id)
        .group_by(AdMetric.platform)
        .order_by(AdMetric.platform)
    )
    platforms = sorted(
        (
            PlatformMetrics(
                platform=platform.value,
                impressions=int(impressions),
                clicks=int(clicks),
                engagements=int(engagements),
                ctr=_percentage(int(clicks), int(impressions)),
            )
            for platform, impressions, clicks, engagements in metrics_result.all()
        ),
        key=lambda p: p.platform,
    )

    comments_result = await session.execute(
        select(AdComment.date, AdComment.platform, AdComment.comment)
        .where(AdComment.ad_id == ad_id)
        .order_by(AdComment.date.desc())
    )
    comments = [
        CommentOut(date=comment_date, platform=platform.value, comment=comment)
        for comment_date, platform, comment in comments_result.all()
    ]

    total_impressions = sum(p.impressions for p in platforms)
    total_clicks = sum(p.clicks for p in platforms)
    total_engagements = sum(p.engagements for p in platforms)

    return AdDetail(
        ad_id=ad.ad_id,
        title=ad.title,
        body=ad.body,
        image_url=f"/static/ads/{ad.path}" if ad.path else None,
        ocr_headline=ad.ocr_headline,
        ocr_body=ad.ocr_body,
        ocr_cta=ad.ocr_cta,
        vision_description=ad.vision_description,
        impressions=total_impressions,
        clicks=total_clicks,
        engagements=total_engagements,
        ctr=_percentage(total_clicks, total_impressions),
        engagement_rate=_percentage(total_engagements, total_impressions),
        platforms=platforms,
        comments=comments,
    )
