from typing import List

from models.response import DateResponse
from repository import DateRepository


class DateService:
    def __init__(self, date_repo: DateRepository) -> None:
        self.date_repo = date_repo

    def get_available_date_range(self) -> List[DateResponse]:
        dates: List[dict] = self.date_repo.get_available_date_range()
        return type(self)._convert_to_responses(dates)

    @classmethod
    def _convert_to_responses(cls, dates: List[dict]) -> List[DateResponse]:
        return [cls._convert_to_response(d) for d in dates]

    @staticmethod
    def _convert_to_response(d: dict) -> DateResponse:
        response = {}
        response["weather_date"] = d["weather_date"]
        response["day_of_month"] = d["day_of_month"]
        response["month_name"] = d["month_name"]
        response["year"] = d["year_int"]

        return DateResponse.model_validate(response)
