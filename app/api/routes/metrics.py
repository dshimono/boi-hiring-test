from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.metrics import CoverageResponse, RankAdsResponse, WeeklySummaryResponse
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


@router.get("/ranked", response_model=RankAdsResponse)
async def get_ranked_ads(
    metric: str = Query("ctr", pattern="^(ctr|engagement_rate|impressions|clicks|engagements)$"),
    ad_id: str | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    top_n: int = Query(10, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
) -> RankAdsResponse:
    """Ads ranked by a metric over a date range, optionally filtered to one ad —
    the same query the chat tool uses, so dashboard and chat rankings always agree."""
    return await metrics.rank_ads(
        db, metric=metric, ad_id=ad_id, start_date=start_date, end_date=end_date, top_n=top_n
    )
