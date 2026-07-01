import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.database import build_engine


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

    try:
        yield
    finally:
        await app.state.engine.dispose()
