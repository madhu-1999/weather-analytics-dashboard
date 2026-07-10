"""Airport weather overview dashboard.

Renders KPI summary cards, a metric trend chart with selectable time
granularity, a precipitation volume-vs-duration chart, and a breakdown of
cloud cover and dominant weather conditions for a chosen airport and date
range.
"""

from datetime import date, datetime

import pandas as pd
import streamlit as st

from api_client import fetch_dashboard_data, fetch_filter_options
from charts import (
    build_cloud_cover_bar_chart,
    build_metric_line_chart,
    build_precipitation_dual_axis_chart,
    build_weather_conditions_pie_chart,
)
from components import weather_kpi_card
from process_data import bucket_cloud_cover, clean_metrics, rollup_to_yearly
from models import AGG_AXIS_CONFIG, AggLevel, MetricOption, YEARLY_ROLLUP_AGG

st.set_page_config(layout="wide")


def render_sidebar_filters(filter_options: dict) -> tuple[str, date, date, str]:
    """Render the airport and date-range selectors in the sidebar.

    Args:
        filter_options: Payload from fetch_filter_options containing
            'locations' and 'date_range'.

    Returns:
        A tuple of (selected_airport_code, start_date, end_date,
        available_range_label), where available_range_label describes the
        full span of data the backend has on offer (independent of what
        the user has currently selected).
    """
    locations = pd.DataFrame(filter_options["locations"]).set_index("airport_code")
    min_record, max_record = _available_date_bound_records(filter_options["date_range"])
    min_date = datetime.strptime(min_record["weather_date"], "%Y-%m-%d")
    max_date = datetime.strptime(max_record["weather_date"], "%Y-%m-%d")

    with st.sidebar:
        airport_code = st.selectbox(
            "Airport",
            options=locations.index,
            format_func=lambda code: (
                f"{code} {locations.loc[code]['city']},{locations.loc[code]['state']}"
            ),
        )

        start_date = st.date_input(
            "Start date",
            min_date,
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD",
            key="start_date",
        )
        end_date = st.date_input(
            "End Date",
            max_date,
            min_value=start_date,
            max_value=max_date,
            format="YYYY-MM-DD",
            key="end_date",
        )

    available_range_label = (
        f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
    )
    return airport_code, start_date, end_date, available_range_label


def _available_date_bound_records(date_range: list[dict]) -> tuple[dict, dict]:
    """Extract the earliest and latest data-availability records.

    Args:
        date_range: A one- or two-element list of date records marking the
            available data window's edges.

    Returns:
        A (min_record, max_record) tuple. When only one record is present,
        both bounds are that same record.
    """
    max_record = date_range[0]
    min_record = date_range[1] if len(date_range) > 1 else date_range[0]
    return min_record, max_record


def render_kpi_section(kpi_data: dict) -> None:
    """Render the three headline KPI cards: temperature, precipitation, wind.

    Args:
        kpi_data: The 'kpi_data' block from the dashboard data payload.
    """
    with st.container(
        horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
    ):
        kpi_col1, kpi_col2, kpi_col3 = st.columns(
            3, gap="medium", vertical_alignment="center"
        )

        with kpi_col1:
            weather_kpi_card(
                title="Temperature",
                max_label="Maximum",
                max_value=f"{kpi_data['max_temp']}°C",
                min_label="Minimum",
                min_value=f"{kpi_data['min_temp']}°C",
                icon=":material/device_thermostat:",
            )

        with kpi_col2:
            weather_kpi_card(
                title="Precipitation",
                max_label="Total Days",
                max_value=f"{kpi_data['precipitation_days_sum']} days",
                min_label="Total precipitation",
                min_value=f"{kpi_data['total_precipitation']} mm",
                icon=":material/rainy:",
            )

        with kpi_col3:
            weather_kpi_card(
                title="Wind speed",
                max_label="Maximum",
                max_value=f"{kpi_data['max_wind_speed']} km/h",
                min_label="Minimum",
                min_value=f"{kpi_data['min_wind_speed']} km/h",
                icon=":material/air:",
            )


def render_metric_trend_tab(
    airport_code: str,
    start_date: date,
    end_date: date,
    metric: MetricOption,
    agg_level: AggLevel,
) -> None:
    """Fetch, transform, and render the trend line chart for one tab.

    Args:
        airport_code: Selected airport identifier.
        start_date: Start of the selected reporting window.
        end_date: End of the selected reporting window.
        metric: Metric family selected in the dropdown above the tabs.
        agg_level: Aggregation level this tab represents.
    """
    with st.spinner(f"Loading {agg_level.lower()} trends..."):
        payload = fetch_dashboard_data(
            airport_code, start_date, end_date, agg_level=agg_level
        )
        if not payload:
            st.error("No data found!")
            return

        # There's no dedicated yearly endpoint; fetch monthly data and roll it up client-side
        source_level = AggLevel.MONTH if agg_level == AggLevel.YEAR else agg_level
        df = clean_metrics(payload, agg_level=source_level)
        if agg_level == AggLevel.YEAR:
            df = rollup_to_yearly(df, YEARLY_ROLLUP_AGG)

        fig = build_metric_line_chart(df, metric=metric, agg_level=agg_level)
        st.plotly_chart(fig, width="stretch")


def render_precipitation_section(
    airport_code: str, start_date: date, end_date: date
) -> None:
    """Render the monthly precipitation volume-vs-duration chart and its explainer."""
    monthly_data = fetch_dashboard_data(
        airport_code, start_date, end_date, agg_level=AggLevel.MONTH
    )
    if not monthly_data:
        st.error("No data found!")
    else:
        precipitation_df = clean_metrics(monthly_data, agg_level=AggLevel.MONTH)
        fig = build_precipitation_dual_axis_chart(precipitation_df)
        st.plotly_chart(fig, width="stretch")

    with st.expander(
        "Why do these charts sometimes show different totals?", expanded=True
    ):
        st.markdown("""
        * **Cloud Cover** is calculated as a strict **24-hour mathematical average** of sky coverage.
        * **Weather Conditions (Pie Chart)** reflects the **dominant or highest-impact weather event** recorded that day.

        *Example:* A day that is clear for 20 hours but experiences a sudden 4-hour heavy thunderstorm will be classified as **"Thunderstorm"** in the condition chart, but its average daily cloud cover might only register as **"Mainly Clear"**.
        """)


def render_daily_breakdown_section(
    airport_code: str, start_date: date, end_date: date
) -> None:
    """Render the cloud cover distribution and dominant weather condition charts."""
    daily_data = fetch_dashboard_data(
        airport_code, start_date, end_date, agg_level=AggLevel.DAY
    )
    if not daily_data:
        st.error("No data found!")
        return

    daily_df = clean_metrics(daily_data, agg_level=AggLevel.DAY)
    daily_df = bucket_cloud_cover(daily_df)

    col1, col2 = st.columns(2, gap="small", vertical_alignment="center")
    col1.plotly_chart(build_cloud_cover_bar_chart(daily_df), width="stretch")
    col2.plotly_chart(build_weather_conditions_pie_chart(daily_df), width="stretch")


def main() -> None:
    """Assemble the full dashboard page."""
    filter_options = fetch_filter_options()
    if not filter_options:
        raise ValueError("No filter options found!")

    airport_code, start_date, end_date, available_range_label = render_sidebar_filters(
        filter_options
    )

    st.title(f"{airport_code} Weather Overview")
    st.subheader(available_range_label, divider="blue")

    dashboard_data = fetch_dashboard_data(airport_code, start_date, end_date)
    if not dashboard_data:
        st.error("No data found!")
        return

    render_kpi_section(dashboard_data["kpi_data"])
    st.divider()

    metric = st.selectbox("Metric", options=list(MetricOption))

    tab_names = [level.capitalize() for level in AGG_AXIS_CONFIG]
    tabs = st.tabs(tab_names, on_change="rerun")
    for tab, name in zip(tabs, tab_names):
        if tab.open:
            with tab:
                render_metric_trend_tab(
                    airport_code, start_date, end_date, metric, AggLevel[name.upper()]
                )

    st.divider()
    with st.container():
        render_precipitation_section(airport_code, start_date, end_date)
        render_daily_breakdown_section(airport_code, start_date, end_date)


if __name__ == "__main__":
    main()
