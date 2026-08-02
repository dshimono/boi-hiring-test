from datetime import date

from pydantic import BaseModel


class AdCoverage(BaseModel):
    ad_id: str
    title: str
    platforms_by_week: list[list[str]]


class CoverageResponse(BaseModel):
    weeks: list[date]
    ads: list[AdCoverage]


class WeeklySummaryResponse(BaseModel):
    weeks: list[date]
    metric: str
    series: dict[str, list[int]]
