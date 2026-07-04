from collections.abc import AsyncGenerator

import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from pydantic import AnyUrl

from core.config import Settings
from core.database import Base
from main import create_app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    settings = Settings(
        environment="test",
        database_url=AnyUrl("sqlite+aiosqlite:///:memory:"),
        debug=True,
    )
    app = create_app(settings=settings)

    async with LifespanManager(app):
        engine = app.state.engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
