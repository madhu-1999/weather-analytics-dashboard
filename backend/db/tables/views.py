from decimal import Decimal
from typing import Optional

from sqlalchemy import Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class WeeklyWeatherMV(Base):
    __tablename__ = "mv_weekly_weather"

    # Materialized views don't have true primary keys, but SQLAlchemy requires one
    airport_code: Mapped[str] = mapped_column(Integer, primary_key=True)
    year_int: Mapped[int] = mapped_column(Integer, primary_key=True)
    week_of_year: Mapped[int] = mapped_column(Integer, primary_key=True)

    temp_mean: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    temp_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    temp_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))

    wind_speed_mean: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_speed_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_speed_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_mean: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    precipitation_sum: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    precipitation_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))


class MonthlyWeatherMV(Base):
    __tablename__ = "mv_monthly_weather"

    # Materialized views don't have true primary keys, but SQLAlchemy requires one
    airport_code: Mapped[int] = mapped_column(Integer, primary_key=True)
    year_int: Mapped[int] = mapped_column(Integer, primary_key=True)
    month_int: Mapped[int] = mapped_column(Integer, primary_key=True)

    temp_mean: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    temp_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    temp_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))

    wind_speed_mean: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_speed_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_speed_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_mean: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    precipitation_sum: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    precipitation_hours: Mapped[Optional[int]] = mapped_column(Numeric(4, 1))
