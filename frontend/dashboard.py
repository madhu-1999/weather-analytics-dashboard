from datetime import datetime, date
from enum import StrEnum
import os
from typing import Optional

from dotenv import load_dotenv
from urllib.parse import urljoin
from pandas import DataFrame
import requests
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as bg
from plotly.subplots import make_subplots


load_dotenv()
global BACKEND_BASE_URL
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL")
if not BACKEND_BASE_URL:
    raise ValueError(
        "Critical Error: 'BACKEND_BASE_URL' is missing from the .env file."
    )

ASSETS_DIR = os.getenv("ASSETS_DIR")
if not ASSETS_DIR:
    raise ValueError("Critical Error: 'ASSETS_DIR' is missing from the .env file.")

global GET_DATA_ENDPT
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


class AggLevelEnum(StrEnum):
    YEAR = "year"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"


MAPPING_TO_COLUMN = {
    "kpi": "kpi_data",
    AggLevelEnum.YEAR: "monthly_metrics",
    AggLevelEnum.MONTH: "monthly_metrics",
    AggLevelEnum.WEEK: "weekly_metrics",
    AggLevelEnum.DAY: "daily_metrics",
}

WEATHER_METRIC_COLS = [
    "temp_mean",
    "temp_max",
    "temp_min",
    "wind_speed_mean",
    "wind_speed_max",
    "wind_speed_min",
    "wind_gusts_mean",
    "wind_gusts_max",
    "wind_gusts_min",
    "precipitation_sum",
    "precipitation_hours",
]

LINE_CHART_AGG_MAPPING = {
    "temp_mean": "mean",
    "temp_max": "max",
    "temp_min": "min",
    "wind_speed_mean": "mean",
    "wind_speed_max": "max",
    "wind_speed_min": "min",
    "wind_gusts_mean": "mean",
    "wind_gusts_max": "max",
    "wind_gusts_min": "min",
    "precipitation_sum": "sum",
    "precipitation_hours": "sum",
}


class MetricOptions(StrEnum):
    TEMPERATURE = "Temperature"
    WIND_SPEED = "Wind Speed"
    WIND_GUST = "Wind Gust Speed"
    PRECIPITATION = "Precipitation"


# Map aggregation levels to their specific configurations
AGG_CONFIG = {
    "year": {
        "enum": AggLevelEnum.YEAR,
        "x_axis": "year_int",
        "x_label": "Year",
    },
    "month": {
        "enum": AggLevelEnum.MONTH,
        "x_axis": "month_str",
        "x_label": "Month",
    },
    "week": {
        "enum": AggLevelEnum.WEEK,
        "x_axis": "week_str",
        "x_label": "Week",
    },
    "day": {"enum": AggLevelEnum.DAY, "x_axis": "weather_date", "x_label": "Day"},
}

# Map metrics to their Plotly chart configurations
METRIC_CONFIG = {
    MetricOptions.TEMPERATURE: {
        "y_fields": ["temp_mean", "temp_max", "temp_min"],
        "title": "Temperature trends over time",
        "y_label": "Temperature (°C)",
    },
    MetricOptions.WIND_SPEED: {
        "y_fields": ["wind_speed_mean", "wind_speed_max", "wind_speed_min"],
        "title": "Wind Speed trends over time",
        "y_label": "Wind Speed (km/h)",
    },
    MetricOptions.WIND_GUST: {
        "y_fields": ["wind_gusts_mean", "wind_gusts_max", "wind_gusts_min"],
        "title": "Wind Gust trends over time",
        "y_label": "Wind Gust (km/h)",
    },
    MetricOptions.PRECIPITATION: {
        "y_fields": ["precipitation_sum"],
        "title": "Precipitation over time",
        "y_label": "Precipitation (mm)",
    },
}


def fetch_dashboard_data(
    agg_level: AggLevelEnum = AggLevelEnum.YEAR,
) -> Optional[dict]:
    if not BACKEND_BASE_URL:
        raise ValueError(
            "Critical Error: 'BACKEND_BASE_URL' is missing from the .env file."
        )

    data_endpt = (
        urljoin(BACKEND_BASE_URL, GET_DATA_ENDPT)
        + f"/{airport_code_select}?start_date={start_date}&end_date={end_date}&agg_level={agg_level}"
    )

    dashboard_data = fetch_api_data(data_endpt)
    return dashboard_data


def clean_metrics(data: dict, agg_level: "AggLevelEnum") -> DataFrame:
    """Normalize `agg_level` (accepts enum or string) and return cleaned DataFrame."""
    # Prefer enum-key lookup in MAPPING_TO_COLUMN, fall back to string value
    agg_value = getattr(agg_level, "value", str(agg_level))
    mapping_key = agg_level if agg_level in MAPPING_TO_COLUMN else agg_value
    mapping_col = MAPPING_TO_COLUMN.get(mapping_key) or MAPPING_TO_COLUMN.get(agg_value)
    if mapping_col is None:
        raise ValueError(f"Unknown aggregation level: {agg_level}")

    df = pd.DataFrame(data[mapping_col])
    df[WEATHER_METRIC_COLS] = df[WEATHER_METRIC_COLS].astype(dtype="float64")

    col_name = AGG_CONFIG[agg_value]["x_axis"]

    if agg_value == "month":
        df[col_name] = (
            pd.to_datetime(df["month_int"], format="%m").dt.month_name().str[:3]
            + " "
            + df["year_int"].astype(str)
        )
    elif agg_value == "week":
        padded_week = df["week_of_year"].astype(str).str.zfill(2)
        iso_string = df["year_int"].astype(str) + padded_week + "1"
        date_series = pd.to_datetime(iso_string, format="%G%V%u")

        df[col_name] = (
            date_series.dt.strftime("%b")
            + " "
            + df["year_int"].astype(str)
            + ", Week "
            + df["week_of_year"].astype(str)
        )

    return df


def render_metric_line_chart(metric: MetricOptions, agg_level: AggLevelEnum):
    """Fetches data, processes it, and renders a line chart for a given metric and aggregation."""
    agg_info = AGG_CONFIG[agg_level]
    metric_info = METRIC_CONFIG[metric]

    dashboard_data = fetch_dashboard_data(agg_level=agg_info["enum"])

    if not dashboard_data:
        st.error("No data found!")
        return

    df = clean_metrics(dashboard_data, agg_level=agg_info["enum"])
    if AggLevelEnum.YEAR == agg_level:
        df = df.groupby(by=agg_info["x_axis"]).agg(LINE_CHART_AGG_MAPPING).reset_index()

    fig = px.line(
        df,
        x=agg_info["x_axis"],
        y=metric_info["y_fields"],
        markers=True,
        title=metric_info["title"],
        labels={
            agg_info["x_axis"]: agg_info["x_label"],
            "value": metric_info["y_label"],
            "variable": "Metric Type",
        },
    )
    fig.update_xaxes(type="category")
    fig.update_xaxes(nticks=10)
    fig.update_yaxes(nticks=5)

    st.plotly_chart(fig, width="stretch")


# ---- Main execution UI container ----
dashboard_data = fetch_dashboard_data()
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

    # Metric selector for line chart
    metric_select = st.selectbox(
        "Metric",
        options=list(MetricOptions),
    )

    tab_names = list(key.capitalize() for key in AGG_CONFIG.keys())
    tabs = st.tabs(tab_names, on_change="rerun")

    for tab, name in zip(tabs, tab_names):
        if tab.open:
            with tab:
                with st.spinner(f"Loading {name.lower()} trends..."):
                    render_metric_line_chart(
                        metric=metric_select, agg_level=AggLevelEnum[name.upper()]
                    )

    st.divider()
    with st.container():
        monthly_data = fetch_dashboard_data(agg_level=AggLevelEnum.MONTH)
        if not monthly_data:
            st.error("No data found!")
        else:
            precipitation_df = clean_metrics(monthly_data, agg_level=AggLevelEnum.MONTH)
            precip_fig = make_subplots(specs=[[{"secondary_y": True}]])

            # Add Bars for Precipitation Sum (Primary Axis)
            precip_fig.add_trace(
                bg.Bar(
                    x=precipitation_df["month_str"],
                    y=precipitation_df["precipitation_sum"],
                    name="Precipitation Sum (mm)",
                    marker_color="rgb(55, 83, 109)",
                ),
                secondary_y=False,
            )

            # Add Line for Precipitation Hours (Secondary Axis)
            precip_fig.add_trace(
                bg.Scatter(
                    x=precipitation_df["month_str"],
                    y=precipitation_df["precipitation_hours"],
                    name="Precipitation Hours",
                    mode="lines+markers",
                    marker_color="rgb(26, 118, 255)",
                    line=dict(width=3),
                ),
                secondary_y=True,
            )

            precip_fig.update_layout(
                title_text="Monthly Precipitation: Volume vs. Duration",
                xaxis=dict(
                    type="category", title="Month", rangeslider=dict(visible=True)
                ),
                legend=dict(
                    orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
                ),
            )

            precip_fig.update_yaxes(title_text="<b>Sum</b> (mm)", secondary_y=False)
            precip_fig.update_yaxes(
                title_text="<b>Duration</b> (Hours)", secondary_y=True
            )
            if len(precipitation_df) > 12:
                precip_fig.update_xaxes(range=[0, 11])
            st.plotly_chart(precip_fig, width="stretch")

        with st.expander("Why do these charts sometimes show different totals?"):
            st.markdown("""
            * **Cloud Cover** is calculated as a strict **24-hour mathematical average** of sky coverage.
            * **Weather Conditions (Pie Chart)** reflects the **dominant or highest-impact weather event** recorded that day.
            
            *Example:* A day that is clear for 20 hours but experiences a sudden 4-hour heavy thunderstorm will be classified as **"Thunderstorm"** in the condition chart, but its average daily cloud cover might only register as **"Mainly Clear"**.
            """)
        col1, col2 = st.columns(2, gap="small", vertical_alignment="center")

        daily_data = fetch_dashboard_data(agg_level=AggLevelEnum.DAY)
        if not daily_data:
            st.error("No data found!")
        else:
            daily_df = clean_metrics(daily_data, agg_level=AggLevelEnum.DAY)

            # Mapping avg cloud cover % to categories
            bins = [-0.1, 0.0, 25.0, 75.0, 100.0]
            labels = ["Clear sky", "Mainly clear", "Partly cloudy", "Overcast"]
            daily_df["cloud_category"] = pd.cut(
                daily_df["cloud_cover_mean"],
                bins=bins,
                labels=labels,
                include_lowest=True,
            )

            # Get count per category safely without column name collision
            counts = daily_df["cloud_category"].value_counts().reset_index()

            category_colors = {
                "Clear sky": "#FFD700",  # Sunny Yellow
                "Mainly clear": "#90EE90",  # Light Green
                "Partly cloudy": "#ADD8E6",  # Light Blue
                "Overcast": "#808080",  # Muted Grey
            }

            legend_labels = {
                "Clear sky": "Clear sky (0%)",
                "Mainly clear": "Mainly clear (1% - 25%)",
                "Partly cloudy": "Partly cloudy (26% - 75%)",
                "Overcast": "Overcast (76% - 100%)",
                "cloud_category": "Cloud Category Mapping",
                "count": "Days Count",
            }

            # Apply the labels to counts
            counts["legend_group"] = counts["cloud_category"].map(legend_labels)
            cloud_cover_fig = px.bar(
                counts,
                x="cloud_category",
                y="count",
                color="legend_group",
                color_discrete_map=category_colors,
                title="24-Hour Avg Cloud Coverage",
                labels={
                    "cloud_category": "Cloud cover category",
                    "count": "count",
                },
            )

            cloud_cover_fig.update_layout(
                legend_title_text="Category Ranges",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=1.02),
            )
            cloud_cover_fig.update_xaxes(nticks=10)
            cloud_cover_fig.update_yaxes(nticks=5)
            col1.plotly_chart(cloud_cover_fig, width="stretch")

            weather_codes_fig = px.pie(
                daily_df,
                names="weather_code_mapping",
                title="Dominant Weather Impact Events",
                hole=0.4,
                labels={
                    "weather_code_mapping": "Weather Condition",
                    "count": "Number of Days",
                },
            )

            weather_codes_fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                insidetextorientation="horizontal",
                hovertemplate="<b>%{label}</b><br>Days: %{value}<br>Percentage: %{percent}<extra></extra>",
            )

            weather_codes_fig.update_layout(
                showlegend=True,
                legend_title_text="Conditions",
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05,
                ),
                margin=dict(
                    t=50, b=20, l=20, r=20
                ),  # Compact margins for better layout fit
            )
            col2.plotly_chart(weather_codes_fig, width="stretch")
