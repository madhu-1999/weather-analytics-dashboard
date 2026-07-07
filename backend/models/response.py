from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, List, Optional

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


class DateResponse(BaseModel):
    weather_date: Annotated[date, Field(description="Date in YYYY-MM-DD format")]
    day_of_month: Annotated[int, Field(description="Day in date")]
    month_name: Annotated[str, Field(description="Month name in date")]
    year: Annotated[int, Field(description="Year in date")]


class FilterOptionsResponse(BaseModel):
    locations: Annotated[
        List[LocationResponse], Field(description="Supported locations")
    ]
    date_range: Annotated[
        List[DateResponse],
        Field(
            description="""Filter date range. 1st element is min_date, 
                2nd element is max_date. If only one date is available, it is both min and max date""",
            max_length=2,
        ),
    ]


class KPICardData(BaseModel):
    max_temp: Annotated[
        Decimal, Field(description="Maximum temperature (°C) in selected date range")
    ]
    min_temp: Annotated[
        Decimal, Field(description="Minimum temperature (°C) in selected date range")
    ]
    precipitation_days_sum: Annotated[
        int, Field(description="Total precipitation days in selected date range")
    ]
    total_precipitation: Annotated[
        Decimal, Field(description="Total precipitation (mm) in selected date range")
    ]
    max_wind_speed: Annotated[
        Decimal, Field(description="Maximum wind speed (km/h) in selected date range")
    ]
    min_wind_speed: Annotated[
        Decimal, Field(description="Minimum wind speed (km/h) in selected date range")
    ]


class SingleLocationDashboardDataResponse(BaseModel):
    kpi_data: Annotated[KPICardData, Field(description="Data displayed in KPI card")]
