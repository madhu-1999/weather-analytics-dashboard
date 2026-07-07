from sqlalchemy.orm import Session
from fastapi import Depends

from db.db import get_session
from repository import (
    IngestedFilesRepository,
    LocationRepository,
    ProcessFileRepository,
    DateRepository,
    MetricsRepository,
)
from services import (
    IngestionService,
    LocationService,
    ProcessingService,
    DateService,
    DashboardService,
    MetricsService,
)


async def get_ingested_files_repo(
    db: Session = Depends(get_session),
) -> IngestedFilesRepository:
    return IngestedFilesRepository(db)


async def get_location_repo(
    db: Session = Depends(get_session),
) -> LocationRepository:
    return LocationRepository(db)


async def get_date_repo(
    db: Session = Depends(get_session),
) -> DateRepository:
    return DateRepository(db)


async def get_metrics_repo(
    db: Session = Depends(get_session),
) -> MetricsRepository:
    return MetricsRepository(db)


async def get_process_file_repo() -> ProcessFileRepository:
    return ProcessFileRepository()


async def get_location_service(
    location_repo: LocationRepository = Depends(get_location_repo),
) -> LocationService:
    return LocationService(location_repo)


async def get_metrics_service(
    metrics_repo: MetricsRepository = Depends(get_metrics_repo),
) -> MetricsService:
    return MetricsService(metrics_repo)


async def get_date_service(
    date_repo: DateRepository = Depends(get_date_repo),
) -> DateService:
    return DateService(date_repo)


async def get_ingestion_service(
    ingested_files_repo: IngestedFilesRepository = Depends(get_ingested_files_repo),
    location_service: LocationService = Depends(get_location_service),
) -> IngestionService:
    return IngestionService(ingested_files_repo, location_service)


async def get_processing_service(
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    process_file_repo: ProcessFileRepository = Depends(get_process_file_repo),
) -> ProcessingService:
    return ProcessingService(ingestion_service, process_file_repo)


async def get_dashboard_service(
    location_service: LocationService = Depends(get_location_service),
    date_service: DateService = Depends(get_date_service),
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> DashboardService:
    return DashboardService(location_service, date_service, metrics_service)
