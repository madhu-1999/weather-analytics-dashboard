from datetime import datetime
from typing import Any, Hashable, List

from pandas import DataFrame
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.tables.weather_tables import DailyWeatherMetricsDB, DateDimDB
from exceptions import DatabaseError
from models.constants import DATE_DIM_COLS, WEATHER_METRICS_COLS


class ProcessFileRepository:
    """Data-access layer for persisting cleaned weather data."""

    def __init__(self) -> None:
        pass

    def save_cleaned_data(self, session: Session, df: DataFrame) -> None:
        """Persist cleaned weather data, upserting date dimension and metrics rows.

        Args:
            session (Session): SQLAlchemy session to use for this operation.
            df (DataFrame): Cleaned weather data. Must contain all columns
                listed in ``DATE_DIM_COLS`` and ``WEATHER_METRICS_COLS``.

        Returns:
            None.

        Raises:
            DatabaseError: If the operation violates a database constraint
                or otherwise fails at the database layer.
        """
        try:
            # Upsert date related data
            date_data = df[DATE_DIM_COLS].to_dict(orient="records")
            stmt = pg_insert(DateDimDB).values(date_data)
            ignore_insert_stmt = stmt.on_conflict_do_nothing(
                index_elements=["weather_date"]
            )
            session.execute(ignore_insert_stmt)
            session.commit()

            metrics_data = df[WEATHER_METRICS_COLS].to_dict(orient="records")
            stmt = pg_insert(DailyWeatherMetricsDB).values(metrics_data)

            # Update all columns if the primary key already exists
            update_dict = {
                col.name: stmt.excluded[col.name]
                for col in DailyWeatherMetricsDB.__table__.columns
                if not (col.primary_key or col.name == "created_at")
            }

            if "updated_at" in update_dict:
                update_dict["updated_at"] = datetime.now()

            upsert_stmt = stmt.on_conflict_do_update(
                index_elements=[
                    "airport_code",
                    "weather_date",
                ],
                set_=update_dict,
            )

            session.execute(upsert_stmt)
            session.commit()
        except IntegrityError as e:
            session.rollback()
            raise DatabaseError(f"Could not insert record: {str(e)}") from e
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseError(f"Failed to insert record: {str(e)}") from e
