from collections.abc import Callable
from datetime import date as date_type
from typing import Literal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.selectable import Subquery

from app.models import Ad, AdMetric

Metric = Literal["ctr", "engagement_rate", "impressions", "clicks", "engagements"]

_METRIC_EXPRESSIONS: dict[Metric, Callable[[Subquery], object]] = {
    "ctr": lambda totals: case(
        (totals.c.impressions > 0, totals.c.clicks * 100.0 / totals.c.impressions), else_=0.0
    ),
    "engagement_rate": lambda totals: case(
        (totals.c.impressions > 0, totals.c.engagements * 100.0 / totals.c.impressions), else_=0.0
    ),
    "impressions": lambda totals: totals.c.impressions * 1.0,
    "clicks": lambda totals: totals.c.clicks * 1.0,
    "engagements": lambda totals: totals.c.engagements * 1.0,
}


async def get_dataset_date_range(
    session: AsyncSession,
) -> tuple[date_type | None, date_type | None]:
    """The earliest and latest dates with any recorded metrics, or (None, None) if empty."""
    result = await session.execute(select(func.min(AdMetric.date), func.max(AdMetric.date)))
    return result.one()


async def list_ads(session: AsyncSession) -> list[dict[str, str]]:
    """Every ad's id and title, so a caller can map a human-readable name to the
    exact id rank_ads() expects."""
    result = await session.execute(select(Ad.ad_id, Ad.title).order_by(Ad.title))
    return [{"ad_id": ad_id, "title": title} for ad_id, title in result.all()]


async def rank_ads(
    session: AsyncSession,
    metric: Metric = "ctr",
    ad_id: str | None = None,
    start_date: date_type | None = None,
    end_date: date_type | None = None,
    top_n: int = 10,
) -> dict:
    """Rank ads by a metric over a date range, optionally filtered to one ad.

    Returns the resolved query context alongside the ranked ads, so a caller
    (e.g. the chat tool) can state exactly what was queried.
    """
    min_date, max_date = await get_dataset_date_range(session)

    resolved_start = start_date or min_date
    resolved_end = end_date or max_date

    if resolved_start is None or resolved_end is None:
        return {"metric": metric, "period": None, "ad_id_filter": ad_id, "ads": []}

    totals = (
        select(
            AdMetric.ad_id,
            func.sum(AdMetric.impressions).label("impressions"),
            func.sum(AdMetric.clicks).label("clicks"),
            func.sum(AdMetric.engagements).label("engagements"),
        )
        .where(
            AdMetric.date >= resolved_start,
            AdMetric.date <= resolved_end,
            *([AdMetric.ad_id == ad_id] if ad_id is not None else []),
        )
        .group_by(AdMetric.ad_id)
        .subquery()
    )
    value_expr = _METRIC_EXPRESSIONS[metric](totals)

    result = await session.execute(
        select(
            totals.c.ad_id,
            Ad.title,
            totals.c.impressions,
            totals.c.clicks,
            totals.c.engagements,
            value_expr.label("value"),
        )
        .join(Ad, Ad.ad_id == totals.c.ad_id)
        .order_by(value_expr.desc(), Ad.title.asc())
        .limit(top_n)
    )

    return {
        "metric": metric,
        "period": f"{resolved_start.isoformat()}..{resolved_end.isoformat()}",
        "ad_id_filter": ad_id,
        "ads": [
            {
                "ad_id": row.ad_id,
                "title": row.title,
                "value": round(row.value, 2),
                "impressions": int(row.impressions),
                "clicks": int(row.clicks),
                "engagements": int(row.engagements),
            }
            for row in result.all()
        ],
    }
