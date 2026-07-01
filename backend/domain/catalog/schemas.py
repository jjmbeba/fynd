from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from domain.catalog.models import ScrapeStatus


class ErrorResponse(BaseModel):
    detail: str


class StoreRead(BaseModel):
    id: int
    slug: str
    display_name: str
    is_active: bool

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DealRead(BaseModel):
    title: str
    listing_id: int

    store_slug: str
    store_display_name: str

    base_amount: Decimal
    native_amount: Decimal
    kes_amount: Decimal
    currency: str

    discount_percent: int | None

    observed_at: datetime


class FreeGameRead(BaseModel):
    title: str
    listing_id: int

    store_slug: str
    store_display_name: str

    currency: str
    base_amount: Decimal | None

    observed_at: datetime


class StoreScrapeStatus(BaseModel):
    store_slug: str
    status: ScrapeStatus
    listings_observed: int
    error_message: str | None

    started_at: datetime
    last_scrape_at: datetime | None


class RefreshStatus(BaseModel):
    started_at: datetime
    stores: list[StoreScrapeStatus]


class CatalogHealth(BaseModel):
    stores: list[StoreScrapeStatus]
