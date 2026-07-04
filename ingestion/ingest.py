import argparse
from datetime import date, datetime
import json
import os
import time
from typing import List
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from urllib.parse import urlencode

from db.db import get_session
from logger import logger
from repository import IngestedFilesRepository

load_dotenv()
DELAY_SECONDS = 5


def ingest_data(**kwargs) -> None:
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
        raise ValueError("Critical Error: 'DATA_DIR' is missing from the .env file.")

    start: date = kwargs["start"]
    end: date = kwargs["end"]
    query_params = {
        "latitude": kwargs["lat"],
        "longitude": kwargs["lon"],
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
        with get_session() as session:
            ingested_files_repo = IngestedFilesRepository(session)
            ingested_files_repo.insert_record(
                filename, kwargs["airport_code"], start, end
            )
        logger.info(f"Inserted {filename} record into ingestion table successfully!")
    except requests.exceptions.ConnectionError as ce:
        logger.error(f"Network Error: Could not connect to the server. Details: {ce}")
    except requests.exceptions.Timeout as te:
        logger.error(f"Timeout Error: The request timed out. Details: {te}")
    except requests.exceptions.HTTPError as he:
        logger.error(f"HTTP Error occurred: {he}")
    except requests.exceptions.RequestException as re:
        logger.error(f"An ambiguous error occurred while handling your request: {re}")
    except Exception as e:
        logger.error(f"An unexpected non-requests error occurred: {e}")


def valid_date(date_string: str) -> date:
    """Parse a string in YYYY-MM-DD format into a date object.

    Intended for use as an ``argparse`` ``type=`` callback so that invalid
    date strings surface as a standard argparse usage error.

    Args:
        date_string (str): Date string to parse, expected in ``YYYY-MM-DD``
            format (e.g. ``"2026-07-01"``).

    Returns:
        date: The parsed date.

    Raises:
        argparse.ArgumentTypeError: If ``date_string`` does not match the
            ``YYYY-MM-DD`` format.

    Example:
        >>> parser.add_argument("start", type=valid_date)
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except ValueError:
        msg = f"Not a valid date: '{date_string}'. Expected format: YYYY-MM-DD."
        raise argparse.ArgumentTypeError(msg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "start", type=valid_date, help="Start Date in YYYY-MM-DD format"
    )
    parser.add_argument("end", type=valid_date, help="End Date in YYYY-MM-DD format")
    args = parser.parse_args()

    CITIES_STR = os.getenv("CITIES")
    if not CITIES_STR:
        raise ValueError("Critical Error: 'CITIES' is missing from the .env file.")

    DAILY_PARAMS = os.getenv("DAILY_PARAMS")
    if not DAILY_PARAMS:
        raise ValueError(
            "Critical Error: 'DAILY_PARAMS' is missing from the .env file."
        )

    try:
        cities_config: List[dict] = json.loads(CITIES_STR)["cities"]
        for city in cities_config:
            kwargs: dict = city
            kwargs["start"] = args.start
            kwargs["end"] = args.end
            kwargs["daily"] = DAILY_PARAMS
            ingest_data(**kwargs)
            time.sleep(DELAY_SECONDS)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding failed: {e.msg}")
        logger.error(
            f"Error occurred at line {e.lineno}, column {e.colno} (char {e.pos})"
        )
    except AttributeError as e:
        logger.error(f"Missing attribute: {e}")

# Example call: python ingest.py 2026-07-01 2026-07-02
