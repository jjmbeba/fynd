from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol, runtime_checkable

__all__ = ["RawListing", "StoreScraper"]


@dataclass(frozen=True, slots=True)
class RawListing:
    """A single observation from a storefront, in the store's own shape.

    This is the wire format. The domain converts it to ORM rows.
    All prices are in the store's own currency, already converted from
    whatever sub-unit the store uses (cents for Steam, etc.) into a
    Decimal of the major unit.
    """

    store_product_id: str
    title: str
    currency: str
    base_amount: Decimal
    native_amount: Decimal
    discount_percent: int | None
    is_free: bool
    image_url: str | None = None


@runtime_checkable
class StoreScraper(Protocol):
    """The Agnostic Scraper Interface.

    Every concrete storefront implementation fulfils this Protocol.
    The registry verifies conformance at import time via isinstance.
    """

    @property
    def store_slug(self) -> str: ...

    async def fetch_current_sales(self) -> Sequence[RawListing]: ...

    async def fetch_free_games(self) -> Sequence[RawListing]: ...

    async def health_check(self) -> bool: ...

    async def aclose(self) -> None: ...
