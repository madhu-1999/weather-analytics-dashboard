from sqlalchemy.orm import Session
from fastapi import Depends

from db.db import get_session
from repository import IngestedFilesRepository, LocationRepository
from services import IngestionService, LocationService


async def get_ingested_files_repo(
    db: Session = Depends(get_session),
) -> IngestedFilesRepository:
    return IngestedFilesRepository(db)


async def get_location_repo(
    db: Session = Depends(get_session),
) -> LocationRepository:
    return LocationRepository(db)


async def get_location_service(
    location_repo: LocationRepository = Depends(get_location_repo),
) -> LocationService:
    return LocationService(location_repo)


async def get_ingestion_service(
    ingested_files_repo: IngestedFilesRepository = Depends(get_ingested_files_repo),
    location_service: LocationService = Depends(get_location_service),
) -> IngestionService:
    return IngestionService(ingested_files_repo, location_service)
