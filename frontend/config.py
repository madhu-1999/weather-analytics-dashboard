"""Application configuration loaded from environment variables."""

import os

from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str) -> str:
    """Fetch a required environment variable.
    Args:
        key: Name of the environment variable to read.

    Returns:
        The variable's value.

    Raises:
        ValueError: If the variable is unset or empty.
    """
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Critical Error: '{key}' is missing from the .env file.")
    return value


BACKEND_BASE_URL = _require_env("BACKEND_BASE_URL")
ASSETS_DIR = _require_env("ASSETS_DIR")

OPTIONS_ENDPOINT = "/dashboards/options"
DATA_ENDPOINT = "/dashboards/data"
