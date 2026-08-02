from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models import Ad, AdComment, AdMetric, AdPlatform
from app.schemas.stats import StatsOverview

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=StatsOverview)
async def get_stats_overview(db: AsyncSession = Depends(get_db)) -> StatsOverview:
    ads_count = await db.scalar(select(func.count()).select_from(Ad))
    weeks_count = await db.scalar(select(func.count(func.distinct(AdMetric.date))))
    metric_rows_count = await db.scalar(select(func.count()).select_from(AdMetric))
    comments_count = await db.scalar(select(func.count()).select_from(AdComment))

    return StatsOverview(
        ads_count=ads_count or 0,
        platforms_count=len(AdPlatform),
        weeks_count=weeks_count or 0,
        metric_rows_count=metric_rows_count or 0,
        comments_count=comments_count or 0,
    )
