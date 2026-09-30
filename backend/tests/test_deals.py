import shutil
import tempfile
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.database import Base, build_engine
from domain.catalog.models import Listing, PriceSnapshot, Store
from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.services.deals import DealsService


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


async def _seed(session: AsyncSession) -> None:
    steam = Store(slug="steam", display_name="Steam", is_active=True)
    epic = Store(slug="epic", display_name="Epic", is_active=True)
    session.add_all([steam, epic])
    await session.flush()

    hades = Listing(
        store_id=steam.id,
        store_product_id="hades",
        title="Hades",
        is_currently_on_sale=True,
    )
    celeste = Listing(
        store_id=steam.id,
        store_product_id="celeste",
        title="Celeste",
        is_currently_on_sale=True,
    )
    control = Listing(
        store_id=epic.id,
        store_product_id="control",
        title="Control",
        is_currently_on_sale=True,
    )
    retired = Listing(
        store_id=steam.id,
        store_product_id="retired",
        title="Retired",
        is_currently_on_sale=False,
    )
    session.add_all([hades, celeste, control, retired])
    await session.flush()

    observed = datetime(2026, 6, 1, tzinfo=UTC)
    session.add_all(
        [
            PriceSnapshot(
                listing_id=hades.id,
                base_amount=Decimal("20"),
                native_amount=Decimal("19"),
                kes_amount=Decimal("1"),
                currency="USD",
                discount_percent=5,
                observed_at=observed - timedelta(days=1),
            ),
            PriceSnapshot(
                listing_id=hades.id,
                base_amount=Decimal("20"),
                native_amount=Decimal("10"),
                kes_amount=Decimal("1300"),
                currency="USD",
                discount_percent=50,
                observed_at=observed,
            ),
            PriceSnapshot(
                listing_id=celeste.id,
                base_amount=Decimal("10"),
                native_amount=Decimal("8"),
                kes_amount=Decimal("1040"),
                currency="USD",
                discount_percent=20,
                observed_at=observed,
            ),
            PriceSnapshot(
                listing_id=control.id,
                base_amount=Decimal("40"),
                native_amount=Decimal("10"),
                kes_amount=Decimal("5200"),
                currency="USD",
                discount_percent=75,
                observed_at=observed,
            ),
            PriceSnapshot(
                listing_id=retired.id,
                base_amount=Decimal("60"),
                native_amount=Decimal("10"),
                kes_amount=Decimal("1300"),
                currency="USD",
                discount_percent=80,
                observed_at=observed,
            ),
        ]
    )
    await session.flush()


async def test_deals_filter_and_sort_by_absolute_savings(session: AsyncSession) -> None:
    await _seed(session)
    service = DealsService(PriceSnapshotRepository(session))

    deals = await service.list()
    assert [deal.title for deal in deals] == ["Control", "Hades", "Celeste"]
    assert deals[1].kes_amount == Decimal("1300")

    steam = await service.list(store_slugs=["steam"])
    assert [deal.title for deal in steam] == ["Hades", "Celeste"]

    affordable = await service.list(max_kes_price=Decimal("2000"))
    assert [deal.title for deal in affordable] == ["Hades", "Celeste"]

    deep = await service.list(min_discount_percent=50)
    assert [deal.title for deal in deep] == ["Control", "Hades"]

    searched = await service.list(query="hades")
    assert [deal.title for deal in searched] == ["Hades"]


async def test_search_escapes_like_wildcards(session: AsyncSession) -> None:
    steam = Store(slug="steam", display_name="Steam", is_active=True)
    session.add(steam)
    await session.flush()

    observed = datetime(2026, 6, 1, tzinfo=UTC)
    titles = ("100% Off", "A_B", "Hades")
    for title in titles:
        listing = Listing(
            store_id=steam.id,
            store_product_id=title,
            title=title,
            is_currently_on_sale=True,
        )
        session.add(listing)
        await session.flush()
        session.add(
            PriceSnapshot(
                listing_id=listing.id,
                base_amount=Decimal("10"),
                native_amount=Decimal("5"),
                kes_amount=Decimal("650"),
                currency="USD",
                discount_percent=50,
                observed_at=observed,
            )
        )
    await session.flush()

    service = DealsService(PriceSnapshotRepository(session))
    assert [deal.title for deal in await service.list(query="%")] == ["100% Off"]
    assert [deal.title for deal in await service.list(query="_")] == ["A_B"]
