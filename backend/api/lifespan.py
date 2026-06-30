import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.config import get_settings
from core.database import close_engine, get_engine


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()

    logging.basicConfig(level=settings.log_level)
    get_engine()

    yield

    await close_engine()
