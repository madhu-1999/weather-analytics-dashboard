from sqlalchemy.orm import Session
from fastapi import Depends

from db.db import get_session
from repository import IngestedFilesRepository


async def get_ingested_files_repo(
    db: Session = Depends(get_session),
) -> IngestedFilesRepository:
    return IngestedFilesRepository(db)
