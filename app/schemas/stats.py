from pydantic import BaseModel


class StatsOverview(BaseModel):
    ads_count: int
    platforms_count: int
    weeks_count: int
    metric_rows_count: int
    comments_count: int
