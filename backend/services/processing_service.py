from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import logging
import os
import pandas as pd
from typing import List

from dotenv import load_dotenv
from pandas import DataFrame

from db.db import session_scope
from exceptions import FileProcessingError, FileReadError
from models.constants import (
    COL_MAPPING,
    CONTINUOUS_COLS,
    DATE_COLUMN,
    FLOAT_COLS,
    INT_COLS,
    PERCENT_COLS,
    TEMP_COLS,
    WIND_COLS,
    IngestionStatus,
)
from models.response import IngestedFileResponse
from services import IngestionService
from repository import ProcessFileRepository

load_dotenv()

logger = logging.getLogger(__name__)


class ProcessingService:
    """Orchestrates cleaning and persisting pending ingested weather files."""

    def __init__(
        self,
        ingestion_service: IngestionService,
        process_file_repo: ProcessFileRepository,
    ) -> None:
        """Initialize the service with its ingestion and persistence dependencies.

        Args:
            ingestion_service (IngestionService): Service used to fetch
                pending files and update their status.
            process_file_repo (ProcessFileRepository): Repository used to
                persist cleaned data.

        Returns:
            None.
        """
        self.ingestion_service = ingestion_service
        self.process_file_repo = process_file_repo

    def process_pending_files(self) -> None:
        """Process every currently pending ingested file, in parallel.

        Fetches all pending files, then dispatches each to a worker thread
        (up to 5 concurrent workers) that reads, cleans, and persists it,
        updating its tracked status along the way. Per-file failures are
        logged and do not stop processing of the remaining files.

        Returns:
            None.

        Raises:
            ValueError: If ``DATA_DIR`` is not set in the environment.

        Example:
            >>> service.process_pending_files()
        """
        pending_files: List[IngestedFileResponse] = (
            self.ingestion_service.get_pending_files()
        )
        if not pending_files:
            logger.info("No pending files found to process.")
            return

        DATA_DIR = os.getenv("DATA_DIR")
        if not DATA_DIR:
            raise ValueError(
                "Critical Error: 'DATA_DIR' is missing from the .env file."
            )

        max_workers = 5
        logger.info(f"Starting parallel pipeline for {len(pending_files)} files...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map thread execution to individual files
            future_to_file = {
                executor.submit(self._worker_process_file, file, DATA_DIR): file
                for file in pending_files
            }

            for future in as_completed(future_to_file):
                file_obj = future_to_file[future]
                try:
                    future.result()
                    logger.info(f"Successfully processed: {file_obj.filename}")
                except Exception as e:
                    logger.error(
                        f"Thread worker failed on file {file_obj.filename}: {e}"
                    )

    def _worker_process_file(self, file: IngestedFileResponse, data_dir: str) -> None:
        """Read, clean, and persist a single ingested file, updating its status.
        Args:
            file (IngestedFileResponse): Metadata of the file to process,
                including its ``filename`` and ``id``.
            data_dir (str): Directory containing the raw JSON file, joined
                with ``file.filename`` to locate it.

        Returns:
            None.

        Raises:
            FileReadError: If the raw file is missing, unreadable, or not
                valid JSON.
            FileProcessingError: If cleaning, transformation, or persistence
                of the data fails for any other reason.
        """
        fqn = os.path.join(data_dir, file.filename)
        # Update Status to PROCESSING
        with session_scope() as session:
            self.ingestion_service.update_status(
                session, file.id, IngestionStatus.PROCESSING
            )

        try:
            with open(fqn, "r") as f:
                data = json.load(f)
        except (
            FileNotFoundError,
            PermissionError,
            IsADirectoryError,
            OSError,
            json.JSONDecodeError,
        ) as e:
            logger.warning(f"File I/O or parsing error on {file.filename}: {e}")
            with session_scope() as session:
                self.ingestion_service.update_status(
                    session, file.id, IngestionStatus.FAILED
                )
            raise FileReadError(f"Error while reading raw json file: {file.filename}")

        try:
            df_flat = pd.json_normalize(data)

            # Explode daily params
            daily_cols = [col for col in df_flat.columns if col.startswith("daily.")]
            df = df_flat.explode(daily_cols).reset_index(drop=True)

            # Type casting
            df[FLOAT_COLS] = df[FLOAT_COLS].astype(float)
            df[INT_COLS] = df[INT_COLS].astype(int)
            df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])

            # Rename columns
            df = df.rename(columns=COL_MAPPING)

            imputed_df = df
            # Impute any missing data
            if any(df.isna().sum() > 0):
                imputed_df = type(self)._impute_metrics(df)

            # Clip to fit valid range values
            imputed_df[TEMP_COLS] = imputed_df[TEMP_COLS].clip(
                lower=-273.15, upper=1.42e32
            )
            LOWER_ZERO_COLS = WIND_COLS + [
                "precipitation_sum_mm",
                "daylight_duration_sec",
            ]
            imputed_df[LOWER_ZERO_COLS] = imputed_df[LOWER_ZERO_COLS].clip(lower=0)
            imputed_df["precipitation_hours"] = imputed_df["precipitation_hours"].clip(
                lower=0, upper=24
            )
            imputed_df["precipitation_sum_mm"] = imputed_df[
                "precipitation_sum_mm"
            ].clip(lower=0)
            imputed_df[PERCENT_COLS] = imputed_df[PERCENT_COLS].clip(lower=0, upper=100)

            # New columns
            # Adjusted timestamp with timezone information
            imputed_df["epoch_timestamp"] = [
                int(dt.tz_localize(tz).timestamp())
                for dt, tz in zip(imputed_df["weather_date"], imputed_df["timezone"])
            ]
            imputed_df["day_of_month"] = imputed_df["weather_date"].dt.day
            imputed_df["day_of_week_int"] = (
                imputed_df["weather_date"].dt.day_of_week + 1
            )
            imputed_df["day_of_week_name"] = imputed_df["weather_date"].dt.day_name()
            imputed_df["day_of_year"] = imputed_df["weather_date"].dt.day_of_year
            imputed_df["week_of_year"] = (
                imputed_df["weather_date"].dt.isocalendar().week
            )
            imputed_df["month_int"] = imputed_df["weather_date"].dt.month
            imputed_df["month_name"] = imputed_df["weather_date"].dt.month_name()
            imputed_df["quarter"] = imputed_df["weather_date"].dt.quarter
            imputed_df["year_int"] = imputed_df["weather_date"].dt.year

            # Drop columns
            daily_unit_cols = [
                col for col in imputed_df.columns if col.startswith("daily_units.")
            ]
            columns_to_drop = [
                "generationtime_ms",
                "utc_offset_seconds",
                "timezone",
                "timezone_abbreviation",
                "elevation",
                *daily_unit_cols,
            ]
            imputed_df = imputed_df.drop(columns=columns_to_drop, errors="ignore")

            # Save cleaned data
            with session_scope() as session:
                # Duplicate rows are upserted
                self.process_file_repo.save_cleaned_data(session, imputed_df)
                self.ingestion_service.update_status(
                    session, file.id, IngestionStatus.COMPLETED
                )
        except Exception as e:
            logger.error(f"Failed pipeline processing sequence on {file.filename}: {e}")
            with session_scope() as session:
                self.ingestion_service.update_status(
                    session, file.id, IngestionStatus.FAILED
                )
            raise FileProcessingError(
                f"Processing failed for file layout: {file.filename}"
            )

    @staticmethod
    def _impute_metrics(orig_df: DataFrame) -> DataFrame:
        """Impute missing weather metric values

        Args:
            orig_df (DataFrame): Weather data that may contain missing values

        Returns:
            DataFrame: Copy of ``orig_df`` with missing values in those
            columns filled.

        Example:
            >>> filled_df = ProcessingService._impute_metrics(df)
        """
        df = orig_df.copy()
        # Imputing random missing observations
        # We limit to 2 consecutive days so we don't accidentally fill massive gaps linearly
        df[CONTINUOUS_COLS] = df[CONTINUOUS_COLS].interpolate(method="linear", limit=2)

        # Forward Fill (Best for episodic/accumulative data like rain)
        df["precipitation_hours"] = df["precipitation_hours"].fillna(0)
        df["precipitation_sum_mm"] = df["precipitation_sum_mm"].fillna(0)

        # Imputing consecutive missing data
        df = df.sort_values("weather_date").reset_index(drop=True)
        # Impute with the average over a 14 day rolling window
        rolling_normals = (
            df[CONTINUOUS_COLS].rolling(window=14, center=True, min_periods=1).mean()
        )
        # Hybrid fill if missing value window > 14 days
        rolling_normals = rolling_normals.ffill().bfill()
        df[CONTINUOUS_COLS] = df[CONTINUOUS_COLS].fillna(rolling_normals)

        # Hybrid fill for rainfall, because it is an episodic event
        # Forward fill known value and backward fill 0 to create variance
        df["precipitation_hours"] = (
            df["precipitation_hours"].ffill(limit=7).bfill(limit=7).fillna(0)
        )
        df["precipitation_sum_mm"] = (
            df["precipitation_sum_mm"].ffill(limit=7).bfill(limit=7).fillna(0)
        )

        # Daylight duration follows a sine curve, so interpolation works best
        df["daylight_duration_sec"] = (
            df["daylight_duration_sec"].interpolate(method="linear").ffill().bfill()
        )

        return df
