from typing import Annotated

from fastapi import APIRouter, Depends, status

from domain.catalog.dependencies import (
    get_deals_service,
    get_free_games_service,
    get_health_service,
    get_refresh_service,
    get_stores_service,
)
from domain.catalog.schemas import CatalogHealth, DealRead, FreeGameRead, RefreshStatus, StoreRead

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get(
    "/stores",
    response_model=list[StoreRead],
    status_code=status.HTTP_200_OK,
    summary="List observed stores",
)
def list_stores(stores: Annotated[list[StoreRead], Depends(get_stores_service)]) -> list[StoreRead]:
    return stores


@router.get(
    "/deals",
    response_model=list[DealRead],
    status_code=status.HTTP_200_OK,
    summary="List current deals",
)
def list_deals(deals: Annotated[list[DealRead], Depends(get_deals_service)]) -> list[DealRead]:
    return deals


@router.get(
    "/free-games",
    response_model=list[FreeGameRead],
    status_code=status.HTTP_200_OK,
    summary="List currently free games",
)
def list_free_games(
    games: Annotated[list[FreeGameRead], Depends(get_free_games_service)],
) -> list[FreeGameRead]:
    return games


@router.post(
    "/refresh",
    response_model=RefreshStatus,
    status_code=status.HTTP_200_OK,
    summary="Trigger immediate scrape of all active stores",
)
def trigger_refresh(
    result: Annotated[RefreshStatus, Depends(get_refresh_service)],
) -> RefreshStatus:
    return result


@router.get(
    "/health",
    response_model=CatalogHealth,
    status_code=status.HTTP_200_OK,
    summary="Get the most recent scrape state per store",
)
def get_health(
    result: Annotated[CatalogHealth, Depends(get_health_service)],
) -> CatalogHealth:
    return result
