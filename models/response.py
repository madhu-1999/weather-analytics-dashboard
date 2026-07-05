from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, Field

from models.constants import IngestionStatus


class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    airport_code: Annotated[
        str, Field(description="IATA Airport code", min_length=3, max_length=4)
    ]
    city: Annotated[str, Field(description="The city in which the airport is")]
    state: Annotated[str, Field(description="Two letter US state code")]
    latitude: Annotated[Decimal, Field(description="Latitude of the airport")]
    longitude: Annotated[Decimal, Field(description="Longitude of the airport")]
    timezone: Annotated[str, Field(description="Timezone information")]


class IngestedFileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Annotated[int, Field(description="Ingestion entry id")]
    filename: Annotated[str, Field(description="Name of ingested file")]
    airport_code: Annotated[str, Field(description="IATA airport code")]
    start_date: Annotated[date, Field(description="Start date for data date range")]
    end_date: Annotated[date, Field(description="End date for data date range")]
    status: Annotated[IngestionStatus, Field(description="Status of ingested file")]
    created_at: Annotated[datetime, Field(description="Ingestion timestamp")]
    processed_at: Annotated[
        Optional[datetime], Field(description="Last modified timestamp")
    ]
