from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.repositories.store_repository import StoreRepository
from domain.catalog.schemas import CatalogHealth, StoreRead, StoreScrapeStatus
from domain.catalog.services.deals import DealsService
from domain.catalog.services.free_games import FreeGamesService
from domain.catalog.services.scraping import ScrapingService, build_scraping_service
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


async def get_request_scrapers() -> AsyncGenerator[list[StoreScraper]]:
    scrapers = get_active_scrapers()
    try:
        yield scrapers
    finally:
        for scraper in scrapers:
            await scraper.aclose()


async def get_request_fx_clients() -> AsyncGenerator[list[FxClient]]:
    clients = get_active_fx_clients()
    try:
        yield clients
    finally:
        for client in clients:
            await client.aclose()


async def get_deals_service(
    repository: Annotated[PriceSnapshotRepository, Depends(get_price_snapshot_repository)],
) -> DealsService:
    return DealsService(repository)


async def get_free_games_service(
    repository: Annotated[PriceSnapshotRepository, Depends(get_price_snapshot_repository)],
) -> FreeGamesService:
    return FreeGamesService(repository)


async def get_stores_service(
    repository: Annotated[StoreRepository, Depends(get_store_repository)],
) -> list[StoreRead]:
    stores = await repository.list_active()
    return [StoreRead.model_validate(store) for store in stores]


async def get_scraping_service(
    session: DBSession,
    scrapers: Annotated[list[StoreScraper], Depends(get_request_scrapers)],
    fx_clients: Annotated[list[FxClient], Depends(get_request_fx_clients)],
) -> ScrapingService:
    if not fx_clients:
        raise ValueError("At least one active FX client is required")
    return build_scraping_service(session=session, scrapers=scrapers, fx_client=fx_clients[0])


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
