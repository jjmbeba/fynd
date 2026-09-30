import logging
from datetime import UTC, datetime, time, timedelta, tzinfo

from sqlalchemy.ext.asyncio import AsyncSession

from core.clock import Clock, SystemClock
from domain.catalog.models import ScrapeStatus, Store
from domain.catalog.repositories.fx_rate_repository import FxRateRepository
from domain.catalog.repositories.listing_repository import ListingRepository
from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.repositories.store_repository import StoreRepository
from domain.catalog.schemas import RefreshStatus, StoreScrapeStatus
from domain.catalog.services.ingestion import IngestionService
from infrastructure.fx.client import FxClient
from infrastructure.scrapers import StoreScraper

logger = logging.getLogger(__name__)


def host_timezone() -> tzinfo:
    local = datetime.now().astimezone().tzinfo
    return local if local is not None else UTC


class ScrapingService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        store_repository: StoreRepository,
        run_repository: ScrapeRunRepository,
        ingestion: IngestionService,
        scrapers: list[StoreScraper],
        clock: Clock | None = None,
        tz: tzinfo | None = None,
    ) -> None:
        self._session = session
        self._stores = store_repository
        self._runs = run_repository
        self._ingestion = ingestion
        self._scrapers = scrapers
        self._clock = clock or SystemClock()
        self._tz = tz or host_timezone()

    async def run_all(self) -> RefreshStatus:
        started_at = self._clock.now()
        results = [await self._scrape_one(scraper) for scraper in self._scrapers]
        return RefreshStatus(started_at=started_at, stores=results)

    async def self_heal_if_needed(self) -> None:
        for scraper in self._scrapers:
            await self._scrape_one(scraper, skip_if_ran_today=True)

    async def _scrape_one(
        self, scraper: StoreScraper, *, skip_if_ran_today: bool = False
    ) -> StoreScrapeStatus:
        try:
            store = await self._upsert_store(scraper)
            if skip_if_ran_today and await self._already_scraped_today(store.id):
                return self._skipped_status(scraper)
            return await self._ingestion.ingest(scraper, store)
        except Exception as exc:
            logger.warning(
                "Refresh failed for store",
                extra={"store_slug": scraper.store_slug},
                exc_info=True,
            )
            return self._error_status(scraper, exc)

    async def _upsert_store(self, scraper: StoreScraper) -> Store:
        async with self._session.begin_nested():
            return await self._stores.upsert_by_slug(
                slug=scraper.store_slug,
                display_name=scraper.store_slug.title(),
            )

    async def _already_scraped_today(self, store_id: int) -> bool:
        start, end = self._local_day_bounds()
        return await self._runs.has_successful_run_between(store_id=store_id, start=start, end=end)

    def _local_day_bounds(self) -> tuple[datetime, datetime]:
        local_now = self._clock.now().astimezone(self._tz)
        start_local = datetime.combine(local_now.date(), time.min, tzinfo=self._tz)
        start = start_local.astimezone(UTC)
        end = (start_local + timedelta(days=1)).astimezone(UTC)
        return start, end

    def _error_status(self, scraper: StoreScraper, exc: Exception) -> StoreScrapeStatus:
        now = self._clock.now()
        return StoreScrapeStatus(
            store_slug=scraper.store_slug,
            status=ScrapeStatus.ERROR,
            listings_observed=0,
            error_message=str(exc)[:2048],
            started_at=now,
            last_scrape_at=None,
        )

    def _skipped_status(self, scraper: StoreScraper) -> StoreScrapeStatus:
        now = self._clock.now()
        return StoreScrapeStatus(
            store_slug=scraper.store_slug,
            status=ScrapeStatus.SUCCESS,
            listings_observed=0,
            error_message=None,
            started_at=now,
            last_scrape_at=now,
        )


def build_scraping_service(
    *,
    session: AsyncSession,
    scrapers: list[StoreScraper],
    fx_client: FxClient,
    clock: Clock | None = None,
    tz: tzinfo | None = None,
) -> ScrapingService:
    clock = clock or SystemClock()
    return ScrapingService(
        session=session,
        store_repository=StoreRepository(session),
        run_repository=ScrapeRunRepository(session),
        ingestion=IngestionService(
            session=session,
            listing_repository=ListingRepository(session),
            snapshot_repository=PriceSnapshotRepository(session),
            run_repository=ScrapeRunRepository(session),
            fx_repository=FxRateRepository(session),
            fx_client=fx_client,
            clock=clock,
        ),
        scrapers=scrapers,
        clock=clock,
        tz=tz,
    )
