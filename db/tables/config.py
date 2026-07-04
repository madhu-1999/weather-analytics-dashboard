from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base
from models.enums import IngestionStatus


class IngestedFilesDB(Base):
    __tablename__ = "ingested_files"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename = Column(String(255), nullable=False)
    airport_code = Column(String(10), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(
        Enum(IngestionStatus),
        default=IngestionStatus.PENDING,
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return (
            f"<IngestedFile(filename='{self.filename}', status='{self.status.value}')>"
        )
