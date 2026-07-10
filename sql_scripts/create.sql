-- ============================================================================
-- Weather Analytics Dashboard — Schema Creation Script
-- Target: PostgreSQL
--
-- Consolidates all tables, constraints, indexes, seed/reference data, and
-- materialized views defined in the backend/db folder (Alembic migrations
-- + SQLAlchemy table/view models) into a single, ordered script.
--
-- Run this against an empty database, e.g.:
--   psql -h localhost -p 5434 -U <user> -d <db> -f create_weather_db.sql
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Enum types
-- ----------------------------------------------------------------------------

CREATE TYPE ingestionstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');

-- ----------------------------------------------------------------------------
-- Table: locations
-- Reference table of airport/city locations tracked by the pipeline.
-- ----------------------------------------------------------------------------

CREATE TABLE locations (
    airport_code VARCHAR(10)    NOT NULL,
    city         VARCHAR(100)   NOT NULL,
    state        VARCHAR(2)     NOT NULL,
    latitude     NUMERIC(9, 6)  NOT NULL,
    longitude    NUMERIC(9, 6)  NOT NULL,
    timezone     VARCHAR(100)   NOT NULL,
    CONSTRAINT locations_pkey PRIMARY KEY (airport_code)
);

-- ----------------------------------------------------------------------------
-- Table: weather_codes
-- Lookup table mapping WMO weather codes to human-readable descriptions.
-- ----------------------------------------------------------------------------

CREATE TABLE weather_codes (
    weather_code        INTEGER      NOT NULL,
    weather_description  VARCHAR(100) NOT NULL,
    CONSTRAINT weather_codes_pkey PRIMARY KEY (weather_code)
);

-- ----------------------------------------------------------------------------
-- Table: ingested_files
-- Tracks raw files fetched from the source API and their pipeline status.
-- ----------------------------------------------------------------------------

CREATE TABLE ingested_files (
    id            SERIAL       NOT NULL,
    filename      VARCHAR(255) NOT NULL,
    airport_code  VARCHAR(10)  NOT NULL,
    start_date    DATE         NOT NULL,
    end_date      DATE         NOT NULL,
    status        ingestionstatus NOT NULL DEFAULT 'PENDING',
    created_at    TIMESTAMP    NOT NULL DEFAULT now(),
    processed_at  TIMESTAMP    NULL,
    CONSTRAINT ingested_files_pkey PRIMARY KEY (id),
    CONSTRAINT ingested_files_airport_code_fkey FOREIGN KEY (airport_code)
        REFERENCES locations (airport_code)
);

-- Index history: an initial (airport_code, status) composite index and a
-- standalone airport_code index were created, then replaced with a
-- standalone status index (final state reflected below).
CREATE INDEX ix_ingested_files_status ON ingested_files (status);

-- ----------------------------------------------------------------------------
-- Table: date_dimension
-- Calendar dimension table with one row per calendar date.
-- ----------------------------------------------------------------------------

CREATE TABLE date_dimension (
    weather_date      DATE    NOT NULL,
    epoch_timestamp   BIGINT  NOT NULL,
    day_of_month      INTEGER NOT NULL,
    day_of_week_int   INTEGER NOT NULL, -- 1 (Monday) to 7 (Sunday)
    day_of_week_name  VARCHAR(9) NOT NULL, -- 'Monday', 'Tuesday'
    day_of_year       INTEGER NOT NULL, -- 1 to 366
    week_of_year      INTEGER NOT NULL, -- 1 to 53
    month_int         INTEGER NOT NULL, -- 1 to 12
    month_name        VARCHAR(9) NOT NULL, -- 'January', 'February'
    quarter           INTEGER NOT NULL, -- 1 to 4
    year_int          INTEGER NOT NULL,
    CONSTRAINT date_dimension_pkey PRIMARY KEY (weather_date)
);

COMMENT ON COLUMN date_dimension.day_of_week_int IS '1 (Monday) to 7 (Sunday)';
COMMENT ON COLUMN date_dimension.day_of_week_name IS '''Monday'', ''Tuesday''';
COMMENT ON COLUMN date_dimension.day_of_year IS '1 to 366';
COMMENT ON COLUMN date_dimension.week_of_year IS '1 to 53';
COMMENT ON COLUMN date_dimension.month_int IS '1 to 12';
COMMENT ON COLUMN date_dimension.month_name IS '''January'', ''February''';
COMMENT ON COLUMN date_dimension.quarter IS '1 to 4';

-- ----------------------------------------------------------------------------
-- Table: daily_weather_metrics
-- Central fact table: one row per airport per date, with cleaned weather
-- metrics. Composite primary key (airport_code, weather_date).
-- ----------------------------------------------------------------------------

CREATE TABLE daily_weather_metrics (
    airport_code                         VARCHAR(10)   NOT NULL,
    weather_date                         DATE          NOT NULL,
    weather_code                         INTEGER       NOT NULL,

    temperature_2m_mean_celsius          NUMERIC(4, 1),
    temperature_2m_max_celsius           NUMERIC(4, 1),
    temperature_2m_min_celsius           NUMERIC(4, 1),
    dew_point_2m_mean_celsius            NUMERIC(4, 1),

    wind_speed_10m_mean_kmh              NUMERIC(5, 2),
    wind_speed_10m_max_kmh               NUMERIC(5, 2),
    wind_speed_10m_min_kmh               NUMERIC(5, 2),
    wind_gusts_10m_mean_kmh              NUMERIC(5, 2),
    wind_gusts_10m_max_kmh               NUMERIC(5, 2),
    wind_gusts_10m_min_kmh               NUMERIC(5, 2),

    precipitation_sum_mm                 NUMERIC(6, 2),
    precipitation_hours                  NUMERIC(4, 1),
    cloud_cover_mean_percent             INTEGER,
    relative_humidity_2m_mean_percent    INTEGER,
    daylight_duration_sec                INTEGER,

    created_at                           TIMESTAMP NOT NULL DEFAULT now(),
    updated_at                           TIMESTAMP NULL,

    CONSTRAINT daily_weather_metrics_pkey PRIMARY KEY (airport_code, weather_date),
    CONSTRAINT locations_airport_code_fkey FOREIGN KEY (airport_code)
        REFERENCES locations (airport_code) ON DELETE CASCADE,
    CONSTRAINT weather_codes_weather_code_fkey FOREIGN KEY (weather_code)
        REFERENCES weather_codes (weather_code),
    CONSTRAINT date_dim_weather_date_fkey FOREIGN KEY (weather_date)
        REFERENCES date_dimension (weather_date)
);

CREATE INDEX idx_weather_date ON daily_weather_metrics (weather_date);

-- ----------------------------------------------------------------------------
-- Seed data: locations
-- ----------------------------------------------------------------------------

INSERT INTO locations (airport_code, city, state, latitude, longitude, timezone) VALUES
    ('LAX', 'Los Angeles',   'CA', 33.942791, -118.410042, 'America/Los_Angeles'),
    ('SFO', 'San Francisco', 'CA', 37.615223, -122.389977, 'America/Los_Angeles'),
    ('LAS', 'Las Vegas',     'NV', 36.086010, -115.153969, 'America/Los_Angeles');

-- ----------------------------------------------------------------------------
-- Seed data: weather_codes (WMO weather interpretation codes)
-- ----------------------------------------------------------------------------

INSERT INTO weather_codes (weather_code, weather_description) VALUES
    (0,  'Clear sky'),
    (1,  'Mainly clear'),
    (2,  'Partly cloudy'),
    (3,  'Overcast'),
    (45, 'Fog'),
    (48, 'Depositing rime fog'),
    (51, 'Drizzle: Light intensity'),
    (53, 'Drizzle: Moderate intensity'),
    (55, 'Drizzle: Dense intensity'),
    (56, 'Freezing Drizzle: Light intensity'),
    (57, 'Freezing Drizzle: Dense intensity'),
    (61, 'Rain: Slight intensity'),
    (63, 'Rain: Moderate intensity'),
    (65, 'Rain: Heavy intensity'),
    (66, 'Freezing Rain: Light intensity'),
    (67, 'Freezing Rain: Heavy intensity'),
    (71, 'Snow fall: Slight intensity'),
    (73, 'Snow fall: Moderate intensity'),
    (75, 'Snow fall: Heavy intensity'),
    (77, 'Snow grains'),
    (80, 'Rain showers: Slight'),
    (81, 'Rain showers: Moderate'),
    (82, 'Rain showers: Violent'),
    (85, 'Snow showers: Slight'),
    (86, 'Snow showers: Heavy'),
    (95, 'Thunderstorm: Slight or moderate'),
    (96, 'Thunderstorm with slight hail'),
    (99, 'Thunderstorm with heavy hail');

-- ----------------------------------------------------------------------------
-- Materialized view: mv_weekly_weather
-- Weekly aggregated metrics per airport.
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW mv_weekly_weather AS
SELECT
    dw.airport_code,
    d.year_int,
    d.week_of_year,
    ROUND(AVG(dw.temperature_2m_mean_celsius), 2) AS temp_mean,
    ROUND(AVG(dw.temperature_2m_max_celsius), 2)  AS temp_max,
    ROUND(AVG(dw.temperature_2m_min_celsius), 2)  AS temp_min,

    ROUND(AVG(dw.wind_speed_10m_mean_kmh), 2)     AS wind_speed_mean,
    ROUND(AVG(dw.wind_speed_10m_max_kmh), 2)      AS wind_speed_max,
    ROUND(AVG(dw.wind_speed_10m_min_kmh), 2)      AS wind_speed_min,

    ROUND(AVG(dw.wind_gusts_10m_mean_kmh), 2)     AS wind_gusts_mean,
    ROUND(AVG(dw.wind_gusts_10m_max_kmh), 2)      AS wind_gusts_max,
    ROUND(AVG(dw.wind_gusts_10m_min_kmh), 2)      AS wind_gusts_min,

    ROUND(SUM(dw.precipitation_sum_mm), 2)        AS precipitation_sum,
    SUM(dw.precipitation_hours)                   AS precipitation_hours
FROM daily_weather_metrics dw
JOIN date_dimension d ON dw.weather_date = d.weather_date
GROUP BY dw.airport_code, d.year_int, d.week_of_year;

CREATE UNIQUE INDEX idx_mv_weekly ON mv_weekly_weather (airport_code, year_int, week_of_year);

-- ----------------------------------------------------------------------------
-- Materialized view: mv_monthly_weather
-- Monthly aggregated metrics per airport.
-- ----------------------------------------------------------------------------

CREATE MATERIALIZED VIEW mv_monthly_weather AS
SELECT
    dw.airport_code,
    d.year_int,
    d.month_int,
    ROUND(AVG(dw.temperature_2m_mean_celsius), 2) AS temp_mean,
    ROUND(AVG(dw.temperature_2m_max_celsius), 2)  AS temp_max,
    ROUND(AVG(dw.temperature_2m_min_celsius), 2)  AS temp_min,

    ROUND(AVG(dw.wind_speed_10m_mean_kmh), 2)     AS wind_speed_mean,
    ROUND(AVG(dw.wind_speed_10m_max_kmh), 2)      AS wind_speed_max,
    ROUND(AVG(dw.wind_speed_10m_min_kmh), 2)      AS wind_speed_min,

    ROUND(AVG(dw.wind_gusts_10m_mean_kmh), 2)     AS wind_gusts_mean,
    ROUND(AVG(dw.wind_gusts_10m_max_kmh), 2)      AS wind_gusts_max,
    ROUND(AVG(dw.wind_gusts_10m_min_kmh), 2)      AS wind_gusts_min,

    ROUND(SUM(dw.precipitation_sum_mm), 2)        AS precipitation_sum,
    SUM(dw.precipitation_hours)                   AS precipitation_hours
FROM daily_weather_metrics dw
JOIN date_dimension d ON dw.weather_date = d.weather_date
GROUP BY dw.airport_code, d.year_int, d.month_int;

CREATE UNIQUE INDEX idx_mv_monthly ON mv_monthly_weather (airport_code, year_int, month_int);

COMMIT;