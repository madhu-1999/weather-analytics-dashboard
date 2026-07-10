from datetime import date
from urllib.parse import urljoin

import requests
import streamlit as st

from config import BACKEND_BASE_URL, DATA_ENDPOINT, OPTIONS_ENDPOINT
from models import AggLevel


@st.cache_data
def fetch_api_data(url: str) -> dict | None:
    """Fetch and cache JSON from a fully-qualified backend URL.

    Caching is keyed on the URL string, so callers naturally get a fresh
    fetch whenever any query parameter (airport, dates, agg level) changes.

    Args:
        url: Fully-qualified endpoint URL, including query string.

    Returns:
        The parsed JSON response, or None if the request failed.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def fetch_filter_options() -> dict | None:
    """Fetch the airport list and available date range for sidebar filters."""
    url = urljoin(BACKEND_BASE_URL, OPTIONS_ENDPOINT)
    return fetch_api_data(url)


def fetch_dashboard_data(
    airport_code: str,
    start_date: date,
    end_date: date,
    agg_level: AggLevel = AggLevel.YEAR,
) -> dict | None:
    """Fetch KPI and metrics data for one airport over a date range.

    Args:
        airport_code: Airport identifier selected in the sidebar.
        start_date: Inclusive start of the reporting window.
        end_date: Inclusive end of the reporting window.
        agg_level: Granularity to aggregate the underlying daily data to.

    Returns:
        Parsed JSON payload with 'kpi_data' plus the metrics collection
        matching agg_level, or None on failure.
    """
    url = (
        urljoin(BACKEND_BASE_URL, DATA_ENDPOINT)
        + f"/{airport_code}?start_date={start_date}&end_date={end_date}&agg_level={agg_level}"
    )
    return fetch_api_data(url)
