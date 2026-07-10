# Weather Analytics Dashboard

## 1. Project Description

This is an interactive tool for exploring historical weather trends across three major U.S. airports — San Francisco (SFO), Los Angeles (LAX), and Las Vegas (LAS) — from 2023 through 2025. Users pick an airport and a date range, then explore temperature, wind, precipitation, humidity, cloud cover, and dominant weather conditions at daily, weekly, monthly, or yearly granularity. The dashboard surfaces headline KPIs (record highs/lows, total precipitation, wind extremes) alongside trend charts, precipitation breakdowns, and a weather-conditions summary.

## 2. Tools Used

| Tool / Library                        | Purpose                                                                              |
| ------------------------------------- | ------------------------------------------------------------------------------------ |
| **Python 3.11+**                      | Core language for backend and frontend                                               |
| **FastAPI**                           | REST API framework serving ingestion, pipeline, and dashboard endpoints              |
| **Uvicorn**                           | ASGI server for running the FastAPI app                                              |
| **Streamlit**                         | Interactive frontend dashboard UI                                                    |
| **Plotly**                            | Charting library for trend lines, dual-axis, bar, and pie charts in the dashboard    |
| **PostgreSQL**                        | Relational database storing cleaned weather data and reference tables                |
| **SQLAlchemy**                        | ORM for defining tables/models and querying the database                             |
| **Alembic**                           | Database schema migrations, including seed data for locations and weather codes      |
| **pandas**                            | Data cleaning, imputation, type casting, and time-based feature engineering          |
| **Requests + urllib3 Retry**          | HTTP client for calling the Open-Meteo API with automatic retry/backoff              |
| **python-dotenv**                     | Loading configuration (API URLs, DB credentials, data directories) from `.env` files |
| **Docker Compose**                    | Running the PostgreSQL database as a containerized service                           |
| **Open-Meteo Historical Weather API** | External data source for daily weather/climate observations                          |
| **uv**                                | Python dependency and virtual environment management (`pyproject.toml` / `uv.lock`)  |

## 3. Architecture Description
![System Design](https://raw.githubusercontent.com/madhu-1999/weather-analytics-dashboard/main/system-overview.drawio.png)

Ingestion — For each configured airport (location), the backend calls the Open-Meteo API for a given date range, writes the raw JSON response to a local data directory, and inserts a tracking record (ingested_files) with status PENDING.

Processing — A worker pool picks up PENDING files, flattens and explodes the nested daily JSON arrays into a tabular pandas DataFrame, casts types, imputes missing values, clips out-of-range readings, engineers date-dimension fields (day of week, week/month/quarter/year, etc.), and upserts the result/ignores the data, depending on the table into PostgreSQL. File status transitions through PENDING → PROCESSING → COMPLETED/FAILED, so a failed file can be identified and retried without reprocessing everything.

Storage — Cleaned data lands in a small relational schema: a locations reference table, a weather_codes lookup, a date_dimension table of calendar attributes, and a central daily_weather_metrics fact table keyed by airport and date. An ingested_files table tracks pipeline state for observability.

Presentation — The FastAPI backend exposes read-only dashboard endpoints (filter options, aggregated KPI and metric data) that the Streamlit frontend calls through a thin, cached API client. The frontend performs light client-side reshaping (bucketing, yearly roll-ups) before rendering KPI cards and Plotly charts

## 5. SQL Tables ERD
![ERD](https://raw.githubusercontent.com/madhu-1999/weather-analytics-dashboard/main/erd.png)

## 6. Setup and Run Instructions

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for dependency management (each of `backend/` and `frontend/` has its own `pyproject.toml` / `uv.lock`)
- Docker (for running PostgreSQL via `compose.yaml`), or a local PostgreSQL 16+ instance

### 1. Clone the repo

```bash
git clone https://github.com/madhu-1999/weather-analytics-dashboard.git
cd weather-analytics-dashboard
```

### 2. Start the database

From `backend/`, create a `.env` file (used by both `compose.yaml` and the app) with at least:

```env
DB_USER=weather_user
DB_PASSWORD=weather_pass
DB_NAME=weather_db
```

Then start Postgres in Docker:

```bash
cd backend
docker compose up -d
```

This starts a `postgres:18-alpine` container named `weather_db`, exposed on host port **5434** (mapped to container port 5432).

### 3. Configure the backend

Add the remaining variables to `backend/.env`:

```env
# Database connection used by SQLAlchemy/Alembic
DB_URL=postgresql+psycopg2://weather_user:weather_pass@localhost:5434/weather_db

# Open-Meteo historical weather API
API_BASE_URL=https://archive-api.open-meteo.com/v1/archive
DAILY_PARAMS=temperature_2m_mean,temperature_2m_max,temperature_2m_min,dew_point_2m_mean,wind_speed_10m_mean,wind_speed_10m_max,wind_speed_10m_min,wind_gusts_10m_mean,wind_gusts_10m_max,wind_gusts_10m_min,precipitation_sum,precipitation_hours,cloud_cover_mean,relative_humidity_2m_mean,daylight_duration,weather_code

# Local storage for raw ingested JSON files (must exist on disk)
DATA_DIR=./data

# Directory for application log files (must exist on disk)
LOG_DIR=./logs
```

Install dependencies and apply database migrations (creates all tables, seed data, and materialized views):

```bash
uv sync
mkdir -p data logs
uv run alembic upgrade head
```

### 4. Run the backend API

```bash
uv run main.py
# or, equivalently:
uv run uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

The API will be available at `http://127.0.0.1:8001`, with interactive docs at `http://127.0.0.1:8001/docs`.

### 5. Ingest and process weather data

With the backend running, trigger ingestion and processing for the seeded airports (SFO, LAX, LAS) over your desired date range via the pipeline endpoints:

```bash
# Fetch raw data from Open-Meteo for each known location and stage it (status PENDING)
curl -X POST "http://127.0.0.1:8001/pipeline/ingest?start_date=2023-01-01&end_date=2025-12-31"

# Clean, transform, and load staged files into the database (status COMPLETED)
curl -X POST "http://127.0.0.1:8001/pipeline/process"
```

After processing, refresh the materialized views so weekly/monthly charts reflect the new data:

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_weekly_weather;
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_weather;
```

### 6. Configure and run the frontend

In a new terminal, from `frontend/`, create a `frontend/.env` file:

```env
BACKEND_BASE_URL=http://127.0.0.1:8001
```

Install dependencies and launch the Streamlit app:

```bash
cd frontend
uv sync
uv run streamlit run app.py
```

Streamlit will open the dashboard in your browser (default `http://localhost:8501`), where you can select an airport and date range and view KPI cards and charts.

### Notes

- Backend and frontend are independent `uv` projects; run `uv sync` separately in each directory.
- The backend must be running and reachable at `BACKEND_BASE_URL` before starting the frontend.
- Re-run the ingest/process steps whenever you want to load additional date ranges.
