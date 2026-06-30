from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import get_settings

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def _build_engine() -> AsyncEngine:
    settings = get_settings()

    return create_async_engine(
        str(settings.database_url),
        echo=settings.debug,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
    )


def get_engine() -> AsyncEngine:
    global _engine

    if _engine is None:
        _engine = _build_engine()

    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global _session_maker

    if _session_maker is None:
        _session_maker = async_sessionmaker(get_engine(), expire_on_commit=False)

    return _session_maker


async def close_engine() -> None:
    global _engine, _session_maker

    if _engine is not None:
        await _engine.dispose()
        _engine = None

    _session_maker = None
