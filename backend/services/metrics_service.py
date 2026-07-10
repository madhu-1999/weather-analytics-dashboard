from datetime import date
from typing import List

from repository import MetricsRepository


class MetricsService:
    def __init__(self, metrics_repo: MetricsRepository) -> None:
        self.metrics_repo = metrics_repo

    def get_kpi_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> dict:
        return self.metrics_repo.get_kpi_metrics(airport_code, start_date, end_date)

    def get_monthly_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        return self.metrics_repo.get_monthly_metrics(airport_code, start_date, end_date)

    def get_weekly_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        return self.metrics_repo.get_weekly_metrics(airport_code, start_date, end_date)

    def get_daily_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        return self.metrics_repo.get_daily_metrics(airport_code, start_date, end_date)
