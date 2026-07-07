from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.tables.weather_tables import DateDimDB
from exceptions import DatabaseError


class DateRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_available_date_range(self) -> List[dict]:
        try:
            # Subqueries for min, max dates
            min_date_subquery = select(
                func.min(DateDimDB.weather_date)
            ).scalar_subquery()
            max_date_subquery = select(
                func.max(DateDimDB.weather_date)
            ).scalar_subquery()

            stmt = select(
                DateDimDB.weather_date,
                DateDimDB.day_of_month,
                DateDimDB.month_name,
                DateDimDB.year_int,
            ).where(DateDimDB.weather_date.in_([min_date_subquery, max_date_subquery]))
            results = self.session.execute(stmt).mappings().all()
            return [dict(row) for row in results]
        except Exception as e:
            raise DatabaseError(f"Could not fetch dates: {str(e)}") from e
