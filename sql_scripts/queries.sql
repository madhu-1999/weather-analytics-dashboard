-- ============================================================================
-- Weather Analytics Dashboard — Dashboard SELECT Queries
-- Target: PostgreSQL
--
-- This script consolidates every SELECT query issued by the dashboard/API
-- layer (backend/repository/*.py) that powers the Streamlit dashboard:
-- filter options (locations + available date range), KPI summary cards,
-- and the daily / weekly / monthly time-series charts.
--
-- Placeholders to substitute before running:
--   :airport_code   e.g. 'SFO'
--   :start_date     e.g. '2023-01-01'
--   :end_date       e.g. '2023-12-31'
--
-- These are read-only queries; no schema changes are made by this script.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- 1. Filter options — Locations
-- Source: repository/location_repo.py -> LocationRepository.get_locations()
-- Used to populate the airport/location dropdown in the sidebar.
-- ----------------------------------------------------------------------------

SELECT
    airport_code,
    city,
    state,
    latitude,
    longitude,
    timezone
FROM locations;


-- ----------------------------------------------------------------------------
-- 2. Filter options — Available date range
-- Source: repository/date_repo.py -> DateRepository.get_available_date_range()
-- Returns the date-dimension rows for the earliest and latest dates that
-- have weather data available, used to bound the sidebar date pickers.
-- ----------------------------------------------------------------------------

SELECT
    weather_date,
    day_of_month,
    month_name,
    year_int
FROM date_dimension
WHERE weather_date IN (
    (SELECT MIN(weather_date) FROM date_dimension),
    (SELECT MAX(weather_date) FROM date_dimension)
);


-- ----------------------------------------------------------------------------
-- 3. KPI summary cards
-- Source: repository/metrics_repo.py -> MetricsRepository.get_kpi_metrics()
-- Headline KPIs for a chosen airport + date range: temperature extremes,
-- number of days with precipitation, total precipitation, and wind extremes.
-- ----------------------------------------------------------------------------

SELECT
    MAX(temperature_2m_max_celsius) AS max_temp,
    MIN(temperature_2m_min_celsius) AS min_temp,
    COUNT(CASE WHEN precipitation_hours > 0 THEN 1 ELSE NULL END) AS precipitation_days_sum,
    SUM(precipitation_sum_mm) AS total_precipitation,
    MAX(wind_speed_10m_max_kmh) AS max_wind_speed,
    MIN(wind_speed_10m_min_kmh) AS min_wind_speed
FROM daily_weather_metrics
WHERE weather_date BETWEEN :start_date AND :end_date
  AND airport_code = :airport_code;


-- ----------------------------------------------------------------------------
-- 4. Daily metrics time series (agg_level = DAY)
-- Source: repository/metrics_repo.py -> MetricsRepository.get_daily_metrics()
-- Raw daily weather metrics joined with the weather-code description, used
-- for the daily-granularity trend chart, precipitation chart, cloud cover
-- breakdown, and weather-conditions pie chart.
-- ----------------------------------------------------------------------------

SELECT
    dwm.weather_date,
    dwm.temperature_2m_mean_celsius   AS temp_mean,
    dwm.temperature_2m_max_celsius    AS temp_max,
    dwm.temperature_2m_min_celsius    AS temp_min,
    dwm.wind_speed_10m_mean_kmh       AS wind_speed_mean,
    dwm.wind_speed_10m_max_kmh        AS wind_speed_max,
    dwm.wind_speed_10m_min_kmh        AS wind_speed_min,
    dwm.wind_gusts_10m_mean_kmh       AS wind_gusts_mean,
    dwm.wind_gusts_10m_max_kmh        AS wind_gusts_max,
    dwm.wind_gusts_10m_min_kmh        AS wind_gusts_min,
    dwm.precipitation_sum_mm          AS precipitation_sum,
    dwm.precipitation_hours,
    dwm.cloud_cover_mean_percent      AS cloud_cover_mean,
    wc.weather_code,
    wc.weather_description            AS weather_code_mapping
FROM daily_weather_metrics dwm
JOIN weather_codes wc ON dwm.weather_code = wc.weather_code
WHERE dwm.airport_code = :airport_code
  AND dwm.weather_date BETWEEN :start_date AND :end_date;


-- ----------------------------------------------------------------------------
-- 5. Weekly metrics time series (agg_level = WEEK)
-- Source: repository/metrics_repo.py -> MetricsRepository.get_weekly_metrics()
-- Pulls pre-aggregated rows from the mv_weekly_weather materialized view for
-- the ISO (year, week) periods spanned by start_date/end_date.
-- ----------------------------------------------------------------------------

SELECT
    year_int,
    week_of_year,
    temp_mean,
    temp_max,
    temp_min,
    wind_speed_mean,
    wind_speed_max,
    wind_speed_min,
    wind_gusts_mean,
    wind_gusts_max,
    wind_gusts_min,
    precipitation_sum,
    precipitation_hours
FROM mv_weekly_weather
WHERE airport_code = :airport_code
  AND (year_int, week_of_year) >= (
        SELECT EXTRACT(ISOYEAR FROM weather_date)::int, EXTRACT(WEEK FROM weather_date)::int
        FROM date_dimension
        WHERE weather_date = :start_date
      )
  AND (year_int, week_of_year) <= (
        SELECT EXTRACT(ISOYEAR FROM weather_date)::int, EXTRACT(WEEK FROM weather_date)::int
        FROM date_dimension
        WHERE weather_date = :end_date
      )
ORDER BY year_int ASC, week_of_year ASC;


-- ----------------------------------------------------------------------------
-- 6. Monthly metrics time series (agg_level = MONTH / YEAR — default)
-- Source: repository/metrics_repo.py -> MetricsRepository.get_monthly_metrics()
-- Pulls pre-aggregated rows from the mv_monthly_weather materialized view
-- for the (year, month) periods spanned by start_date/end_date. The
-- frontend further rolls this up to yearly granularity when needed.
-- ----------------------------------------------------------------------------

SELECT
    year_int,
    month_int,
    temp_mean,
    temp_max,
    temp_min,
    wind_speed_mean,
    wind_speed_max,
    wind_speed_min,
    wind_gusts_mean,
    wind_gusts_max,
    wind_gusts_min,
    precipitation_sum,
    precipitation_hours
FROM mv_monthly_weather
WHERE airport_code = :airport_code
  AND (year_int, month_int) >= (
        SELECT year_int, month_int
        FROM date_dimension
        WHERE weather_date = :start_date
      )
  AND (year_int, month_int) <= (
        SELECT year_int, month_int
        FROM date_dimension
        WHERE weather_date = :end_date
      )
ORDER BY year_int ASC, month_int ASC;