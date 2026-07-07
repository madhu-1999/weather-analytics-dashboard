from fastapi import APIRouter, Depends, status

from dependencies import get_dashboard_service
from models.response import FilterOptionsResponse
from services import DashboardService


router = APIRouter()


@router.get(
    "/options", status_code=status.HTTP_200_OK, response_model=FilterOptionsResponse
)
async def get_options(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> FilterOptionsResponse:
    return dashboard_service.get_options()
