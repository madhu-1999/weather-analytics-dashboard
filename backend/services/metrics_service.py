from datetime import date
from typing import List

from repository import MetricsRepository


class MetricsService:
    def __init__(self, metrics_repo: MetricsRepository) -> None:
        self.metrics_repo = metrics_repo

    def get_kpi_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> dict:
        """Fetch headline KPI values for an airport over a date range.

        Args:
            airport_code: IATA/ICAO code identifying the airport.
            start_date: Inclusive start of the reporting period.
            end_date: Inclusive end of the reporting period.

        Returns:
            Aggregate KPI values for the period.
        """
        return self.metrics_repo.get_kpi_metrics(airport_code, start_date, end_date)

    def get_monthly_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        """Fetch monthly weather metrics for an airport over a date range.

        Args:
            airport_code: IATA/ICAO code identifying the airport.
            start_date: Inclusive start of the reporting period.
            end_date: Inclusive end of the reporting period.

        Returns:
            Monthly weather summaries covering the period.
        """
        return self.metrics_repo.get_monthly_metrics(airport_code, start_date, end_date)

    def get_weekly_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        """Fetch weekly weather metrics for an airport over a date range.

        Args:
            airport_code: IATA/ICAO code identifying the airport.
            start_date: Inclusive start of the reporting period.
            end_date: Inclusive end of the reporting period.

        Returns:
            Weekly weather summaries covering the period.
        """

        return self.metrics_repo.get_weekly_metrics(airport_code, start_date, end_date)

    def get_daily_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        """Fetch daily weather metrics for an airport over a date range.

        Args:
            airport_code: IATA/ICAO code identifying the airport.
            start_date: Inclusive start of the reporting period.
            end_date: Inclusive end of the reporting period.

        Returns:
            Daily weather records covering the period.
        """
        return self.metrics_repo.get_daily_metrics(airport_code, start_date, end_date)
