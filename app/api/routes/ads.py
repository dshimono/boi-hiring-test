from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.exceptions import NotFoundError
from app.models import Ad, AdComment, AdMetric
from app.schemas.ad import AdDetail, AdOut, CommentOut, PlatformMetrics

router = APIRouter(prefix="/ads", tags=["ads"])


def _ctr(clicks: int, impressions: int) -> float:
    return round(clicks / impressions * 100, 2) if impressions else 0.0


@router.get("", response_model=list[AdOut])
async def list_ads(db: AsyncSession = Depends(get_db)) -> list[AdOut]:
    result = await db.execute(select(Ad).order_by(Ad.title))
    ads = result.scalars().all()
    return [
        AdOut(
            ad_id=ad.ad_id,
            title=ad.title,
            body=ad.body,
            image_url=f"/static/ads/{ad.path}" if ad.path else None,
        )
        for ad in ads
    ]


@router.get("/{ad_id}", response_model=AdDetail)
async def get_ad_detail(ad_id: str, db: AsyncSession = Depends(get_db)) -> AdDetail:
    ad = await db.scalar(select(Ad).where(Ad.ad_id == ad_id))
    if ad is None:
        raise NotFoundError(f"Ad '{ad_id}' not found")

    metrics_result = await db.execute(
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
                ctr=_ctr(int(clicks), int(impressions)),
            )
            for platform, impressions, clicks, engagements in metrics_result.all()
        ),
        key=lambda p: p.platform,
    )

    comments_result = await db.execute(
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
        impressions=total_impressions,
        clicks=total_clicks,
        engagements=total_engagements,
        ctr=_ctr(total_clicks, total_impressions),
        engagement_rate=_ctr(total_engagements, total_impressions),
        platforms=platforms,
        comments=comments,
    )
