from datetime import date, datetime, timezone
import logging
from typing import List

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.tables.config import IngestedFilesDB
from exceptions import DatabaseError
from models.constants import IngestionStatus


logger = logging.getLogger(__name__)


class IngestedFilesRepository:
    """Data-access layer for the ingested files tracking table."""

    def __init__(self, session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            session (Session): SQLAlchemy session to use for queries and
                commits.

        Returns:
            None.
        """
        self.session = session
        self.logger = logger

    def insert_record(
        self, filename: str, airport_code: str, start_date: date, end_date: date
    ) -> None:
        """Insert a record marking a file as ingested with status as PENDING

        Args:
            filename (str): Name of the ingested file.
            airport_code (str): Airport/location code the file's data
                belongs to.
            start_date (date): Start of the date range covered by the file.
            end_date (date): End of the date range covered by the file.

        Returns:
            None.

        Raises:
            DatabaseError: If the insert violates a database constraint
                or if the insert fails at the database layer, or if the insert executes
                without error but returns no row.
        """
        try:
            stmt = (
                insert(IngestedFilesDB)
                .values(
                    filename=filename,
                    airport_code=airport_code,
                    start_date=start_date,
                    end_date=end_date,
                )
                .returning(IngestedFilesDB)
            )

            created_record = self.session.execute(stmt).first()
            if not created_record:
                raise DatabaseError("Could not insert record for ingested file")
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise DatabaseError(f"Could not insert record: {str(e)}") from e
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to insert record: {str(e)}") from e

    def get_pending_files(self) -> List[IngestedFilesDB]:
        """Fetch all ingested-file records with status PENDING.

        Returns:
            List[IngestedFilesDB]: Records currently marked PENDING. Empty
            if none exist.

        Raises:
            DatabaseError: If the query fails at the database layer.
        """
        try:
            stmt = select(IngestedFilesDB).where(
                IngestedFilesDB.status == IngestionStatus.PENDING
            )
            return list(self.session.scalars(stmt).all())
        except Exception as e:
            raise DatabaseError(f"Could not fetch locations: {str(e)}") from e

    def update_status(
        self, session: Session, ingestion_id: int, status: IngestionStatus
    ) -> None:
        """Update the status (and processed timestamp) of an ingested-file record.

        Args:
            session (Session): SQLAlchemy session to use for this update. If
                falsy, the repository's own session is used instead.
            ingestion_id (int): Primary key of the record
                to update.
            status (IngestionStatus): New status to set on the record.

        Returns:
            None.

        Raises:
            DatabaseError: If no record matches ``ingestion_id``, if the
                update violates a database constraint, or if the update
                otherwise fails at the database layer.
        """
        if not session:
            session = self.session
        try:
            stmt = (
                update(IngestedFilesDB)
                .where(IngestedFilesDB.id == ingestion_id)
                .values(status=status, processed_at=datetime.now(timezone.utc))
                .returning(IngestedFilesDB)
            )
            updated_record = session.execute(stmt).first()
            if not updated_record:
                self.logger.warning(
                    f"Update failed for unknown reason, for ingestion_id: {ingestion_id} status: {status}"
                )
                raise DatabaseError("Could not update record for ingested file")
            session.commit()
        except IntegrityError as e:
            session.rollback()
            self.logger.error(
                f"Update failed for ingestion_id: {ingestion_id} status: {status} due to: {e.detail}"
            )
            raise DatabaseError(f"Could not update record: {str(e)}") from e
        except SQLAlchemyError as e:
            self.logger.error(
                f"Update failed for ingestion_id: {ingestion_id} status: {status} due to: {e}"
            )
            raise DatabaseError(f"Failed to update record: {str(e)}") from e
