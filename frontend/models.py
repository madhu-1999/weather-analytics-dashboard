from enum import StrEnum


class AggLevel(StrEnum):
    """Granularity at which daily weather records can be aggregated."""

    YEAR = "year"
    MONTH = "month"
    WEEK = "week"
    DAY = "day"


class MetricOption(StrEnum):
    """User-facing metric families offered in the trend line chart."""

    TEMPERATURE = "Temperature"
    WIND_SPEED = "Wind Speed"
    WIND_GUST = "Wind Gust Speed"
    PRECIPITATION = "Precipitation"


# Key holding each aggregation level's records in the dashboard API response.
# Note "year" reuses the monthly payload: yearly figures are derived by
# rolling monthly rows up client-side rather than via a dedicated endpoint.
RESPONSE_KEY_BY_AGG_LEVEL = {
    AggLevel.YEAR: "monthly_metrics",
    AggLevel.MONTH: "monthly_metrics",
    AggLevel.WEEK: "weekly_metrics",
    AggLevel.DAY: "daily_metrics",
}

# Raw numeric columns present in every metrics record, regardless of agg level.
WEATHER_METRIC_COLUMNS = [
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

# How to collapse monthly rows into yearly rows for the "year" chart view.
YEARLY_ROLLUP_AGG = {
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

# Chart x-axis column and display label for each aggregation level.
AGG_AXIS_CONFIG = {
    AggLevel.YEAR: {"x_axis": "year_int", "x_label": "Year"},
    AggLevel.MONTH: {"x_axis": "month_str", "x_label": "Month"},
    AggLevel.WEEK: {"x_axis": "week_str", "x_label": "Week"},
    AggLevel.DAY: {"x_axis": "weather_date", "x_label": "Day"},
}

# Which columns to plot, and axis labels, for each selectable metric.
METRIC_CHART_CONFIG = {
    MetricOption.TEMPERATURE: {
        "y_fields": ["temp_mean", "temp_max", "temp_min"],
        "title": "Temperature trends over time",
        "y_label": "Temperature (°C)",
    },
    MetricOption.WIND_SPEED: {
        "y_fields": ["wind_speed_mean", "wind_speed_max", "wind_speed_min"],
        "title": "Wind Speed trends over time",
        "y_label": "Wind Speed (km/h)",
    },
    MetricOption.WIND_GUST: {
        "y_fields": ["wind_gusts_mean", "wind_gusts_max", "wind_gusts_min"],
        "title": "Wind Gust trends over time",
        "y_label": "Wind Gust (km/h)",
    },
    MetricOption.PRECIPITATION: {
        "y_fields": ["precipitation_sum"],
        "title": "Precipitation over time",
        "y_label": "Precipitation (mm)",
    },
}

# Bucketing rules for classifying a day's average cloud cover percentage
# into a human-readable sky condition.
CLOUD_COVER_BINS = [-0.1, 0.0, 25.0, 75.0, 100.0]
CLOUD_COVER_LABELS = ["Clear sky", "Mainly clear", "Partly cloudy", "Overcast"]

CLOUD_COVER_COLORS = {
    "Clear sky": "#FFD700",
    "Mainly clear": "#90EE90",
    "Partly cloudy": "#ADD8E6",
    "Overcast": "#808080",
}

CLOUD_COVER_LEGEND_LABELS = {
    "Clear sky": "Clear sky (0%)",
    "Mainly clear": "Mainly clear (1% - 25%)",
    "Partly cloudy": "Partly cloudy (26% - 75%)",
    "Overcast": "Overcast (76% - 100%)",
}
