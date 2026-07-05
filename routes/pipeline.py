from datetime import date

from fastapi import APIRouter, Depends, status

from dependencies import get_ingestion_service, get_processing_service
from services import IngestionService, ProcessingService


router = APIRouter()


@router.post("/ingest", status_code=status.HTTP_200_OK)
async def ingest_data(
    start_date: date,
    end_date: date,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
) -> None:
    await ingestion_service.start_ingestion(start_date, end_date)


@router.post("/process", status_code=status.HTTP_202_ACCEPTED)
def process_data(
    processing_service: ProcessingService = Depends(get_processing_service),
) -> None:
    processing_service.process_pending_files()
