import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.config import Settings
from core.database import build_engine
from core.scheduler import AppScheduler
from domain.catalog.services.fx_refresh import build_fx_refresh_service
from domain.catalog.services.scraping import build_scraping_service
from infrastructure.fx.client import FxClient
from infrastructure.fx.registry import get_active_fx_clients
from infrastructure.scrapers.client import StoreScraper
from infrastructure.scrapers.registry import get_active_scrapers

logger = logging.getLogger(__name__)

CatalogWork = Callable[[AsyncSession, list[StoreScraper], FxClient], Awaitable[None]]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings: Settings = app.state.settings

    logging.basicConfig(level=settings.log_level)
    app.state.engine = build_engine(
        str(settings.database_url),
        debug=settings.debug,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )

    async def daily_refresh() -> None:
        await _run_catalog_job(app, _refresh_fx, open_scrapers=False)
        await _run_catalog_job(app, _scrape_all, open_scrapers=True)

    if settings.environment != "test":
        await _run_catalog_job(app, _self_heal, open_scrapers=True)

    scheduler = AppScheduler()
    scheduler.start(daily_refresh, hour=settings.scrape_hour_local)

    try:
        yield
    finally:
        scheduler.stop()
        await app.state.engine.dispose()


async def _scrape_all(
    session: AsyncSession, scrapers: list[StoreScraper], fx_client: FxClient
) -> None:
    service = build_scraping_service(session=session, scrapers=scrapers, fx_client=fx_client)
    await service.run_all()


async def _self_heal(
    session: AsyncSession, scrapers: list[StoreScraper], fx_client: FxClient
) -> None:
    service = build_scraping_service(session=session, scrapers=scrapers, fx_client=fx_client)
    await service.self_heal_if_needed()


async def _refresh_fx(
    session: AsyncSession, _scrapers: list[StoreScraper], fx_client: FxClient
) -> None:
    service = build_fx_refresh_service(session=session, fx_client=fx_client)
    await service.refresh()


async def _run_catalog_job(app: FastAPI, work: CatalogWork, *, open_scrapers: bool) -> None:
    session_maker = async_sessionmaker(app.state.engine, expire_on_commit=False)
    fx_clients: list[FxClient] = []
    scrapers: list[StoreScraper] = []

    async with session_maker() as session:
        try:
            fx_clients = get_active_fx_clients()
            if not fx_clients:
                raise ValueError("At least one active FX client is required")
            if open_scrapers:
                scrapers = get_active_scrapers()
            await work(session, scrapers, fx_clients[0])
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Catalog job failed")
        finally:
            for scraper in scrapers:
                await scraper.aclose()
            for client in fx_clients:
                await client.aclose()
