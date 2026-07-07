from typing import Any

from sqlalchemy import MetaData, event
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def build_engine(
    database_url: str,
    *,
    debug: bool,
    pool_size: int,
    max_overflow: int,
) -> AsyncEngine:
    url = make_url(database_url)
    kwargs: dict[str, Any] = {
        "echo": debug,
        "pool_pre_ping": True,
    }
    if not url.drivername.startswith("sqlite"):
        kwargs["pool_size"] = pool_size
        kwargs["max_overflow"] = max_overflow

    engine = create_async_engine(database_url, **kwargs)

    if url.drivername.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def _set_sqlite_isolation(dbapi_conn: Any, connection_record: Any) -> None:  # noqa: ARG001
            dbapi_conn.isolation_level = None

        @event.listens_for(engine.sync_engine, "begin")
        def _emit_sqlite_begin(conn: Any) -> None:
            conn.exec_driver_sql("BEGIN")

    return engine
