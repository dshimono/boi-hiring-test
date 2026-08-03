import uuid
from datetime import date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models import Ad, AdComment, AdMetric, AdPlatform
from app.services.ad import get_ad_detail

DAY_1 = date(2025, 7, 1)
DAY_2 = date(2025, 7, 8)


async def _make_ad(
    session: AsyncSession, ad_id: str, title: str, body: str | None = None, path: str | None = None
) -> None:
    session.add(
        Ad(
            id=uuid.uuid4(),
            ad_id=ad_id,
            title=title,
            body=body,
            path=path,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )


async def _make_metric(
    session: AsyncSession,
    ad_id: str,
    metric_date: date,
    platform: AdPlatform,
    impressions: int,
    clicks: int,
    engagements: int,
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


async def _make_comment(
    session: AsyncSession, ad_id: str, comment_date: date, platform: AdPlatform, comment: str
) -> None:
    session.add(
        AdComment(
            id=uuid.uuid4(),
            date=comment_date,
            ad_id=ad_id,
            platform=platform,
            comment=comment,
            created_at=datetime.now(),
        )
    )


@pytest.mark.asyncio
async def test_get_ad_detail_not_found_raises(db_session: AsyncSession) -> None:
    with pytest.raises(NotFoundError):
        await get_ad_detail(db_session, "does_not_exist")


@pytest.mark.asyncio
async def test_get_ad_detail_computes_ctr_and_engagement_rate(db_session: AsyncSession) -> None:
    await _make_ad(db_session, "ad_1", "Ad One", body="Body text", path="ad_1.png")
    await _make_metric(
        db_session, "ad_1", DAY_1, AdPlatform.GOOGLE, impressions=1000, clicks=100, engagements=50
    )
    await db_session.flush()

    detail = await get_ad_detail(db_session, "ad_1")

    assert detail.ad_id == "ad_1"
    assert detail.title == "Ad One"
    assert detail.image_url == "/static/ads/ad_1.png"
    assert detail.impressions == 1000
    assert detail.clicks == 100
    assert detail.engagements == 50
    assert detail.ctr == 10.0
    assert detail.engagement_rate == 5.0
    assert len(detail.platforms) == 1
    assert detail.platforms[0].platform == "Google"
    assert detail.platforms[0].ctr == 10.0


@pytest.mark.asyncio
async def test_get_ad_detail_sums_across_platforms_and_sorts(db_session: AsyncSession) -> None:
    await _make_ad(db_session, "ad_1", "Ad One")
    await _make_metric(
        db_session, "ad_1", DAY_1, AdPlatform.META, impressions=500, clicks=25, engagements=10
    )
    await _make_metric(
        db_session, "ad_1", DAY_1, AdPlatform.GOOGLE, impressions=500, clicks=75, engagements=40
    )
    await db_session.flush()

    detail = await get_ad_detail(db_session, "ad_1")

    assert detail.impressions == 1000
    assert detail.clicks == 100
    assert detail.engagements == 50
    assert [p.platform for p in detail.platforms] == ["Google", "Meta"]


@pytest.mark.asyncio
async def test_get_ad_detail_includes_comments_ordered_by_date_desc(
    db_session: AsyncSession,
) -> None:
    await _make_ad(db_session, "ad_1", "Ad One")
    await _make_comment(db_session, "ad_1", DAY_1, AdPlatform.GOOGLE, "First comment")
    await _make_comment(db_session, "ad_1", DAY_2, AdPlatform.GOOGLE, "Second comment")
    await db_session.flush()

    detail = await get_ad_detail(db_session, "ad_1")

    assert [c.comment for c in detail.comments] == ["Second comment", "First comment"]


@pytest.mark.asyncio
async def test_get_ad_detail_zero_impressions_returns_zero_ctr(db_session: AsyncSession) -> None:
    await _make_ad(db_session, "ad_1", "Ad One")
    await _make_metric(
        db_session, "ad_1", DAY_1, AdPlatform.GOOGLE, impressions=0, clicks=0, engagements=0
    )
    await db_session.flush()

    detail = await get_ad_detail(db_session, "ad_1")

    assert detail.ctr == 0.0
    assert detail.engagement_rate == 0.0


@pytest.mark.asyncio
async def test_get_ad_detail_no_image_when_path_missing(db_session: AsyncSession) -> None:
    await _make_ad(db_session, "ad_1", "Ad One", path=None)
    await db_session.flush()

    detail = await get_ad_detail(db_session, "ad_1")

    assert detail.image_url is None
