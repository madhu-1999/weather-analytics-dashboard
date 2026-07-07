from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from db.tables.weather_tables import DailyWeatherMetricsDB
from exceptions import DatabaseError


class MetricsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_data(self, airport_code: str, start_date: date, end_date: date) -> dict:
        try:
            stmt = select(
                func.max(DailyWeatherMetricsDB.temperature_2m_max_celsius).label(
                    "max_temp"
                ),
                func.min(DailyWeatherMetricsDB.temperature_2m_min_celsius).label(
                    "min_temp"
                ),
                func.count(
                    case((DailyWeatherMetricsDB.precipitation_hours > 0, 1), else_=None)
                ).label("precipitation_days_sum"),
                func.sum(DailyWeatherMetricsDB.precipitation_sum_mm).label(
                    "total_precipitation"
                ),
                func.max(DailyWeatherMetricsDB.wind_speed_10m_max_kmh).label(
                    "max_wind_speed"
                ),
                func.min(DailyWeatherMetricsDB.wind_speed_10m_min_kmh).label(
                    "min_wind_speed"
                ),
            ).where(
                DailyWeatherMetricsDB.weather_date.between(start_date, end_date),
                DailyWeatherMetricsDB.airport_code == airport_code,
            )
            results = self.session.execute(stmt).mappings().first()
            return dict(results) if results is not None else {}
        except Exception as e:
            raise DatabaseError(f"Could not fetch dates: {str(e)}") from e
