from datetime import date
import logging
from typing import List, TypeVar

from pydantic import BaseModel

from exceptions import InvalidDateRangeError
from models.constants import AggLevelEnum
from models.response import (
    DailyWeatherMetrics,
    DateResponse,
    FilterOptionsResponse,
    LocationResponse,
    MonthlyWeatherMetrics,
    SingleLocationDashboardDataResponse,
    WeeklyWeatherMetrics,
)
from .date_service import DateService
from .location_service import LocationService
from .metrics_service import MetricsService

logger = logging.getLogger(__name__)

M = TypeVar("M", bound=BaseModel)


class DashboardService:
    def __init__(
        self,
        location_service: LocationService,
        date_service: DateService,
        metrics_service: MetricsService,
    ) -> None:
        self.location_service = location_service
        self.date_service = date_service
        self.metrics_service = metrics_service

    def get_options(self) -> FilterOptionsResponse:
        try:
            locations: List[LocationResponse] = self.location_service.get_locations()
            dates: List[DateResponse] = self.date_service.get_available_date_range()
            return type(self)._convert_to_response(locations, dates)
        except Exception as e:
            logger.error(f"Error encountered while fetching options: {e}")
            raise ValueError(f"Dashboard data error encountered: {str(e)}") from e

    def get_data(
        self,
        airport_code: str,
        start_date: date,
        end_date: date,
        agg_level: AggLevelEnum,
    ) -> SingleLocationDashboardDataResponse:
        if start_date > end_date or end_date > date.today():
            raise InvalidDateRangeError("Start date is after end date!")
        try:
            kpi_data: dict = self.metrics_service.get_kpi_metrics(
                airport_code, start_date, end_date
            )
            monthly_metrics: List[MonthlyWeatherMetrics] = []
            weekly_metrics: List[WeeklyWeatherMetrics] = []
            daily_metrics: List[DailyWeatherMetrics] = []
            if agg_level == AggLevelEnum.YEAR or agg_level == AggLevelEnum.MONTH:
                monthly_metrics_dict: List[dict] = (
                    self.metrics_service.get_monthly_metrics(
                        airport_code, start_date, end_date
                    )
                )
                monthly_metrics = type(self)._list_validate_model(
                    monthly_metrics_dict, MonthlyWeatherMetrics
                )
            elif agg_level == AggLevelEnum.WEEK:
                weekly_metrics_dict: List[dict] = (
                    self.metrics_service.get_weekly_metrics(
                        airport_code, start_date, end_date
                    )
                )
                weekly_metrics = type(self)._list_validate_model(
                    weekly_metrics_dict, WeeklyWeatherMetrics
                )
            else:
                daily_metrics_dict: List[dict] = self.metrics_service.get_daily_metrics(
                    airport_code, start_date, end_date
                )
                daily_metrics = type(self)._list_validate_model(
                    daily_metrics_dict, DailyWeatherMetrics
                )
            return type(self)._construct_dashboard_response(
                airport_code,
                start_date,
                end_date,
                kpi_data,
                monthly_metrics,
                weekly_metrics,
                daily_metrics,
            )
        except Exception as e:
            logger.error(f"Error encountered while fetching data: {e}")
            raise ValueError(f"Dashboard data error encountered: {str(e)}") from e

    @classmethod
    def _list_validate_model(
        cls, metrics: List[dict], metric_class: type[M]
    ) -> List[M]:
        return [
            cls._validate_model(metric_dict, metric_class) for metric_dict in metrics
        ]

    @staticmethod
    def _validate_model(metric_dict: dict, metric_class: type[M]) -> M:
        return metric_class.model_validate(metric_dict)

    @staticmethod
    def _construct_dashboard_response(
        airport_code: str,
        start_date: date,
        end_date: date,
        data: dict,
        monthly_metrics: List[MonthlyWeatherMetrics],
        weekly_metrics: List[WeeklyWeatherMetrics],
        daily_metrics: List[DailyWeatherMetrics],
    ) -> SingleLocationDashboardDataResponse:
        kpi_data = {}
        kpi_data["max_temp"] = data["max_temp"]
        kpi_data["min_temp"] = data["min_temp"]
        kpi_data["precipitation_days_sum"] = data["precipitation_days_sum"]
        kpi_data["total_precipitation"] = data["total_precipitation"]
        kpi_data["max_wind_speed"] = data["max_wind_speed"]
        kpi_data["min_wind_speed"] = data["min_wind_speed"]

        result = {}
        result["airport_code"] = airport_code
        result["start_date"] = start_date
        result["end_date"] = end_date
        result["kpi_data"] = kpi_data
        result["monthly_metrics"] = monthly_metrics
        result["weekly_metrics"] = weekly_metrics
        result["daily_metrics"] = daily_metrics
        return SingleLocationDashboardDataResponse.model_validate(result)

    @staticmethod
    def _convert_to_response(
        locations: List[LocationResponse], dates: List[DateResponse]
    ) -> FilterOptionsResponse:
        response = {}
        response["locations"] = locations
        response["date_range"] = dates

        return FilterOptionsResponse.model_validate(response)
