import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

import structlog
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.client import ToolDef
from app.ai.sql_guard import (
    MAX_ROWS,
    READONLY_ROLE,
    STATEMENT_TIMEOUT_S,
    apply_row_cap,
    scrub_uuids,
    validate_select_only,
)
from app.core.exceptions import NotFoundError
from app.services import ad as ad_service
from app.services import metrics

logger = structlog.get_logger(__name__)


@dataclass
class Tool:
    name: str
    description: str
    args_model: type[BaseModel]
    fn: Callable[[AsyncSession, BaseModel], Awaitable[Any]]

    def definition(self) -> ToolDef:
        return ToolDef(
            name=self.name,
            description=self.description,
            parameters=self.args_model.model_json_schema(),
        )


class AdPerformanceArgs(BaseModel):
    """All fields optional with defaults — the model can always make a valid call."""

    metric: Literal["ctr", "engagement_rate", "impressions", "clicks", "engagements"] = "ctr"
    ad_id: str | None = None
    start_date: date | None = None  # None = full dataset range
    end_date: date | None = None
    top_n: int = Field(default=10, ge=1, le=20)


async def get_ad_performance(session: AsyncSession, args: AdPerformanceArgs) -> dict:
    """Return the resolved query context, not just rows, so the model can state
    what it actually queried."""
    return await metrics.rank_ads(session, **args.model_dump())


class SqlQueryArgs(BaseModel):
    query: str = Field(
        max_length=4000,
        description=(
            "A single read-only PostgreSQL SELECT statement. Queryable tables: "
            "ads(ad_id, title, body, image, path, ocr_headline, ocr_body, ocr_cta, "
            "vision_description, created_at, updated_at), "
            "ad_comments(date, ad_id, platform, comment, created_at), "
            "ad_metrics(date, ad_id, platform, impressions, clicks, engagements, "
            "created_at). platform is one of 'Google', 'Meta', 'LinkedIn'. No other "
            "tables exist. The 'id' column is never queryable on any table. "
            "List columns explicitly — SELECT * is not allowed."
        ),
    )


async def run_sql_query(session: AsyncSession, args: SqlQueryArgs) -> dict:
    """Validate and run an ad-hoc read-only query for questions get_ad_performance
    can't answer (e.g. ad comments). Defense in depth: validate_select_only checks
    a parsed AST (statement shape, table/column allowlist), then the query still
    runs under a Postgres role that can only SELECT the three ads tables, inside a
    read-only transaction, so a gap in the app-level check can't become a real
    leak or write. See app/ai/sql_guard.py."""
    try:
        parsed = validate_select_only(args.query)
    except ValueError as e:
        return {"error": str(e)}

    capped_sql = apply_row_cap(parsed).sql(dialect="postgres")
    nested = await session.begin_nested()
    try:
        await session.execute(text(f"SET LOCAL ROLE {READONLY_ROLE}"))
        await session.execute(text("SET TRANSACTION READ ONLY"))
        await session.execute(text(f"SET LOCAL statement_timeout = '{STATEMENT_TIMEOUT_S}s'"))
        result = await session.execute(text(capped_sql))
        rows = [dict(row) for row in result.mappings().all()]
    finally:
        # Always roll back, even on success: a savepoint *release* would let the
        # SET LOCAL role/timeout leak into the rest of this shared, request-scoped
        # session for later tool calls in the same chat turn. Rolling back also
        # keeps a rejected/erroring query from poisoning the session for the next
        # tool call in the loop.
        await nested.rollback()

    rows = scrub_uuids(rows)
    logger.info("sql_tool_query_executed", sql=capped_sql, row_count=len(rows))
    return {"rows": rows, "row_count": len(rows), "truncated": len(rows) >= MAX_ROWS}


class AdDetailsArgs(BaseModel):
    ad_id: str = Field(description="The ad's id, from the ad list in the system prompt.")


async def get_ad_details(session: AsyncSession, args: AdDetailsArgs) -> dict:
    """Full detail for one ad: creative text/visual description plus performance and comments."""
    try:
        detail = await ad_service.get_ad_detail(session, args.ad_id)
    except NotFoundError as e:
        return {"error": str(e)}
    return detail.model_dump()


TOOLS: list[Tool] = [
    Tool(
        name="get_ad_performance",
        description=(
            "Rank ads by a metric, optionally filtered by ad and date range. "
            "Use for any question about ad performance, comparison, or trends."
        ),
        args_model=AdPerformanceArgs,
        fn=get_ad_performance,
    ),
    Tool(
        name="run_sql_query",
        description=(
            "Run a read-only SQL SELECT against the ads/ad_comments/ad_metrics tables. "
            "Use for questions get_ad_performance can't answer, e.g. ad comment content, "
            "counts, or platform breakdowns. Results are capped at "
            f"{MAX_ROWS} rows."
        ),
        args_model=SqlQueryArgs,
        fn=run_sql_query,
    ),
    Tool(
        name="get_ad_details",
        description=(
            "Full detail for one specific ad: its creative text (headline, body, CTA as they "
            "appear on the image), a visual description of the creative, plus performance "
            "totals, per-platform breakdown, and comments. Use this for questions about what "
            "a specific ad says or looks like, or for the full picture of one ad."
        ),
        args_model=AdDetailsArgs,
        fn=get_ad_details,
    ),
]

REGISTRY: dict[str, Tool] = {t.name: t for t in TOOLS}


async def execute(session: AsyncSession, name: str, raw_args: dict) -> str:
    """Run a tool call and return its JSON result. Never raises — validation
    errors, unknown tools, and unexpected failures all become JSON error
    strings so the model can see what went wrong and self-correct."""
    tool = REGISTRY.get(name)
    if tool is None:
        return json.dumps({"error": f"unknown tool: {name}"})
    try:
        args = tool.args_model.model_validate(raw_args)
        result = await tool.fn(session, args)
        return json.dumps(result, default=str)
    except ValidationError as e:
        return json.dumps({"error": e.errors()}, default=str)
    except Exception:
        logger.exception("tool_execution_failed", tool=name)
        return json.dumps({"error": "tool execution failed"})
