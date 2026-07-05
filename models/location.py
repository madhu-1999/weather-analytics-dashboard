from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


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
