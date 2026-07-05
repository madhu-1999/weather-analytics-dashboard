from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.tables.config import LocationDB
from exceptions import DatabaseError


class LocationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_locations(self) -> List[LocationDB]:
        """Fetch all location records from the database.

        Returns:
            List[LocationDB]: All location records currently stored. Empty
            if none exist.

        Raises:
            DatabaseError: If the query fails at the database layer.
        """
        try:
            stmt = select(LocationDB)
            return list(self.session.scalars(stmt).all())
        except Exception as e:
            raise DatabaseError(f"Could not fetch locations: {str(e)}") from e
