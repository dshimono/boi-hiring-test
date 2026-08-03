"""Integration tests for the run_sql_query AI tool against a real Postgres session.

These specifically exercise the DB-level backstop (the ai_query_readonly role, the
read-only transaction) that app/ai/sql_guard.py's app-level parsing can't be tested
against with SQLite — see tests/unit/test_tools.py for the rejection paths, which
don't need real Postgres since they never reach the DB.
"""

import json
from datetime import date, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.sql_guard import MAX_ROWS, READONLY_ROLE
from app.ai.tools import execute
from app.models import Ad, AdComment, AdMetric, AdPlatform


@pytest_asyncio.fixture
async def db_with_ads(db_session: AsyncSession) -> AsyncSession:
    now = datetime.now()
    for i in range(3):
        db_session.add(Ad(ad_id=f"ad_{i}", title=f"Ad {i}", created_at=now, updated_at=now))
    db_session.add(
        AdMetric(
            date=datetime(2025, 7, 1).date(),
            ad_id="ad_0",
            platform=AdPlatform.GOOGLE,
            impressions=1000,
            clicks=100,
            engagements=50,
            created_at=now,
        )
    )
    db_session.add(
        AdComment(
            date=datetime(2025, 7, 1).date(),
            ad_id="ad_0",
            platform=AdPlatform.LINKEDIN,
            comment="Great ad!",
            created_at=now,
        )
    )
    await db_session.commit()
    return db_session


@pytest.mark.asyncio
async def test_valid_query_returns_scrubbed_rows(db_with_ads: AsyncSession) -> None:
    raw = await execute(
        db_with_ads,
        "run_sql_query",
        {"query": "SELECT ad_id, comment FROM ad_comments WHERE ad_id = 'ad_0'"},
    )
    result = json.loads(raw)

    assert result["rows"] == [{"ad_id": "ad_0", "comment": "Great ad!"}]
    assert result["row_count"] == 1
    assert result["truncated"] is False
    assert "id" not in result["rows"][0]


@pytest.mark.asyncio
async def test_join_across_allowed_tables(db_with_ads: AsyncSession) -> None:
    raw = await execute(
        db_with_ads,
        "run_sql_query",
        {
            "query": (
                "SELECT a.ad_id, m.impressions FROM ads a "
                "JOIN ad_metrics m ON a.ad_id = m.ad_id WHERE a.ad_id = 'ad_0'"
            )
        },
    )
    result = json.loads(raw)

    assert result["rows"] == [{"ad_id": "ad_0", "impressions": 1000}]


@pytest.mark.asyncio
async def test_query_scoped_to_fixture_rows_returns_exact_count(db_with_ads: AsyncSession) -> None:
    # The dev DB may already have seeded ads (make seed), so scope by ad_id rather
    # than assuming the table only holds this fixture's rows.
    raw = await execute(
        db_with_ads,
        "run_sql_query",
        {"query": "SELECT ad_id FROM ads WHERE ad_id IN ('ad_0', 'ad_1', 'ad_2')"},
    )
    result = json.loads(raw)

    assert result["row_count"] == 3
    assert result["truncated"] is False
    assert {row["ad_id"] for row in result["rows"]} == {"ad_0", "ad_1", "ad_2"}


@pytest.mark.asyncio
async def test_result_set_larger_than_max_rows_is_truncated(db_with_ads: AsyncSession) -> None:
    now = datetime.now()
    db_with_ads.add_all(
        [
            AdMetric(
                date=date(2020, 1, 1) + timedelta(days=i),
                ad_id="ad_0",
                platform=AdPlatform.META,
                impressions=1,
                clicks=1,
                engagements=1,
                created_at=now,
            )
            for i in range(MAX_ROWS + 5)
        ]
    )
    await db_with_ads.commit()

    raw = await execute(
        db_with_ads,
        "run_sql_query",
        {"query": "SELECT date FROM ad_metrics WHERE ad_id = 'ad_0' AND platform = 'Meta'"},
    )
    result = json.loads(raw)

    assert result["row_count"] == MAX_ROWS
    assert result["truncated"] is True


@pytest.mark.asyncio
async def test_users_table_rejected_before_touching_db(db_with_ads: AsyncSession) -> None:
    raw = await execute(db_with_ads, "run_sql_query", {"query": "SELECT email FROM users"})
    result = json.loads(raw)

    assert "not queryable" in result["error"]


@pytest.mark.asyncio
async def test_readonly_role_cannot_write_even_if_it_reached_execution(
    db_with_ads: AsyncSession,
) -> None:
    """The DB-level grant is the real backstop, not just app-level parsing: even a
    query that reaches the role-scoped connection can't write, because the role
    itself was only ever granted SELECT."""
    nested = await db_with_ads.begin_nested()
    try:
        await db_with_ads.execute(text(f"SET LOCAL ROLE {READONLY_ROLE}"))
        with pytest.raises(DBAPIError, match="permission denied"):
            await db_with_ads.execute(text("INSERT INTO ads (ad_id, title) VALUES ('x', 'x')"))
    finally:
        await nested.rollback()


@pytest.mark.asyncio
async def test_readonly_role_cannot_see_users_table(db_with_ads: AsyncSession) -> None:
    nested = await db_with_ads.begin_nested()
    try:
        await db_with_ads.execute(text(f"SET LOCAL ROLE {READONLY_ROLE}"))
        with pytest.raises(DBAPIError, match="permission denied"):
            await db_with_ads.execute(text("SELECT * FROM users"))
    finally:
        await nested.rollback()


@pytest.mark.asyncio
async def test_role_and_readonly_mode_revert_after_tool_call(db_with_ads: AsyncSession) -> None:
    """The tool must always roll back its savepoint so SET LOCAL settings don't
    leak into the rest of the shared request-scoped session for later tool calls
    in the same chat turn."""
    await execute(db_with_ads, "run_sql_query", {"query": "SELECT ad_id FROM ads"})

    result = await db_with_ads.execute(text("SELECT current_user"))
    assert result.scalar() != READONLY_ROLE

    result = await db_with_ads.execute(text("SHOW transaction_read_only"))
    assert result.scalar() == "off"

    # and the session is still fully usable for writes afterward
    db_with_ads.add(
        Ad(ad_id="after_tool_call", title="x", created_at=datetime.now(), updated_at=datetime.now())
    )
    await db_with_ads.flush()
