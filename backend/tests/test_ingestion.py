from collections.abc import AsyncGenerator, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import cast

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.clock import FrozenClock
from core.database import build_engine
from domain.catalog.models import Listing, PriceSnapshot, ScrapeRun, ScrapeStatus, Store
from domain.catalog.repositories.fx_rate_repository import FxRateRepository
from domain.catalog.repositories.listing_repository import ListingRepository
from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.services.ingestion import IngestionService
from infrastructure.fx.client import FxClient
from infrastructure.scrapers.client import RawListing, StoreScraper

OBSERVED_AT = datetime(2026, 6, 1, 12, tzinfo=UTC)


class FakeScraper:
    def __init__(
        self,
        sales: Sequence[RawListing] = (),
        free: Sequence[RawListing] = (),
    ) -> None:
        self._sales = list(sales)
        self._free = list(free)

    @property
    def store_slug(self) -> str:
        return "steam"

    async def fetch_current_sales(self) -> Sequence[RawListing]:
        return list(self._sales)

    async def fetch_free_games(self) -> Sequence[RawListing]:
        return list(self._free)

    async def health_check(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


class _Rate:
    def __init__(self, rate: Decimal) -> None:
        self.rate_to_kes = rate


class FakeFxRepository:
    def __init__(self) -> None:
        self.saved: list[tuple[str, date, Decimal]] = []

    async def get_by_date(self, *, source: str, on: date) -> _Rate | None:
        for saved_source, saved_on, rate in self.saved:
            if saved_source == source and saved_on == on:
                return _Rate(rate)
        return None

    async def upsert(self, *, source: str, on: date, rate: Decimal) -> _Rate:
        self.saved.append((source, on, rate))
        return _Rate(rate)


class FakeFxClient:
    def __init__(self) -> None:
        self.calls = 0

    @property
    def provider_slug(self) -> str:
        return "fake"

    async def fetch_rate(self, source: str, target: str, on: date) -> Decimal:
        self.calls += 1
        assert source == "USD"
        assert target == "KES"
        assert on == OBSERVED_AT.date()
        return Decimal("130")

    async def health_check(self) -> bool:
        return True

    async def aclose(self) -> None:
        return None


class CompletedRun:
    def __init__(
        self,
        run_id: int,
        listings_observed: int,
        finished_at: datetime,
        error_message: str | None,
    ) -> None:
        self.run_id = run_id
        self.listings_observed = listings_observed
        self.finished_at = finished_at
        self.error_message = error_message


class FakeRunRepository:
    def __init__(self) -> None:
        self.created: list[ScrapeRun] = []
        self.completed: list[CompletedRun] = []

    async def create(self, *, store_id: int, started_at: datetime) -> ScrapeRun:
        run = ScrapeRun(
            id=len(self.created) + 1,
            store_id=store_id,
            status=ScrapeStatus.RUNNING,
            started_at=started_at,
        )
        self.created.append(run)
        return run

    async def complete(
        self,
        *,
        run_id: int,
        listings_observed: int,
        finished_at: datetime,
        error_message: str | None = None,
    ) -> None:
        self.completed.append(CompletedRun(run_id, listings_observed, finished_at, error_message))


class SnapshotInsert:
    def __init__(
        self,
        *,
        listing_id: int,
        base_amount: Decimal,
        native_amount: Decimal,
        kes_amount: Decimal,
        currency: str,
        discount_percent: int | None,
    ) -> None:
        self.listing_id = listing_id
        self.base_amount = base_amount
        self.native_amount = native_amount
        self.kes_amount = kes_amount
        self.currency = currency
        self.discount_percent = discount_percent


class FakeSnapshotRepository:
    def __init__(self) -> None:
        self.inserts: list[SnapshotInsert] = []

    async def insert(
        self,
        *,
        listing_id: int,
        base_amount: Decimal,
        native_amount: Decimal,
        kes_amount: Decimal,
        currency: str,
        discount_percent: int | None,
        observed_at: datetime,
    ) -> PriceSnapshot:
        self.inserts.append(
            SnapshotInsert(
                listing_id=listing_id,
                base_amount=base_amount,
                native_amount=native_amount,
                kes_amount=kes_amount,
                currency=currency,
                discount_percent=discount_percent,
            )
        )
        return PriceSnapshot(
            id=len(self.inserts),
            listing_id=listing_id,
            base_amount=base_amount,
            native_amount=native_amount,
            kes_amount=kes_amount,
            currency=currency,
            discount_percent=discount_percent,
            observed_at=observed_at,
        )


class FakeListingRepository:
    def __init__(self, on_sale: list[str] | None = None) -> None:
        self.upserts: list[Listing] = []
        self.on_sale_ids = list(on_sale or [])
        self.off_sale: list[tuple[int, list[str]]] = []

    async def upsert(
        self, *, store_id: int, store_product_id: str, title: str, is_currently_on_sale: bool
    ) -> Listing:
        listing = Listing(
            id=len(self.upserts) + 1,
            store_id=store_id,
            store_product_id=store_product_id,
            title=title,
            is_currently_on_sale=is_currently_on_sale,
        )
        self.upserts.append(listing)
        return listing

    async def list_on_sale_product_ids(self, *, store_id: int) -> list[str]:
        assert store_id == 1
        return list(self.on_sale_ids)

    async def mark_off_sale(self, *, store_id: int, store_product_ids: Sequence[str]) -> None:
        self.off_sale.append((store_id, list(store_product_ids)))


def _raw(product_id: str, *, title: str = "Hades") -> RawListing:
    return RawListing(
        store_product_id=product_id,
        title=title,
        currency="USD",
        base_amount=Decimal("20"),
        native_amount=Decimal("10"),
        discount_percent=50,
        is_free=False,
    )


def _service(
    session: AsyncSession,
    *,
    listings: FakeListingRepository,
    snapshots: FakeSnapshotRepository,
    runs: FakeRunRepository,
    fx_rates: FakeFxRepository,
    fx_client: FakeFxClient,
) -> IngestionService:
    return IngestionService(
        session=session,
        listing_repository=cast(ListingRepository, listings),
        snapshot_repository=cast(PriceSnapshotRepository, snapshots),
        run_repository=cast(ScrapeRunRepository, runs),
        fx_repository=cast(FxRateRepository, fx_rates),
        fx_client=cast(FxClient, fx_client),
        clock=FrozenClock(OBSERVED_AT),
    )


@pytest_asyncio.fixture
async def session() -> AsyncGenerator[AsyncSession]:
    engine = build_engine("sqlite+aiosqlite:///:memory:", debug=False, pool_size=1, max_overflow=0)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as db_session:
        yield db_session
    await engine.dispose()


def _store() -> Store:
    return Store(id=1, slug="steam", display_name="Steam", is_active=True)


async def test_ingest_creates_listing_and_closes_run(session: AsyncSession) -> None:
    listings = FakeListingRepository()
    snapshots = FakeSnapshotRepository()
    runs = FakeRunRepository()
    fx_client = FakeFxClient()
    service = _service(
        session,
        listings=listings,
        snapshots=snapshots,
        runs=runs,
        fx_rates=FakeFxRepository(),
        fx_client=fx_client,
    )

    status = await service.ingest(cast(StoreScraper, FakeScraper([_raw("hades")])), _store())

    assert status.status is ScrapeStatus.SUCCESS
    assert status.listings_observed == 1
    assert listings.upserts[0].store_product_id == "hades"
    assert listings.upserts[0].is_currently_on_sale is True
    assert snapshots.inserts[0].kes_amount == Decimal("1300")
    assert fx_client.calls == 1
    assert len(runs.created) == 1
    assert runs.completed[0].run_id == runs.created[0].id
    assert runs.completed[0].listings_observed == 1
    assert runs.completed[0].finished_at == OBSERVED_AT
    assert runs.completed[0].error_message is None


async def test_ingest_updates_existing_listing(session: AsyncSession) -> None:
    listings = FakeListingRepository()
    runs = FakeRunRepository()
    service = _service(
        session,
        listings=listings,
        snapshots=FakeSnapshotRepository(),
        runs=runs,
        fx_rates=FakeFxRepository(),
        fx_client=FakeFxClient(),
    )
    scraper = cast(StoreScraper, FakeScraper([_raw("hades", title="Hades")]))
    await service.ingest(scraper, _store())

    updated = cast(StoreScraper, FakeScraper([_raw("hades", title="Hades II")]))
    await service.ingest(updated, _store())

    assert [listing.title for listing in listings.upserts] == ["Hades", "Hades II"]
    assert all(listing.store_product_id == "hades" for listing in listings.upserts)
    assert len(runs.created) == 2
    assert all(run.error_message is None for run in runs.completed)


async def test_ingest_marks_absent_listing_off_sale_without_snapshot(
    session: AsyncSession,
) -> None:
    listings = FakeListingRepository(on_sale=["gone"])
    snapshots = FakeSnapshotRepository()
    service = _service(
        session,
        listings=listings,
        snapshots=snapshots,
        runs=FakeRunRepository(),
        fx_rates=FakeFxRepository(),
        fx_client=FakeFxClient(),
    )

    await service.ingest(cast(StoreScraper, FakeScraper([_raw("still-here")])), _store())

    assert listings.off_sale == [(1, ["gone"])]
    assert [listing.store_product_id for listing in listings.upserts] == ["still-here"]
    assert len(snapshots.inserts) == 1
    assert snapshots.inserts[0].listing_id == listings.upserts[0].id
