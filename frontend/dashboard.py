from datetime import datetime, date
import os

from dotenv import load_dotenv
from urllib.parse import urljoin
import requests
import streamlit as st
import pandas as pd

load_dotenv()
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL")
if not BACKEND_BASE_URL:
    raise ValueError(
        "Critical Error: 'BACKEND_BASE_URL' is missing from the .env file."
    )

ASSETS_DIR = os.getenv("ASSETS_DIR")
if not ASSETS_DIR:
    raise ValueError("Critical Error: 'ASSETS_DIR' is missing from the .env file.")

GET_OPTIONS_ENDPT = "/dashboards/options"
GET_DATA_ENDPT = "/dashboards/data"

st.set_page_config(layout="wide")


@st.cache_data
def fetch_api_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


# ---- Set Locations to sidebar ----
target_url: str = urljoin(BACKEND_BASE_URL, GET_OPTIONS_ENDPT)
data = fetch_api_data(target_url)
if not data:
    raise ValueError("No filter options found!")

locations = pd.DataFrame(data["locations"])
locations = locations.set_index("airport_code")
with st.sidebar:
    airport_code_select = st.selectbox(
        "Airport",
        options=locations.index,
        format_func=lambda code: (
            code
            + " "
            + locations.loc[code]["city"]
            + ","
            + locations.loc[code]["state"]
        ),
    )
# ---- Set dashboard title based on location selection ----
st.title(f"{airport_code_select} Weather Overview")

# ---- Get date range ----
date_range = data["date_range"]
if not date_range:
    st.write("No data found!")

min_date_obj: dict = date_range[0]
min_date: date = datetime.strptime(min_date_obj["weather_date"], "%Y-%m-%d")

max_date_obj: dict = date_range[1] if len(date_range) > 1 else date_range[0]
max_date: date = datetime.strptime(max_date_obj["weather_date"], "%Y-%m-%d")
with st.sidebar:
    start_date = st.date_input(
        "Start date",
        min_date,
        min_value=min_date,
        max_value=max_date,
        format="YYYY-MM-DD",
        key=1,
    )

    end_date = st.date_input(
        "End Date",
        max_date,
        min_value=start_date,
        max_value=max_date,
        format="YYYY-MM-DD",
        key=2,
    )
st.subheader(
    f"{min_date_obj['month_name']} {min_date_obj['day_of_month']}, {min_date_obj['year']} - {max_date_obj['month_name']} {max_date_obj['day_of_month']}, {max_date_obj['year']}",
    divider="blue",
)


# ---- KPI card definition ----
def weather_kpi_card(
    title: str,
    max_label: str,
    max_value: str,
    min_label: str,
    min_value: str,
    icon: str,
):
    """Renders a standard 2-column metric card inside a sub-container."""
    with st.container(border=False):
        st.subheader(title, text_alignment="center")
        col1, col2 = st.columns(2, border=True, vertical_alignment="center")

        # Left Metric
        col1.badge(max_label, icon=icon, color="red")
        col1.subheader(max_value, text_alignment="center")

        # Right Metric
        col2.badge(min_label, icon=icon, color="blue")
        col2.subheader(min_value, text_alignment="center")


# ---- Main execution UI container ----
data_endpt = (
    urljoin(BACKEND_BASE_URL, GET_DATA_ENDPT)
    + f"/{airport_code_select}?start_date={start_date}&end_date={end_date}"
)
dashboard_data = fetch_api_data(data_endpt)
if not dashboard_data:
    st.error("No data found!")
else:
    with st.container(
        horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
    ):
        kpi_col1, kpi_col2, kpi_col3 = st.columns(
            3, gap="medium", vertical_alignment="center"
        )
        kpi_data = dashboard_data["kpi_data"]
        # Render Temperature
        with kpi_col1:
            weather_kpi_card(
                title="Temperature",
                max_label="Maximum",
                max_value=f"{kpi_data['max_temp']}°C",
                min_label="Minimum",
                min_value=f"{kpi_data['min_temp']}°C",
                icon=":material/device_thermostat:",
            )

        # Render Precipitation
        with kpi_col2:
            weather_kpi_card(
                title="Precipitation",
                max_label="Total Days",
                max_value=f"{kpi_data['precipitation_days_sum']} days",
                min_label="Total precipitation",
                min_value=f"{kpi_data['total_precipitation']} mm",
                icon=":material/rainy:",
            )

        # Render Wind Speed
        with kpi_col3:
            weather_kpi_card(
                title="Wind speed",
                max_label="Maximum",
                max_value=f"{kpi_data['max_wind_speed']} km/h",
                min_label="Minimum",
                min_value=f"{kpi_data['min_wind_speed']} km/h",
                icon=":material/air:",
            )

    st.divider()
