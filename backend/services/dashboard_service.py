from datetime import date
import logging
from typing import List

from exceptions import InvalidDateRangeError
from models.response import (
    DateResponse,
    FilterOptionsResponse,
    LocationResponse,
    SingleLocationDashboardDataResponse,
)
from .date_service import DateService
from .location_service import LocationService
from .metrics_service import MetricsService

logger = logging.getLogger(__name__)


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
        self, airport_code: str, start_date: date, end_date: date
    ) -> SingleLocationDashboardDataResponse:
        if start_date > end_date:
            raise InvalidDateRangeError("Start date is after end date!")
        try:
            data: dict = self.metrics_service.get_data(
                airport_code, start_date, end_date
            )
            return type(self)._construct_dashboard_response(data)
        except Exception as e:
            logger.error(f"Error encountered while fetching data: {e}")
            raise ValueError(f"Dashboard data error encountered: {str(e)}") from e

    @staticmethod
    def _construct_dashboard_response(
        data: dict,
    ) -> SingleLocationDashboardDataResponse:
        kpi_data = {}
        kpi_data["max_temp"] = data["max_temp"]
        kpi_data["min_temp"] = data["min_temp"]
        kpi_data["precipitation_days_sum"] = data["precipitation_days_sum"]
        kpi_data["total_precipitation"] = data["total_precipitation"]
        kpi_data["max_wind_speed"] = data["max_wind_speed"]
        kpi_data["min_wind_speed"] = data["min_wind_speed"]

        result = {}
        result["kpi_data"] = kpi_data
        return SingleLocationDashboardDataResponse.model_validate(result)

    @staticmethod
    def _convert_to_response(
        locations: List[LocationResponse], dates: List[DateResponse]
    ) -> FilterOptionsResponse:
        response = {}
        response["locations"] = locations
        response["date_range"] = dates

        return FilterOptionsResponse.model_validate(response)
