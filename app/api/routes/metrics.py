from datetime import date as date_type

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Ad, AdMetric, AdPlatform
from app.schemas.metrics import AdCoverage, CoverageResponse, WeeklySummaryResponse

router = APIRouter(prefix="/metrics", tags=["metrics"])

_METRIC_COLUMNS = {
    "impressions": AdMetric.impressions,
    "clicks": AdMetric.clicks,
    "engagements": AdMetric.engagements,
}


@router.get("/coverage", response_model=CoverageResponse)
async def get_coverage(db: AsyncSession = Depends(get_db)) -> CoverageResponse:
    ads_result = await db.execute(select(Ad.ad_id, Ad.title).order_by(Ad.title))
    ads = ads_result.all()

    metrics_result = await db.execute(select(AdMetric.ad_id, AdMetric.date, AdMetric.platform))
    metric_rows = metrics_result.all()

    weeks = sorted({row.date for row in metric_rows})
    week_index = {week: i for i, week in enumerate(weeks)}

    coverage: dict[str, list[set[AdPlatform]]] = {ad_id: [set() for _ in weeks] for ad_id, _ in ads}
    for ad_id, metric_date, platform in metric_rows:
        if ad_id in coverage:
            coverage[ad_id][week_index[metric_date]].add(platform)

    return CoverageResponse(
        weeks=weeks,
        ads=[
            AdCoverage(
                ad_id=ad_id,
                title=title,
                platforms_by_week=[
                    sorted(platforms.value for platforms in week_platforms)
                    for week_platforms in coverage[ad_id]
                ],
            )
            for ad_id, title in ads
        ],
    )


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    metric: str = Query("impressions", pattern="^(impressions|clicks|engagements)$"),
    db: AsyncSession = Depends(get_db),
) -> WeeklySummaryResponse:
    column = _METRIC_COLUMNS[metric]
    result = await db.execute(
        select(AdMetric.date, AdMetric.platform, func.sum(column))
        .group_by(AdMetric.date, AdMetric.platform)
        .order_by(AdMetric.date)
    )
    rows = result.all()

    weeks: list[date_type] = sorted({row[0] for row in rows})
    week_index = {week: i for i, week in enumerate(weeks)}
    series: dict[str, list[int]] = {p.value: [0] * len(weeks) for p in AdPlatform}
    for metric_date, platform, total in rows:
        series[platform.value][week_index[metric_date]] = int(total)

    return WeeklySummaryResponse(weeks=weeks, metric=metric, series=series)
