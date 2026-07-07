from typing import List

from db.tables.config import LocationDB
from repository import LocationRepository
from models.response import LocationResponse


class LocationService:
    def __init__(self, location_repo: LocationRepository) -> None:
        self.location_repo = location_repo

    def get_locations(self) -> List[LocationResponse]:
        """Retrieve all known locations.

        Args:
            None.

        Returns:
            List[LocationResponse]: One response model per known location.

        Raises:
            ValueError: If no locations are found.
        """
        locations: List[LocationDB] = self.location_repo.get_locations()
        if not locations:
            raise ValueError("No location information found!")
        return self._convert_to_responses(locations)

    def _convert_to_responses(
        self, locations: List[LocationDB]
    ) -> List[LocationResponse]:
        return [self._convert_to_response(location) for location in locations]

    def _convert_to_response(self, location: LocationDB) -> LocationResponse:
        return LocationResponse.model_validate(location)
