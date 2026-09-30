import shutil
import tempfile
from collections.abc import AsyncGenerator

import pytest_asyncio
from asgi_lifespan import LifespanManager
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import AnyUrl

from core.config import Settings
from core.database import Base
from main import create_app


@pytest_asyncio.fixture
async def app() -> AsyncGenerator[FastAPI]:
    tmp = tempfile.mkdtemp()
    try:
        settings = Settings(
            environment="test",
            database_url=AnyUrl(f"sqlite+aiosqlite:///{tmp}/fynd.db"),
            debug=False,
        )
        application = create_app(settings=settings)
        async with LifespanManager(application):
            async with application.state.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            yield application
        application.dependency_overrides.clear()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
