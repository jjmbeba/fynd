import logging
from collections.abc import Sequence
from decimal import Decimal
from typing import ClassVar, TypedDict

from httpx import AsyncClient, HTTPError, codes

from infrastructure.scrapers.client import RawListing, StoreScraper

logger = logging.getLogger(__name__)


class _SteamSpecialItem(TypedDict, total=False):
    id: int
    name: str
    discounted: bool
    discount_percent: int | None
    original_price: int | None
    final_price: int | None
    currency: str
    header_image: str
    large_capsule_image: str


class SteamScraper(StoreScraper):
    BASE_URL: ClassVar[str] = "https://store.steampowered.com/api"
    ENDPOINT: ClassVar[str] = "/featuredcategories"
    LANGUAGE: ClassVar[str] = "en"
    COUNTRY_CODE: ClassVar[str] = "us"
    REQUEST_TIMEOUT: ClassVar[float] = 30.0

    def __init__(self, http_client: AsyncClient | None = None) -> None:
        self._owns_client = http_client is None
        self._client = http_client or AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.REQUEST_TIMEOUT,
            headers={"Accept": "application/json"},
        )

    @property
    def store_slug(self) -> str:
        return "steam"

    async def _fetch_special_items(self) -> list[_SteamSpecialItem]:
        response = await self._client.get(
            self.ENDPOINT, params={"cc": self.COUNTRY_CODE, "l": self.LANGUAGE}
        )
        response.raise_for_status()
        payload = response.json()
        specials = payload.get("specials") or {}
        return list(specials.get("items") or [])

    async def fetch_current_sales(self) -> Sequence[RawListing]:
        items = await self._fetch_special_items()

        return [self._to_listing(item) for item in items if self._is_on_sale(item)]

    async def fetch_free_games(self) -> Sequence[RawListing]:
        items = await self._fetch_special_items()

        return [self._to_listing(item) for item in items if self._is_free_item(item)]

    async def health_check(self) -> bool:
        try:
            response = await self._client.get(
                self.ENDPOINT, params={"cc": self.COUNTRY_CODE, "l": self.LANGUAGE}
            )
            return response.status_code == codes.OK
        except HTTPError as exc:
            logger.warning("Steam health check failed", extra={"error": str(exc)})

            return False

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    @staticmethod
    def _is_on_sale(item: _SteamSpecialItem) -> bool:
        if item.get("id") is None or item.get("name") is None:
            return False
        if not item.get("discounted"):
            return False

        if item.get("original_price") in (None, 0):
            return False

        discount = item.get("discount_percent")

        return discount is not None and 0 < discount < 100

    @staticmethod
    def _is_free_item(item: _SteamSpecialItem) -> bool:
        if item.get("id") is None or item.get("name") is None:
            return False
        return item.get("discount_percent") == 100

    @staticmethod
    def _to_listing(item: _SteamSpecialItem) -> RawListing:
        return RawListing(
            store_product_id=str(item["id"]),
            title=item["name"],
            currency=item.get("currency") or "USD",
            base_amount=Decimal(int(item.get("original_price") or 0)) / 100,
            native_amount=Decimal(int(item.get("final_price") or 0)) / 100,
            discount_percent=item.get("discount_percent"),
            is_free=item.get("discount_percent") == 100,
            image_url=item.get("header_image") or item.get("large_capsule_image"),
        )
