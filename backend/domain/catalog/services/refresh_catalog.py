import logging
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import ScrapeRun, ScrapeStatus
from domain.catalog.repositories.fx_rate_repository import FxRateRepository
from domain.catalog.repositories.listing_repository import ListingRepository
from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.repositories.store_repository import StoreRepository
from domain.catalog.schemas import RefreshStatus, StoreScrapeStatus
from infrastructure.fx.client import FxClient
from infrastructure.scrapers import StoreScraper
from infrastructure.scrapers.client import RawListing

logger = logging.getLogger(__name__)


class RefreshCatalogService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        store_repository: StoreRepository,
        listing_repository: ListingRepository,
        snapshot_repository: PriceSnapshotRepository,
        run_repository: ScrapeRunRepository,
        fx_client: FxClient,
        scrapers: list[StoreScraper],
    ) -> None:
        self._session = session
        self._stores = store_repository
        self._listings = listing_repository
        self._snapshots = snapshot_repository
        self._runs = run_repository
        self._fx_client = fx_client
        self._scrapers = scrapers

    async def refresh_all(self) -> RefreshStatus:
        started_at = datetime.now(UTC)
        results = [await self._refresh_one(scraper=scraper) for scraper in self._scrapers]

        return RefreshStatus(started_at=started_at, stores=results)

    def _build_status(
        self,
        scraper: StoreScraper,
        run: ScrapeRun,
        *,
        status: ScrapeStatus,
        listings_observed: int,
        error_message: str | None,
    ) -> StoreScrapeStatus:
        return StoreScrapeStatus(
            store_slug=scraper.store_slug,
            status=status,
            listings_observed=listings_observed,
            error_message=error_message,
            started_at=run.started_at,
            last_scrape_at=datetime.now(UTC),
        )

    async def _refresh_one(self, scraper: StoreScraper) -> StoreScrapeStatus:
        store = await self._stores.upsert_by_slug(
            slug=scraper.store_slug, display_name=scraper.store_slug.title()
        )

        run = await self._runs.create(store_id=store.id)

        try:
            async with self._session.begin_nested():
                sales = await scraper.fetch_current_sales()
                free = await scraper.fetch_free_games()
                raw = list(sales) + list(free)

                await self._process_listings(raw=raw, store_id=store.id, observed_at=run.started_at)

                await self._runs.complete(run_id=run.id, listings_observed=len(raw))

            return self._build_status(
                scraper,
                run,
                status=ScrapeStatus.SUCCESS,
                listings_observed=len(raw),
                error_message=None,
            )
        except Exception as exc:
            logger.warning(
                "Refresh failed for store",
                extra={"store_slug": scraper.store_slug, "error": str(exc)},
            )

            await self._runs.complete(
                run_id=run.id, listings_observed=0, error_message=str(exc)[:2048]
            )

            return self._build_status(
                scraper,
                run,
                status=ScrapeStatus.ERROR,
                listings_observed=0,
                error_message=str(exc)[:2048],
            )

    async def _process_listings(
        self, raw: Sequence[RawListing], *, store_id: int, observed_at: datetime
    ) -> None:
        fx_repo = FxRateRepository(self._session)
        rate_cache: dict[str, Decimal] = {}

        for listing in raw:
            cache_key = listing.currency

            if cache_key not in rate_cache:
                rate_record = await fx_repo.get_by_date(
                    source=listing.currency, on=observed_at.date()
                )

                if rate_record is None:
                    fetched_rate = await self._fx_client.fetch_rate(
                        source=listing.currency, target="KES", on=observed_at.date()
                    )
                    rate_record = await fx_repo.upsert(
                        source=listing.currency, rate=fetched_rate, on=observed_at.date()
                    )

                rate_cache[cache_key] = rate_record.rate_to_kes

            kes_amount = listing.native_amount * rate_cache[cache_key]
            is_on_sale = (
                not listing.is_free
                and listing.discount_percent is not None
                and 0 < listing.discount_percent < 100
            )

            db_listing = await self._listings.upsert(
                store_id=store_id,
                is_currently_on_sale=is_on_sale,
                store_product_id=listing.store_product_id,
                title=listing.title,
            )

            await self._snapshots.insert(
                listing_id=db_listing.id,
                base_amount=listing.base_amount,
                native_amount=listing.native_amount,
                kes_amount=kes_amount,
                currency=listing.currency,
                discount_percent=listing.discount_percent,
                observed_at=observed_at,
            )


def build_refresh_catalog_service(
    *, session: AsyncSession, scrapers: list[StoreScraper], fx_client: FxClient
) -> RefreshCatalogService:
    return RefreshCatalogService(
        session=session,
        store_repository=StoreRepository(session),
        listing_repository=ListingRepository(session),
        snapshot_repository=PriceSnapshotRepository(session),
        run_repository=ScrapeRunRepository(session),
        fx_client=fx_client,
        scrapers=scrapers,
    )
