import logging
from typing import List

from models.response import DateResponse, FilterOptionsResponse, LocationResponse
from services import LocationService, DateService

logger = logging.getLogger(__name__)


class DashboardService:
    def __init__(
        self, location_service: LocationService, date_service: DateService
    ) -> None:
        self.location_service = location_service
        self.date_service = date_service

    def get_options(self) -> FilterOptionsResponse:
        try:
            locations: List[LocationResponse] = self.location_service.get_locations()
            dates: List[DateResponse] = self.date_service.get_available_date_range()
            return type(self)._convert_to_response(locations, dates)
        except Exception as e:
            logger.error(f"Error encountered while fetching options: {e}")
            raise ValueError(f"Dashboard data error encountered: {str(e)}") from e

    @staticmethod
    def _convert_to_response(
        locations: List[LocationResponse], dates: List[DateResponse]
    ) -> FilterOptionsResponse:
        response = {}
        response["locations"] = locations
        response["date_range"] = dates

        return FilterOptionsResponse.model_validate(response)
