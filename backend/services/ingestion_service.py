from datetime import date
import json
import logging
import os
import time
from typing import List
from urllib.parse import urlencode

from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.orm import Session
from urllib3 import Retry

from db.tables.config import IngestedFilesDB
from models.constants import IngestionStatus
from models.response import IngestedFileResponse, LocationResponse
from .location_service import LocationService

load_dotenv()

DELAY_SECONDS = 2

logger = logging.getLogger(__name__)


class IngestionService:
    """Coordinates fetching weather data for known locations and tracking ingestion status."""

    def __init__(self, ingested_files_repo, location_service: LocationService) -> None:
        self.ingested_files_repo = ingested_files_repo
        self.location_service = location_service

    async def start_ingestion(self, start_date: date, end_date: date) -> None:
        """Ingest weather/climate data for all known locations over a date range.

        Args:
            start_date (date): First date (inclusive) of the data range to
                ingest for each location.
            end_date (date): Last date (inclusive) of the data range to
                ingest for each location.

        Returns:
            None.

        Raises:
            ValueError: If ``DAILY_PARAMS`` is not set in the environment.
            json.JSONDecodeError: If location data cannot be parsed as JSON.
            AttributeError: If an expected attribute is missing from a
                location or its data.
        """
        DAILY_PARAMS = os.getenv("DAILY_PARAMS")
        if not DAILY_PARAMS:
            raise ValueError(
                "Critical Error: 'DAILY_PARAMS' is missing from the .env file."
            )

        try:
            cities: List[LocationResponse] = self.location_service.get_locations()
            for city in cities:
                kwargs: dict = city.model_dump()
                kwargs["start"] = start_date
                kwargs["end"] = end_date
                kwargs["daily"] = DAILY_PARAMS
                await self.ingest_data(**kwargs)
                time.sleep(DELAY_SECONDS)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding failed: {e.msg}")
            logger.error(
                f"Error occurred at line {e.lineno}, column {e.colno} (char {e.pos})"
            )
            raise e
        except AttributeError as e:
            logger.error(f"Missing attribute: {e}")
            raise e

    async def ingest_data(self, **kwargs) -> None:
        """Fetch daily weather/climate data for one location, save it to a JSON file
        with the filename format ``{airport_code}-{start}_{end}.json`` and insert a record in the
        ingestion tracking table.

        Args:
            **kwargs: Location and query parameters. Expected keys:
                lat (float): Latitude of the location, in decimal degrees.
                lon (float): Longitude of the location, in decimal degrees.
                start (date): First date (inclusive) of the data range.
                end (date): Last date (inclusive) of the data range.
                daily (str): Comma-separated list of daily variables to request
                    (e.g. ``"temperature_2m_max,precipitation_sum"``).
                timezone (str): Timezone name to apply to the returned data
                    (e.g. ``"America/Los_Angeles"``).
                airport_code (str): Short code identifying the location, used
                    as part of the output filename.
                state (str): State/region name, attached to the saved record.
                city (str): City name, attached to the saved record.

        Returns:
            None.

        Raises:
            ValueError: If ``API_BASE_URL`` or ``DATA_DIR`` is not set in the
                environment.

        Example:
            >>> from datetime import date
            >>> ingest_data(
            ...     lat=37.62,
            ...     lon=-122.38,
            ...     start=date(2026, 7, 1),
            ...     end=date(2026, 7, 2),
            ...     daily="temperature_2m_max,precipitation_sum",
            ...     timezone="America/Los_Angeles",
            ...     airport_code="SFO",
            ...     state="CA",
            ...     city="San Francisco",
            ... )
        """
        BASE_URL = os.getenv("API_BASE_URL")
        DATA_DIR = os.getenv("DATA_DIR")
        if not BASE_URL:
            raise ValueError(
                "Critical Error: 'API_BASE_URL' is missing from the .env file."
            )
        if not DATA_DIR:
            raise ValueError(
                "Critical Error: 'DATA_DIR' is missing from the .env file."
            )

        start: date = kwargs["start"]
        end: date = kwargs["end"]
        query_params = {
            "latitude": kwargs["latitude"],
            "longitude": kwargs["longitude"],
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "daily": kwargs["daily"],
            "timezone": kwargs["timezone"],
        }

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],  # Retry on these HTTP status codes
            allowed_methods=["GET"],
        )

        # Mount the retry logic to a requests session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        try:
            logger.info(f"Fetching data with query params: {query_params}...")

            # Create query parameters string
            encoded_params = urlencode(query_params)
            # Change %2C back to literal comma
            fixed_params = encoded_params.replace("%2C", ",")
            full_url = f"{BASE_URL}?{fixed_params}"

            # We add a timeout (connect timeout, read timeout) so the script doesn't hang forever
            response = session.get(full_url, timeout=(5, 15))
            # Automatically raises an HTTPError if the response code was 4xx or 5xx
            response.raise_for_status()
            result = response.json()
            result["airport_code"] = kwargs["airport_code"]
            result["state"] = kwargs["state"]
            result["city"] = kwargs["city"]

            filename = (
                f"{kwargs['airport_code']}-{start.isoformat()}_{end.isoformat()}.json"
            )
            logger.info(f"Saving data to {filename}...")
            with open(os.path.join(DATA_DIR, filename), "w") as f:
                json.dump(result, f, indent=4)
            logger.info(f"Saved data to {filename}!")

            logger.info(
                f"Inserting {filename} record into ingestion table with status PENDING..."
            )
            self.ingested_files_repo.insert_record(
                filename, kwargs["airport_code"], start, end
            )
            logger.info(
                f"Inserted {filename} record into ingestion table successfully!"
            )
        except requests.exceptions.ConnectionError as ce:
            logger.error(
                f"Network Error: Could not connect to the server. Details: {ce}"
            )
        except requests.exceptions.Timeout as te:
            logger.error(f"Timeout Error: The request timed out. Details: {te}")
        except requests.exceptions.HTTPError as he:
            logger.error(f"HTTP Error occurred: {he}")
        except requests.exceptions.RequestException as re:
            logger.error(
                f"An ambiguous error occurred while handling your request: {re}"
            )
        except Exception as e:
            logger.error(f"An unexpected non-requests error occurred: {e}")

    def get_pending_files(self) -> List[IngestedFileResponse]:
        """Retrieve all files currently pending processing.

        Returns:
            List[IngestedFileResponse]: Pending ingested-file records,
            Empty if none are pending.

        Raises:
            DatabaseError: If the underlying repository query fails.
        """
        pending_files: List[IngestedFilesDB] = (
            self.ingested_files_repo.get_pending_files()
        )

        return self._convert_to_responses(pending_files)

    def update_status(
        self, session: Session, ingestion_id: int, status: IngestionStatus
    ) -> None:
        """Update the tracked status of an ingested file.

        Args:
            session (Session): SQLAlchemy session to use for the update.
            ingestion_id (int): Identifier of the ingested-file record to
                update.
            status (IngestionStatus): New status to assign to the record.

        Returns:
            None.

        Raises:
            DatabaseError: If the underlying repository update fails.
        """
        self.ingested_files_repo.update_status(session, ingestion_id, status)

    def _convert_to_responses(
        self, files: List[IngestedFilesDB]
    ) -> List[IngestedFileResponse]:
        """Convert a list of ingested-file database records to response models.

        Args:
            files (List[IngestedFilesDB]): Database records to convert.

        Returns:
            List[IngestedFileResponse]: One response model per input record,
            in the same order.
        """
        return [self._convert_to_response(file) for file in files]

    def _convert_to_response(self, file: IngestedFilesDB) -> IngestedFileResponse:
        """Convert a single ingested-file database record to a response model.

        Args:
            file (IngestedFilesDB): Database record to convert.

        Returns:
            IngestedFileResponse: Response model built from ``file``.
        """
        return IngestedFileResponse.model_validate(file)
