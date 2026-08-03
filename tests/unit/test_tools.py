import json
import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tools import REGISTRY, TOOLS, AdPerformanceArgs, execute
from app.models import Ad, AdMetric, AdPlatform


@pytest_asyncio.fixture
async def db_with_one_ad(db_session: AsyncSession) -> AsyncSession:
    db_session.add(
        Ad(
            id=uuid.uuid4(),
            ad_id="ad_1",
            title="Ad One",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    )
    db_session.add(
        AdMetric(
            id=uuid.uuid4(),
            date=datetime(2025, 7, 1).date(),
            ad_id="ad_1",
            platform=AdPlatform.GOOGLE,
            impressions=1000,
            clicks=100,
            engagements=50,
            created_at=datetime.now(),
        )
    )
    await db_session.flush()
    return db_session


def test_get_ad_performance_registered() -> None:
    assert "get_ad_performance" in REGISTRY
    assert REGISTRY["get_ad_performance"].args_model is AdPerformanceArgs
    assert len(TOOLS) == 1


def test_tool_definition_exposes_json_schema() -> None:
    definition = REGISTRY["get_ad_performance"].definition()

    assert definition.name == "get_ad_performance"
    assert "metric" in definition.parameters["properties"]


@pytest.mark.asyncio
async def test_execute_valid_call_returns_tool_result(db_with_one_ad: AsyncSession) -> None:
    raw = await execute(db_with_one_ad, "get_ad_performance", {"metric": "ctr"})
    result = json.loads(raw)

    assert result["metric"] == "ctr"
    assert result["ads"][0]["ad_id"] == "ad_1"
    assert result["ads"][0]["value"] == 10.0


@pytest.mark.asyncio
async def test_execute_bad_metric_name_returns_json_error(db_with_one_ad: AsyncSession) -> None:
    raw = await execute(db_with_one_ad, "get_ad_performance", {"metric": "shares"})
    result = json.loads(raw)

    assert "error" in result


@pytest.mark.asyncio
async def test_execute_malformed_date_returns_json_error(db_with_one_ad: AsyncSession) -> None:
    raw = await execute(db_with_one_ad, "get_ad_performance", {"start_date": "not-a-date"})
    result = json.loads(raw)

    assert "error" in result


@pytest.mark.asyncio
async def test_execute_unknown_tool_returns_json_error(db_with_one_ad: AsyncSession) -> None:
    raw = await execute(db_with_one_ad, "delete_everything", {})
    result = json.loads(raw)

    assert result == {"error": "unknown tool: delete_everything"}


@pytest.mark.asyncio
async def test_execute_top_n_out_of_range_returns_json_error(db_with_one_ad: AsyncSession) -> None:
    raw = await execute(db_with_one_ad, "get_ad_performance", {"top_n": 100})
    result = json.loads(raw)

    assert "error" in result
