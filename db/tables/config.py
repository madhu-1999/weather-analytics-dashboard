from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Column, Date, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base
from models.enums import IngestionStatus


class LocationDB(Base):
    __tablename__ = "locations"

    airport_code: Mapped[str] = mapped_column(String(10), primary_key=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), nullable=False)

    ingested_files: Mapped[list["IngestedFilesDB"]] = relationship(
        back_populates="location"
    )


class IngestedFilesDB(Base):
    __tablename__ = "ingested_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    airport_code: Mapped[str] = mapped_column(
        String(10),
        ForeignKey("locations.airport_code", name="ingested_files_airport_code_fkey"),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(nullable=False)
    end_date: Mapped[date] = mapped_column(nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(
        default=IngestionStatus.PENDING,
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(default=None, nullable=True)

    location: Mapped["LocationDB"] = relationship(back_populates="ingested_files")
