from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.metrics import CoverageResponse, WeeklySummaryResponse
from app.services import metrics

router = APIRouter(prefix="/metrics", tags=["metrics"], dependencies=[Depends(get_current_user)])


@router.get("/coverage", response_model=CoverageResponse)
async def get_coverage(db: AsyncSession = Depends(get_db)) -> CoverageResponse:
    """Which platforms reported data for each ad, week by week."""
    return await metrics.get_coverage(db)


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    metric: str = Query("impressions", pattern="^(impressions|clicks|engagements)$"),
    db: AsyncSession = Depends(get_db),
) -> WeeklySummaryResponse:
    """Weekly per-platform totals for one metric (impressions, clicks, or engagements)."""
    return await metrics.get_weekly_summary(db, metric)
