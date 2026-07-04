import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.config import Settings
from core.database import build_engine
from domain.catalog.services.refresh_catalog import build_refresh_catalog_service
from infrastructure.fx.registry import get_active_fx_clients
from infrastructure.scrapers.registry import get_active_scrapers


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = app.state.settings

    logging.basicConfig(level=settings.log_level)
    app.state.engine = build_engine(
        str(settings.database_url),
        debug=settings.debug,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
    )

    scheduler = _build_scheduler(app, settings)
    scheduler.start()

    try:
        yield
    finally:
        scheduler.shutdown(wait=False)
        await app.state.engine.dispose()


def _build_scheduler(app: FastAPI, settings: Settings) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    async def _scheduled_refresh() -> None:
        async with async_sessionmaker(app.state.engine)() as session:
            try:
                service = build_refresh_catalog_service(
                    session=session,
                    scrapers=get_active_scrapers(),
                    fx_clients=get_active_fx_clients(),
                )

                await service.refresh_all()
                await session.commit()
            except Exception:
                await session.rollback()
                logging.exception("Scheduled refresh failed")

    scheduler.add_job(
        _scheduled_refresh,
        CronTrigger(hour=settings.scrape_hour_local, minute=0),
        id="daily_refresh",
        replace_existing=True,
    )

    return scheduler
