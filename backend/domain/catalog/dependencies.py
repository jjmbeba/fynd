from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from domain.catalog.repositories.fx_rate_repository import FxRateRepository
from domain.catalog.repositories.listing_repository import ListingRepository
from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.repositories.store_repository import StoreRepository
from domain.catalog.schemas import (
    CatalogHealth,
    DealRead,
    FreeGameRead,
    StoreRead,
    StoreScrapeStatus,
)
from domain.catalog.services.refresh_catalog import (
    RefreshCatalogService,
    build_refresh_catalog_service,
)
from infrastructure.fx.client import FxClient
from infrastructure.fx.registry import get_active_fx_clients
from infrastructure.scrapers import StoreScraper, get_active_scrapers

DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_store_repository(session: DBSession) -> StoreRepository:
    return StoreRepository(session)


async def get_price_snapshot_repository(session: DBSession) -> PriceSnapshotRepository:
    return PriceSnapshotRepository(session)


async def get_scrape_run_repository(session: DBSession) -> ScrapeRunRepository:
    return ScrapeRunRepository(session)


async def get_listing_repository(session: DBSession) -> ListingRepository:
    return ListingRepository(session)


async def get_fx_rate_repository(
    session: DBSession,
) -> FxRateRepository:
    return FxRateRepository(session)


async def get_deals_service(
    repository: Annotated[PriceSnapshotRepository, Depends(get_price_snapshot_repository)],
) -> list[DealRead]:
    rows = await repository.latest_sales_with_listing()
    return [
        DealRead(
            title=listing.title,
            listing_id=listing.id,
            store_slug=store.slug,
            store_display_name=store.display_name,
            base_amount=snapshot.base_amount,
            native_amount=snapshot.native_amount,
            kes_amount=snapshot.kes_amount,
            currency=snapshot.currency,
            discount_percent=snapshot.discount_percent,
            observed_at=snapshot.observed_at,
        )
        for snapshot, listing, store in rows
    ]


async def get_free_games_service(
    repository: Annotated[PriceSnapshotRepository, Depends(get_price_snapshot_repository)],
) -> list[FreeGameRead]:
    rows = await repository.latest_free_games_with_listing()
    return [
        FreeGameRead(
            title=listing.title,
            listing_id=listing.id,
            store_slug=store.slug,
            store_display_name=store.display_name,
            currency=snapshot.currency,
            base_amount=snapshot.base_amount,
            observed_at=snapshot.observed_at,
        )
        for snapshot, listing, store in rows
    ]


async def get_stores_service(
    repository: Annotated[StoreRepository, Depends(get_store_repository)],
) -> list[StoreRead]:
    stores = await repository.list_active()
    return [StoreRead.model_validate(store) for store in stores]


async def get_refresh_catalog_service(
    session: DBSession,
    scrapers: Annotated[list[StoreScraper], Depends(get_active_scrapers)],
    fx_clients: Annotated[list[FxClient], Depends(get_active_fx_clients)],
) -> RefreshCatalogService:
    if not fx_clients:
        raise ValueError("At least one active FX client is required")
    return build_refresh_catalog_service(
        session=session, scrapers=scrapers, fx_client=fx_clients[0]
    )


async def get_health_service(
    repository: Annotated[ScrapeRunRepository, Depends(get_scrape_run_repository)],
) -> CatalogHealth:
    rows = await repository.latest_runs_with_store()
    stores = [
        StoreScrapeStatus(
            store_slug=store.slug,
            status=run.status,
            listings_observed=run.listings_observed,
            error_message=run.error_message,
            started_at=run.started_at,
            last_scrape_at=run.finished_at,
        )
        for run, store in rows
    ]
    return CatalogHealth(stores=stores)
