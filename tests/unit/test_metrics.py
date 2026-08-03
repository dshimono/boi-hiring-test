import uuid
from datetime import date, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Ad, AdMetric, AdPlatform
from app.services.metrics import get_coverage, get_weekly_summary, rank_ads

DAY_1 = date(2025, 6, 30)
DAY_2 = date(2025, 7, 7)
DAY_3 = date(2025, 7, 14)


async def _make_ad(session: AsyncSession, ad_id: str, title: str) -> None:
    session.add(
        Ad(
            id=uuid.uuid4(),
            ad_id=ad_id,
            title=title,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )


async def _make_metric(
    session: AsyncSession,
    ad_id: str,
    metric_date: date,
    impressions: int,
    clicks: int,
    engagements: int,
    platform: AdPlatform = AdPlatform.GOOGLE,
) -> None:
    session.add(
        AdMetric(
            id=uuid.uuid4(),
            date=metric_date,
            ad_id=ad_id,
            platform=platform,
            impressions=impressions,
            clicks=clicks,
            engagements=engagements,
            created_at=datetime.now(),
        )
    )


@pytest_asyncio.fixture
async def seeded(db_session: AsyncSession) -> AsyncSession:
    """Two ads, each with metrics on DAY_1 and DAY_3 (DAY_2 has no data at all)."""
    await _make_ad(db_session, "high_ctr_ad", "High CTR Ad")
    await _make_ad(db_session, "low_ctr_ad", "Low CTR Ad")

    # high_ctr_ad: 100 clicks / 1000 impressions = 10% ctr, 50 engagements = 5% engagement_rate
    await _make_metric(db_session, "high_ctr_ad", DAY_1, impressions=600, clicks=60, engagements=30)
    await _make_metric(db_session, "high_ctr_ad", DAY_3, impressions=400, clicks=40, engagements=20)

    # low_ctr_ad: 10 clicks / 1000 impressions = 1% ctr, 5 engagements = 0.5% engagement_rate
    await _make_metric(db_session, "low_ctr_ad", DAY_1, impressions=600, clicks=6, engagements=3)
    await _make_metric(db_session, "low_ctr_ad", DAY_3, impressions=400, clicks=4, engagements=2)

    await db_session.flush()
    return db_session


@pytest.mark.asyncio
async def test_rank_ads_orders_by_ctr_desc(seeded: AsyncSession) -> None:
    result = await rank_ads(seeded, metric="ctr")

    assert [ad["ad_id"] for ad in result["ads"]] == ["high_ctr_ad", "low_ctr_ad"]
    assert result["ads"][0]["value"] == 10.0
    assert result["ads"][1]["value"] == 1.0


@pytest.mark.asyncio
async def test_rank_ads_orders_by_engagement_rate_desc(seeded: AsyncSession) -> None:
    result = await rank_ads(seeded, metric="engagement_rate")

    assert [ad["ad_id"] for ad in result["ads"]] == ["high_ctr_ad", "low_ctr_ad"]
    assert result["ads"][0]["value"] == 5.0
    assert result["ads"][1]["value"] == 0.5


@pytest.mark.asyncio
async def test_rank_ads_orders_by_raw_impressions(seeded: AsyncSession) -> None:
    result = await rank_ads(seeded, metric="impressions")

    assert result["ads"][0]["value"] == 1000.0
    assert result["ads"][1]["value"] == 1000.0
    assert result["ads"][0]["impressions"] == 1000
    assert result["ads"][0]["clicks"] == 100
    assert result["ads"][0]["engagements"] == 50


@pytest.mark.asyncio
async def test_rank_ads_filters_by_date_range(seeded: AsyncSession) -> None:
    result = await rank_ads(seeded, metric="impressions", start_date=DAY_1, end_date=DAY_1)

    assert result["period"] == "2025-06-30..2025-06-30"
    for ad in result["ads"]:
        assert ad["impressions"] == 600


@pytest.mark.asyncio
async def test_rank_ads_resolves_none_dates_to_full_dataset_range(seeded: AsyncSession) -> None:
    result = await rank_ads(seeded, metric="ctr")

    assert result["period"] == f"{DAY_1.isoformat()}..{DAY_3.isoformat()}"


@pytest.mark.asyncio
async def test_rank_ads_empty_date_range_returns_no_ads(seeded: AsyncSession) -> None:
    empty_day = DAY_3 + timedelta(days=30)
    result = await rank_ads(seeded, metric="ctr", start_date=empty_day, end_date=empty_day)

    assert result["ads"] == []
    assert result["period"] == f"{empty_day.isoformat()}..{empty_day.isoformat()}"


@pytest.mark.asyncio
async def test_rank_ads_unknown_ad_id_returns_no_ads(seeded: AsyncSession) -> None:
    result = await rank_ads(seeded, metric="ctr", ad_id="does_not_exist")

    assert result["ads"] == []
    assert result["ad_id_filter"] == "does_not_exist"


@pytest.mark.asyncio
async def test_rank_ads_filters_by_ad_id(seeded: AsyncSession) -> None:
    result = await rank_ads(seeded, metric="ctr", ad_id="low_ctr_ad")

    assert [ad["ad_id"] for ad in result["ads"]] == ["low_ctr_ad"]


@pytest.mark.asyncio
async def test_rank_ads_respects_top_n(seeded: AsyncSession) -> None:
    result = await rank_ads(seeded, metric="ctr", top_n=1)

    assert len(result["ads"]) == 1
    assert result["ads"][0]["ad_id"] == "high_ctr_ad"


@pytest.mark.asyncio
async def test_rank_ads_no_data_returns_none_period(db_session: AsyncSession) -> None:
    result = await rank_ads(db_session, metric="ctr")

    assert result == {"metric": "ctr", "period": None, "ad_id_filter": None, "ads": []}


@pytest_asyncio.fixture
async def multi_platform_seeded(db_session: AsyncSession) -> AsyncSession:
    """One ad with Google + Meta metrics on DAY_1, Google only on DAY_2."""
    await _make_ad(db_session, "ad_1", "Ad One")
    await _make_metric(
        db_session,
        "ad_1",
        DAY_1,
        impressions=100,
        clicks=10,
        engagements=5,
        platform=AdPlatform.GOOGLE,
    )
    await _make_metric(
        db_session,
        "ad_1",
        DAY_1,
        impressions=200,
        clicks=20,
        engagements=10,
        platform=AdPlatform.META,
    )
    await _make_metric(
        db_session,
        "ad_1",
        DAY_2,
        impressions=50,
        clicks=5,
        engagements=2,
        platform=AdPlatform.GOOGLE,
    )
    await db_session.flush()
    return db_session


@pytest.mark.asyncio
async def test_get_coverage_builds_ad_by_week_platform_grid(
    multi_platform_seeded: AsyncSession,
) -> None:
    result = await get_coverage(multi_platform_seeded)

    assert result.weeks == [DAY_1, DAY_2]
    assert len(result.ads) == 1
    ad_coverage = result.ads[0]
    assert ad_coverage.ad_id == "ad_1"
    assert ad_coverage.platforms_by_week[0] == ["Google", "Meta"]
    assert ad_coverage.platforms_by_week[1] == ["Google"]


@pytest.mark.asyncio
async def test_get_coverage_empty_dataset_returns_no_weeks(db_session: AsyncSession) -> None:
    result = await get_coverage(db_session)

    assert result.weeks == []
    assert result.ads == []


@pytest.mark.asyncio
async def test_get_weekly_summary_sums_per_platform_per_week(
    multi_platform_seeded: AsyncSession,
) -> None:
    result = await get_weekly_summary(multi_platform_seeded, "impressions")

    assert result.weeks == [DAY_1, DAY_2]
    assert result.metric == "impressions"
    assert result.series["Google"] == [100, 50]
    assert result.series["Meta"] == [200, 0]
    assert result.series["LinkedIn"] == [0, 0]
