import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from typing import Any, Literal

import structlog
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.client import ToolDef
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
