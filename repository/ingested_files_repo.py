from datetime import date

from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from db.tables.config import IngestedFilesDB
from exceptions import DatabaseError


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
                self.session.rollback()
                raise DatabaseError("Could not insert record for ingested file")
            self.session.commit()
        except IntegrityError as e:
            self.session.rollback()
            raise DatabaseError(f"Could not insert record: {str(e)}") from e
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to insert record: {str(e)}") from e
