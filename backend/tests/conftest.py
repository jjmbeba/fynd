from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import AnyUrl
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.deps import get_db
from core.config import Settings, get_settings
from core.database import Base
from main import create_app


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings(
        environment="test", database_url=AnyUrl("sqlite+aiosqlite:///test.db"), debug=True
    )


@pytest.fixture(autouse=True)
def _reset_settings_cache():
    get_settings.cache_clear()
    yield

    get_settings.cache_clear()


@pytest_asyncio.fixture
async def engine(settings: Settings):
    test_engine = create_async_engine(str(settings.database_url), echo=False)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession]:
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    async with session_maker() as session:
        yield session

        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    app = create_app()

    async def _override_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = _override_db

    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
