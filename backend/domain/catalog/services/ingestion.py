import logging
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from core.clock import Clock, SystemClock
from domain.catalog.models import ScrapeStatus, Store
from domain.catalog.repositories.fx_rate_repository import FxRateRepository
from domain.catalog.repositories.listing_repository import ListingRepository
from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.schemas import StoreScrapeStatus
from infrastructure.fx.client import FxClient
from infrastructure.scrapers import StoreScraper
from infrastructure.scrapers.client import RawListing

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(
        self,
        *,
        session: AsyncSession,
        listing_repository: ListingRepository,
        snapshot_repository: PriceSnapshotRepository,
        run_repository: ScrapeRunRepository,
        fx_repository: FxRateRepository,
        fx_client: FxClient,
        clock: Clock | None = None,
    ) -> None:
        self._session = session
        self._listings = listing_repository
        self._snapshots = snapshot_repository
        self._runs = run_repository
        self._fx_rates = fx_repository
        self._fx_client = fx_client
        self._clock = clock or SystemClock()

    async def ingest(self, scraper: StoreScraper, store: Store) -> StoreScrapeStatus:
        observed_at = self._clock.now()
        run = await self._runs.create(store_id=store.id, started_at=observed_at)

        try:
            async with self._session.begin_nested():
                sales = await scraper.fetch_current_sales()
                free = await scraper.fetch_free_games()
                raw = list(sales) + list(free)

                await self._process_listings(raw=raw, store_id=store.id, observed_at=observed_at)
                await self._mark_absent_off_sale(raw=raw, store_id=store.id)
                await self._runs.complete(
                    run_id=run.id,
                    listings_observed=len(raw),
                    finished_at=self._clock.now(),
                )

            return self._status(
                scraper,
                observed_at=observed_at,
                status=ScrapeStatus.SUCCESS,
                listings_observed=len(raw),
                error_message=None,
            )
        except Exception as exc:
            logger.warning(
                "Ingest failed for store",
                extra={"store_slug": scraper.store_slug, "error": str(exc)},
            )
            message = str(exc)[:2048]
            await self._runs.complete(
                run_id=run.id,
                listings_observed=0,
                finished_at=self._clock.now(),
                error_message=message,
            )
            return self._status(
                scraper,
                observed_at=observed_at,
                status=ScrapeStatus.ERROR,
                listings_observed=0,
                error_message=message,
            )

    async def _process_listings(
        self, raw: Sequence[RawListing], *, store_id: int, observed_at: datetime
    ) -> None:
        rate_cache: dict[str, Decimal] = {}

        for listing in raw:
            rate = await self._rate_to_kes(
                currency=listing.currency, observed_at=observed_at, cache=rate_cache
            )
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
                image_url=listing.image_url,
            )
            await self._snapshots.insert(
                listing_id=db_listing.id,
                base_amount=listing.base_amount,
                native_amount=listing.native_amount,
                kes_amount=listing.native_amount * rate,
                currency=listing.currency,
                discount_percent=listing.discount_percent,
                observed_at=observed_at,
            )

    async def _mark_absent_off_sale(self, raw: Sequence[RawListing], *, store_id: int) -> None:
        seen = {listing.store_product_id for listing in raw}
        on_sale = await self._listings.list_on_sale_product_ids(store_id=store_id)
        missing = [product_id for product_id in on_sale if product_id not in seen]
        await self._listings.mark_off_sale(store_id=store_id, store_product_ids=missing)

    async def _rate_to_kes(
        self, *, currency: str, observed_at: datetime, cache: dict[str, Decimal]
    ) -> Decimal:
        if currency in cache:
            return cache[currency]

        on = observed_at.date()
        rate_record = await self._fx_rates.get_by_date(source=currency, on=on)
        if rate_record is None:
            fetched = await self._fx_client.fetch_rate(source=currency, target="KES", on=on)
            rate_record = await self._fx_rates.upsert(source=currency, rate=fetched, on=on)

        cache[currency] = rate_record.rate_to_kes
        return rate_record.rate_to_kes

    def _status(
        self,
        scraper: StoreScraper,
        *,
        observed_at: datetime,
        status: ScrapeStatus,
        listings_observed: int,
        error_message: str | None,
    ) -> StoreScrapeStatus:
        return StoreScrapeStatus(
            store_slug=scraper.store_slug,
            status=status,
            listings_observed=listings_observed,
            error_message=error_message,
            started_at=observed_at,
            last_scrape_at=self._clock.now(),
        )
