from datetime import date
from typing import List

from sqlalchemy import case, func, select, tuple_
from sqlalchemy.orm import Session

from db.tables.config import WeatherCodesDB
from db.tables.views import MonthlyWeatherMV, WeeklyWeatherMV
from db.tables.weather_tables import DailyWeatherMetricsDB, DateDimDB
from exceptions import DatabaseError


class MetricsRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_kpi_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> dict:
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
            raise DatabaseError(
                f"Could not fetch kpi data for given dates: {str(e)}"
            ) from e

    def get_monthly_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        try:
            # Subquery for the start date tuple (year, month)
            start_subquery = (
                select(DateDimDB.year_int, DateDimDB.month_int)
                .where(DateDimDB.weather_date == start_date)
                .scalar_subquery()
            )

            # Subquery for the end date tuple (year, month)
            end_subquery = (
                select(DateDimDB.year_int, DateDimDB.month_int)
                .where(DateDimDB.weather_date == end_date)
                .scalar_subquery()
            )

            stmt = (
                select(
                    MonthlyWeatherMV.year_int,
                    MonthlyWeatherMV.month_int,
                    MonthlyWeatherMV.temp_mean,
                    MonthlyWeatherMV.temp_max,
                    MonthlyWeatherMV.temp_min,
                    MonthlyWeatherMV.wind_speed_mean,
                    MonthlyWeatherMV.wind_speed_max,
                    MonthlyWeatherMV.wind_speed_min,
                    MonthlyWeatherMV.wind_gusts_mean,
                    MonthlyWeatherMV.wind_gusts_max,
                    MonthlyWeatherMV.wind_gusts_min,
                    MonthlyWeatherMV.precipitation_sum,
                    MonthlyWeatherMV.precipitation_hours,
                )
                .where(
                    MonthlyWeatherMV.airport_code == airport_code,
                    tuple_(MonthlyWeatherMV.year_int, MonthlyWeatherMV.month_int)
                    >= start_subquery,
                    tuple_(MonthlyWeatherMV.year_int, MonthlyWeatherMV.month_int)
                    <= end_subquery,
                )
                .order_by(
                    MonthlyWeatherMV.year_int.asc(), MonthlyWeatherMV.month_int.asc()
                )
            )
            results = self.session.execute(stmt).mappings().all()
            return [dict(result) for result in results if results is not None]
        except Exception as e:
            raise DatabaseError(
                f"Could not fetch monthly data for given dates: {str(e)}"
            ) from e

    def get_weekly_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        try:
            # Subquery for the start date tuple (year, week_of_year)
            start_subquery = (
                select(DateDimDB.year_int, DateDimDB.week_of_year)
                .where(DateDimDB.weather_date == start_date)
                .scalar_subquery()
            )

            # Subquery for the end date tuple (year, week_of_year)
            end_subquery = (
                select(DateDimDB.year_int, DateDimDB.week_of_year)
                .where(DateDimDB.weather_date == end_date)
                .scalar_subquery()
            )

            stmt = (
                select(
                    WeeklyWeatherMV.year_int,
                    WeeklyWeatherMV.week_of_year,
                    WeeklyWeatherMV.temp_mean,
                    WeeklyWeatherMV.temp_max,
                    WeeklyWeatherMV.temp_min,
                    WeeklyWeatherMV.wind_speed_mean,
                    WeeklyWeatherMV.wind_speed_max,
                    WeeklyWeatherMV.wind_speed_min,
                    WeeklyWeatherMV.wind_gusts_mean,
                    WeeklyWeatherMV.wind_gusts_max,
                    WeeklyWeatherMV.wind_gusts_min,
                    WeeklyWeatherMV.precipitation_sum,
                    WeeklyWeatherMV.precipitation_hours,
                )
                .where(
                    WeeklyWeatherMV.airport_code == airport_code,
                    tuple_(WeeklyWeatherMV.year_int, WeeklyWeatherMV.week_of_year)
                    >= start_subquery,
                    tuple_(WeeklyWeatherMV.year_int, WeeklyWeatherMV.week_of_year)
                    <= end_subquery,
                )
                .order_by(
                    WeeklyWeatherMV.year_int.asc(), WeeklyWeatherMV.week_of_year.asc()
                )
            )
            results = self.session.execute(stmt).mappings().all()
            return [dict(result) for result in results if results is not None]
        except Exception as e:
            raise DatabaseError(
                f"Could not fetch weekly data for given dates: {str(e)}"
            ) from e

    def get_daily_metrics(
        self, airport_code: str, start_date: date, end_date: date
    ) -> List[dict]:
        try:
            stmt = (
                select(
                    DailyWeatherMetricsDB.weather_date,
                    DailyWeatherMetricsDB.temperature_2m_mean_celsius.label(
                        "temp_mean"
                    ),
                    DailyWeatherMetricsDB.temperature_2m_max_celsius.label("temp_max"),
                    DailyWeatherMetricsDB.temperature_2m_min_celsius.label("temp_min"),
                    DailyWeatherMetricsDB.wind_speed_10m_mean_kmh.label(
                        "wind_speed_mean"
                    ),
                    DailyWeatherMetricsDB.wind_speed_10m_max_kmh.label(
                        "wind_speed_max"
                    ),
                    DailyWeatherMetricsDB.wind_speed_10m_min_kmh.label(
                        "wind_speed_min"
                    ),
                    DailyWeatherMetricsDB.wind_gusts_10m_mean_kmh.label(
                        "wind_gusts_mean"
                    ),
                    DailyWeatherMetricsDB.wind_gusts_10m_max_kmh.label(
                        "wind_gusts_max"
                    ),
                    DailyWeatherMetricsDB.wind_gusts_10m_min_kmh.label(
                        "wind_gusts_min"
                    ),
                    DailyWeatherMetricsDB.precipitation_sum_mm.label(
                        "precipitation_sum"
                    ),
                    DailyWeatherMetricsDB.precipitation_hours,
                    DailyWeatherMetricsDB.cloud_cover_mean_percent.label(
                        "cloud_cover_mean"
                    ),
                    WeatherCodesDB.weather_code,
                    WeatherCodesDB.weather_description.label("weather_code_mapping"),
                )
                .join(
                    WeatherCodesDB,
                    DailyWeatherMetricsDB.weather_code == WeatherCodesDB.weather_code,
                )
                .where(
                    DailyWeatherMetricsDB.airport_code == airport_code,
                    DailyWeatherMetricsDB.weather_date.between(start_date, end_date),
                )
            )
            results = self.session.execute(stmt).mappings().all()
            return [dict(result) for result in results if results is not None]
        except Exception as e:
            raise DatabaseError(
                f"Could not fetch daily data for given dates: {str(e)}"
            ) from e
