from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_db
from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.repositories.store_repository import StoreRepository
from domain.catalog.schemas import CatalogHealth, DealRead, FreeGameRead, RefreshStatus, StoreRead
from domain.catalog.services.get_catalog_health import get_catalog_health
from domain.catalog.services.list_deals import list_deals
from domain.catalog.services.list_free_games import list_free_games
from domain.catalog.services.list_stores import list_stores

DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_store_repository(session: DBSession) -> StoreRepository:
    return StoreRepository(session)


async def get_price_snapshot_repository(session: DBSession) -> PriceSnapshotRepository:
    return PriceSnapshotRepository(session)


async def get_scrape_run_repository(session: DBSession) -> ScrapeRunRepository:
    return ScrapeRunRepository(session)


async def get_deals_service(
    repository: Annotated[PriceSnapshotRepository, Depends(get_price_snapshot_repository)],
) -> list[DealRead]:
    return await list_deals(repository)


async def get_free_games_service(
    repository: Annotated[PriceSnapshotRepository, Depends(get_price_snapshot_repository)],
) -> list[FreeGameRead]:
    return await list_free_games(repository)


async def get_stores_service(
    repository: Annotated[StoreRepository, Depends(get_store_repository)],
) -> list[StoreRead]:
    return await list_stores(repository)


def get_refresh_service() -> RefreshStatus:
    return RefreshStatus(started_at=datetime.now(UTC), stores=[])


async def get_health_service(
    repository: Annotated[ScrapeRunRepository, Depends(get_scrape_run_repository)],
) -> CatalogHealth:
    return await get_catalog_health(repository)
