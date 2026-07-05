from enum import StrEnum


class IngestionStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


FLOAT_COLS = [
    "daily.wind_gusts_10m_mean",
    "daily.wind_speed_10m_mean",
    "daily.temperature_2m_mean",
    "daily.temperature_2m_max",
    "daily.temperature_2m_min",
    "daily.precipitation_hours",
    "daily.precipitation_sum",
    "daily.wind_gusts_10m_max",
    "daily.wind_speed_10m_max",
    "daily.wind_gusts_10m_min",
    "daily.wind_speed_10m_min",
    "daily.dew_point_2m_mean",
]

INT_COLS = [
    "daily.weather_code",
    "daily.cloud_cover_mean",
    "daily.relative_humidity_2m_mean",
    "daily.daylight_duration",
]

COL_MAPPING = {
    "daily.time": "weather_date",
    "daily.wind_gusts_10m_mean": "wind_gusts_10m_mean_kmh",
    "daily.wind_speed_10m_mean": "wind_speed_10m_mean_kmh",
    "daily.temperature_2m_mean": "temperature_2m_mean_celsius",
    "daily.temperature_2m_max": "temperature_2m_max_celsius",
    "daily.temperature_2m_min": "temperature_2m_min_celsius",
    "daily.precipitation_hours": "precipitation_hours",
    "daily.precipitation_sum": "precipitation_sum_mm",
    "daily.wind_gusts_10m_max": "wind_gusts_10m_max_kmh",
    "daily.wind_speed_10m_max": "wind_speed_10m_max_kmh",
    "daily.cloud_cover_mean": "cloud_cover_mean_percent",
    "daily.relative_humidity_2m_mean": "relative_humidity_2m_mean_percent",
    "daily.wind_gusts_10m_min": "wind_gusts_10m_min_kmh",
    "daily.wind_speed_10m_min": "wind_speed_10m_min_kmh",
    "daily.dew_point_2m_mean": "dew_point_2m_mean_celsius",
    "daily.daylight_duration": "daylight_duration_sec",
    "daily.weather_code": "weather_code",
}

TEMP_COLS = [
    "temperature_2m_mean_celsius",
    "temperature_2m_max_celsius",
    "temperature_2m_min_celsius",
    "dew_point_2m_mean_celsius",
]

WIND_COLS = [
    "wind_gusts_10m_mean_kmh",
    "wind_speed_10m_mean_kmh",
    "wind_gusts_10m_max_kmh",
    "wind_speed_10m_max_kmh",
    "wind_gusts_10m_min_kmh",
    "wind_speed_10m_min_kmh",
]

PERCENT_COLS = ["cloud_cover_mean_percent", "relative_humidity_2m_mean_percent"]

DATE_COLUMN = "daily.time"

CONTINUOUS_COLS = [
    "wind_gusts_10m_mean_kmh",
    "wind_speed_10m_mean_kmh",
    "temperature_2m_mean_celsius",
    "temperature_2m_max_celsius",
    "temperature_2m_min_celsius",
    "wind_gusts_10m_max_kmh",
    "wind_speed_10m_max_kmh",
    "wind_gusts_10m_min_kmh",
    "wind_speed_10m_min_kmh",
    "cloud_cover_mean_percent",
    "relative_humidity_2m_mean_percent",
    "dew_point_2m_mean_celsius",
    "daylight_duration_sec",
]

DATE_DIM_COLS = [
    "weather_date",
    "epoch_timestamp",
    "day_of_month",
    "day_of_week_int",
    "day_of_week_name",
    "day_of_year",
    "week_of_year",
    "month_int",
    "month_name",
    "quarter",
    "year_int",
]

WEATHER_METRICS_COLS = [
    "airport_code",
    "weather_code",
    "weather_date",
    *TEMP_COLS,
    *WIND_COLS,
    *PERCENT_COLS,
    "precipitation_hours",
    "precipitation_sum_mm",
    "daylight_duration_sec",
]
