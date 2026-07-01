from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class ScrapeStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)

    slug: Mapped[str] = mapped_column(String(32), unique=True)
    display_name: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Listing(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"))
    store_product_id: Mapped[str] = mapped_column(String(64))

    title: Mapped[str] = mapped_column(String(255))
    is_currently_on_sale: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = UniqueConstraint(
        "store_id", "store_product_id", name="uq_listings_store_product"
    )


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)

    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), index=True)

    base_amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    native_amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    kes_amount: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))

    currency: Mapped[str] = mapped_column(String(3))

    discount_percent: Mapped[int | None] = mapped_column(Integer)

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class FxRate(Base):
    __tablename__ = "fx_rates"

    id: Mapped[int] = mapped_column(primary_key=True)

    source_currency: Mapped[str] = mapped_column(String(3))
    rate_to_kes: Mapped[Decimal] = mapped_column(Numeric(precision=18, scale=8))
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = UniqueConstraint("date", "source_currency", name="uq_fx_rates_date_source")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id: Mapped[int] = mapped_column(primary_key=True)

    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id"), index=True)
    status: Mapped[ScrapeStatus] = mapped_column(
        Enum(ScrapeStatus, native_enum=False, length=16), default=ScrapeStatus.RUNNING
    )

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    listings_observed: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(String(2048))
