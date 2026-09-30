from datetime import UTC, datetime
from decimal import Decimal

from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker

from domain.catalog.dependencies import get_scraping_service
from domain.catalog.models import Listing, PriceSnapshot, ScrapeRun, ScrapeStatus, Store
from domain.catalog.schemas import RefreshStatus, StoreScrapeStatus


async def _seed(app: FastAPI) -> None:
    maker = async_sessionmaker(app.state.engine, expire_on_commit=False)
    observed = datetime(2026, 6, 1, tzinfo=UTC)
    async with maker() as session:
        store = Store(slug="steam", display_name="Steam", is_active=True)
        session.add(store)
        await session.flush()

        deal = Listing(
            store_id=store.id,
            store_product_id="hades",
            title="Hades",
            is_currently_on_sale=True,
        )
        free = Listing(
            store_id=store.id,
            store_product_id="freebie",
            title="Freebie",
            is_currently_on_sale=False,
        )
        session.add_all([deal, free])
        await session.flush()

        session.add_all(
            [
                PriceSnapshot(
                    listing_id=deal.id,
                    base_amount=Decimal("20"),
                    native_amount=Decimal("10"),
                    kes_amount=Decimal("1300"),
                    currency="USD",
                    discount_percent=50,
                    observed_at=observed,
                ),
                PriceSnapshot(
                    listing_id=free.id,
                    base_amount=Decimal("15"),
                    native_amount=Decimal("0"),
                    kes_amount=Decimal("0"),
                    currency="USD",
                    discount_percent=100,
                    observed_at=observed,
                ),
                ScrapeRun(
                    store_id=store.id,
                    status=ScrapeStatus.SUCCESS,
                    started_at=observed,
                    finished_at=observed,
                    listings_observed=2,
                ),
            ]
        )
        await session.commit()


async def test_list_stores(client: AsyncClient, app: FastAPI) -> None:
    await _seed(app)

    response = await client.get("/api/v1/catalog/stores")

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "steam"


async def test_list_deals(client: AsyncClient, app: FastAPI) -> None:
    await _seed(app)

    response = await client.get(
        "/api/v1/catalog/deals",
        params={
            "store": "steam",
            "max_kes_price": "2000",
            "min_discount_percent": 40,
            "q": "Hades",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body[0]["title"] == "Hades"
    assert Decimal(body[0]["kes_amount"]) == Decimal("1300")

    missed = await client.get("/api/v1/catalog/deals", params={"q": "Nope"})
    assert missed.status_code == 200
    assert missed.json() == []


async def test_list_free_games(client: AsyncClient, app: FastAPI) -> None:
    await _seed(app)

    response = await client.get("/api/v1/catalog/free-games")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Freebie"


async def test_catalog_health(client: AsyncClient, app: FastAPI) -> None:
    await _seed(app)

    response = await client.get("/api/v1/catalog/health")

    assert response.status_code == 200
    store = response.json()["stores"][0]
    assert store["store_slug"] == "steam"
    assert store["status"] == "success"
    assert store["listings_observed"] == 2


async def test_trigger_refresh(client: AsyncClient, app: FastAPI) -> None:
    started = datetime(2026, 6, 1, tzinfo=UTC)

    class _Scraping:
        async def run_all(self) -> RefreshStatus:
            return RefreshStatus(
                started_at=started,
                stores=[
                    StoreScrapeStatus(
                        store_slug="steam",
                        status=ScrapeStatus.SUCCESS,
                        listings_observed=2,
                        error_message=None,
                        started_at=started,
                        last_scrape_at=started,
                    )
                ],
            )

    app.dependency_overrides[get_scraping_service] = lambda: _Scraping()

    response = await client.post("/api/v1/catalog/refresh")

    assert response.status_code == 200
    assert response.json()["stores"][0]["store_slug"] == "steam"
    assert response.json()["stores"][0]["listings_observed"] == 2
