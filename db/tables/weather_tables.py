from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.tables.config import LocationDB, WeatherCodesDB
from db.base import Base


class DateDimDB(Base):
    __tablename__ = "date_dimension"

    weather_date: Mapped[date] = mapped_column(Date, primary_key=True)
    epoch_timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)
    day_of_month: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week_int: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1 (Monday) to 7 (Sunday)"
    )
    day_of_week_name: Mapped[str] = mapped_column(
        String(9), nullable=False, comment="'Monday', 'Tuesday'"
    )
    day_of_year: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1 to 366"
    )
    week_of_year: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="1 to 53"
    )
    month_int: Mapped[int] = mapped_column(Integer, nullable=False, comment="1 to 12")
    month_name: Mapped[str] = mapped_column(
        String(9), nullable=False, comment="'January', 'February'"
    )
    quarter: Mapped[int] = mapped_column(Integer, nullable=False, comment="1 to 4")
    year_int: Mapped[int] = mapped_column(Integer, nullable=False)


class DailyWeatherMetricsDB(Base):
    __tablename__ = "daily_weather_metrics"

    airport_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey(
            "locations.airport_code",
            name="locations_airport_code_fkey",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )
    weather_date: Mapped[date] = mapped_column(
        Date,
        ForeignKey("date_dimension.weather_date", name="date_dim_weather_date_fkey"),
        primary_key=True,
    )
    weather_code: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "weather_codes.weather_code", name="weather_codes_weather_code_fkey"
        ),
        nullable=False,
    )

    temperature_2m_mean_celsius: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(4, 1)
    )
    temperature_2m_max_celsius: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    temperature_2m_min_celsius: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    dew_point_2m_mean_celsius: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))

    wind_speed_10m_mean_kmh: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_speed_10m_max_kmh: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_speed_10m_min_kmh: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_10m_mean_kmh: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_10m_max_kmh: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    wind_gusts_10m_min_kmh: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))

    precipitation_sum_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 2))
    precipitation_hours: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    cloud_cover_mean_percent: Mapped[Optional[int]] = mapped_column(Integer)
    relative_humidity_2m_mean_percent: Mapped[Optional[int]] = mapped_column(Integer)
    daylight_duration_sec: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(default=None, nullable=True)

    __table_args__ = (Index("idx_weather_date", "weather_date"),)

    location: Mapped["LocationDB"] = relationship()
    date_dimension: Mapped["DateDimDB"] = relationship()
    weather_code_details: Mapped["WeatherCodesDB"] = relationship()
