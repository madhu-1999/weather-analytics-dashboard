from typing import List

from models.response import DateResponse
from repository import DateRepository


class DateService:
    def __init__(self, date_repo: DateRepository) -> None:
        self.date_repo = date_repo

    def get_available_date_range(self) -> List[DateResponse]:
        """Determine the overall span of dates for which weather data exists.

        Returns:
            The boundary dates (earliest and latest) available in the system,
            formatted for client consumption.
        """
        dates: List[dict] = self.date_repo.get_available_date_range()
        return type(self)._convert_to_responses(dates)

    @classmethod
    def _convert_to_responses(cls, dates: List[dict]) -> List[DateResponse]:
        """Convert raw date records into response models.

        Args:
            dates: Raw date records as returned by the repository layer.

        Returns:
            Validated date response models.
        """
        return [cls._convert_to_response(d) for d in dates]

    @staticmethod
    def _convert_to_response(d: dict) -> DateResponse:
        """Convert a single raw date record into a response model.

        Args:
            d: A raw date record.

        Returns:
            The validated date response.
        """
        response = {}
        response["weather_date"] = d["weather_date"]
        response["day_of_month"] = d["day_of_month"]
        response["month_name"] = d["month_name"]
        response["year"] = d["year_int"]

        return DateResponse.model_validate(response)
