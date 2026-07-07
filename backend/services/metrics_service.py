from datetime import date

from repository import MetricsRepository


class MetricsService:
    def __init__(self, metrics_repo: MetricsRepository) -> None:
        self.metrics_repo = metrics_repo

    def get_data(self, airport_code: str, start_date: date, end_date: date) -> dict:
        return self.metrics_repo.get_data(airport_code, start_date, end_date)
