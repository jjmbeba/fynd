from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from domain.catalog.dependencies import (
    get_deals_service,
    get_free_games_service,
    get_health_service,
    get_scraping_service,
    get_stores_service,
)
from domain.catalog.schemas import CatalogHealth, DealRead, FreeGameRead, RefreshStatus, StoreRead
from domain.catalog.services.deals import DealsService
from domain.catalog.services.free_games import FreeGamesService
from domain.catalog.services.scraping import ScrapingService

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("/stores", response_model=list[StoreRead], summary="List observed stores")
def list_stores(
    stores: Annotated[list[StoreRead], Depends(get_stores_service)],
) -> list[StoreRead]:
    return stores


@router.get("/deals", response_model=list[DealRead], summary="List current deals")
async def list_deals(
    service: Annotated[DealsService, Depends(get_deals_service)],
    store: Annotated[list[str] | None, Query()] = None,
    max_kes_price: Decimal | None = None,
    min_discount_percent: int | None = None,
    q: str | None = None,
) -> list[DealRead]:
    return await service.list(
        store_slugs=store,
        max_kes_price=max_kes_price,
        min_discount_percent=min_discount_percent,
        query=q,
    )


@router.get(
    "/free-games",
    response_model=list[FreeGameRead],
    summary="List currently free games",
)
async def list_free_games(
    service: Annotated[FreeGamesService, Depends(get_free_games_service)],
) -> list[FreeGameRead]:
    return await service.list()


@router.post(
    "/refresh",
    response_model=RefreshStatus,
    summary="Trigger immediate scrape of all active stores",
)
async def trigger_refresh(
    service: Annotated[ScrapingService, Depends(get_scraping_service)],
) -> RefreshStatus:
    return await service.run_all()


@router.get(
    "/health",
    response_model=CatalogHealth,
    summary="Get the most recent scrape state per store",
)
def get_health(
    result: Annotated[CatalogHealth, Depends(get_health_service)],
) -> CatalogHealth:
    return result
