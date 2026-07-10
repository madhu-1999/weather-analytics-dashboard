from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, status

from dependencies import get_dashboard_service
from models.constants import AggLevelEnum
from models.response import FilterOptionsResponse, SingleLocationDashboardDataResponse
from services import DashboardService


router = APIRouter()


@router.get(
    "/options", status_code=status.HTTP_200_OK, response_model=FilterOptionsResponse
)
async def get_options(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> FilterOptionsResponse:
    return dashboard_service.get_options()


@router.get(
    "/data/{airport_code}",
    status_code=status.HTTP_200_OK,
    response_model=SingleLocationDashboardDataResponse,
)
def get_data(
    airport_code: str,
    start_date: date,
    end_date: date,
    agg_level: AggLevelEnum = AggLevelEnum.YEAR,
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> SingleLocationDashboardDataResponse:
    return dashboard_service.get_data(airport_code, start_date, end_date, agg_level)
