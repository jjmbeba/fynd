import shutil
import tempfile
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta, timezone
from typing import cast

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.clock import FrozenClock
from core.database import Base, build_engine
from domain.catalog.models import ScrapeRun, ScrapeStatus, Store
from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.repositories.store_repository import StoreRepository
from domain.catalog.schemas import StoreScrapeStatus
from domain.catalog.services.ingestion import IngestionService
from domain.catalog.services.scraping import ScrapingService
from infrastructure.scrapers.client import StoreScraper

EAT = timezone(timedelta(hours=3))
# 22:00 UTC is 01:00 the next day in UTC+3, so the local date is not the UTC date.
LOCAL_MORNING = datetime(2026, 6, 1, 22, tzinfo=UTC)


class _Scraper:
    def __init__(self, slug: str) -> None:
        self._slug = slug

    @property
    def store_slug(self) -> str:
        return self._slug

    async def fetch_current_sales(self) -> list[object]:
        return []

    async def fetch_free_games(self) -> list[object]:
        return []

    async def health_check(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


class _Stores:
    async def upsert_by_slug(self, *, slug: str, display_name: str) -> Store:
        if slug == "gog":
            raise RuntimeError("upsert failed")
        return Store(id=1, slug=slug, display_name=display_name, is_active=True)


class _Ingestion:
    def __init__(self) -> None:
        self.slugs: list[str] = []

    async def ingest(self, scraper: StoreScraper, store: Store) -> StoreScrapeStatus:
        self.slugs.append(store.slug)
        return StoreScrapeStatus(
            store_slug=store.slug,
            status=ScrapeStatus.SUCCESS,
            listings_observed=1,
            error_message=None,
            started_at=LOCAL_MORNING,
            last_scrape_at=LOCAL_MORNING,
        )


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    tmp = tempfile.mkdtemp()
    engine = build_engine(
        f"sqlite+aiosqlite:///{tmp}/fynd.db",
        debug=False,
        pool_size=1,
        max_overflow=0,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()
    shutil.rmtree(tmp, ignore_errors=True)


async def test_run_all_keeps_going_when_upsert_fails(session: AsyncSession) -> None:
    ingestion = _Ingestion()
    service = ScrapingService(
        session=session,
        store_repository=cast(StoreRepository, _Stores()),
        run_repository=cast(ScrapeRunRepository, object()),
        ingestion=cast(IngestionService, ingestion),
        scrapers=[cast(StoreScraper, _Scraper("gog")), cast(StoreScraper, _Scraper("steam"))],
        clock=FrozenClock(LOCAL_MORNING),
        tz=UTC,
    )

    status = await service.run_all()

    assert [store.store_slug for store in status.stores] == ["gog", "steam"]
    assert status.stores[0].status is ScrapeStatus.ERROR
    assert status.stores[0].error_message == "upsert failed"
    assert status.stores[1].status is ScrapeStatus.SUCCESS
    assert ingestion.slugs == ["steam"]


async def test_self_heal_uses_local_day_not_utc_date(session: AsyncSession) -> None:
    steam = Store(slug="steam", display_name="Steam", is_active=True)
    epic = Store(slug="epic", display_name="Epic", is_active=True)
    session.add_all([steam, epic])
    await session.flush()

    same_local_day = datetime(2026, 6, 1, 21, 30, tzinfo=UTC)
    previous_local_day = datetime(2026, 6, 1, 20, tzinfo=UTC)
    session.add_all(
        [
            ScrapeRun(
                store_id=steam.id,
                status=ScrapeStatus.SUCCESS,
                started_at=same_local_day,
                finished_at=same_local_day,
                listings_observed=1,
            ),
            ScrapeRun(
                store_id=epic.id,
                status=ScrapeStatus.SUCCESS,
                started_at=previous_local_day,
                finished_at=previous_local_day,
                listings_observed=1,
            ),
        ]
    )
    await session.flush()

    ingestion = _Ingestion()
    service = ScrapingService(
        session=session,
        store_repository=StoreRepository(session),
        run_repository=ScrapeRunRepository(session),
        ingestion=cast(IngestionService, ingestion),
        scrapers=[cast(StoreScraper, _Scraper("steam")), cast(StoreScraper, _Scraper("epic"))],
        clock=FrozenClock(LOCAL_MORNING),
        tz=EAT,
    )

    await service.self_heal_if_needed()

    assert ingestion.slugs == ["epic"]
