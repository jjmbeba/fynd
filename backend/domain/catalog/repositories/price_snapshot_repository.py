from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import Listing, PriceSnapshot, Store
from domain.catalog.repositories._latest_per_group import latest_per_group_subquery


def _contains_pattern(query: str) -> str:
    escaped = query.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


class PriceSnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        snapshot = PriceSnapshot(
            listing_id=listing_id,
            base_amount=base_amount,
            native_amount=native_amount,
            kes_amount=kes_amount,
            currency=currency,
            discount_percent=discount_percent,
            observed_at=observed_at,
        )

        self._session.add(snapshot)
        await self._session.flush()

        return snapshot

    def _latest_with_listing_query(self) -> Any:
        """Return a base query that selects latest PriceSnapshot + Listing + Store join."""
        latest_sq = latest_per_group_subquery(PriceSnapshot.listing_id, PriceSnapshot.observed_at)
        return (
            select(PriceSnapshot, Listing, Store)
            .join(
                latest_sq,
                (PriceSnapshot.listing_id == latest_sq.c.group_id)
                & (PriceSnapshot.observed_at == latest_sq.c.latest),
            )
            .join(Listing, PriceSnapshot.listing_id == Listing.id)
            .join(Store, Listing.store_id == Store.id)
        )

    async def latest_sales_with_listing(
        self,
        *,
        store_slugs: Sequence[str] | None = None,
        max_kes_price: Decimal | None = None,
        min_discount_percent: int | None = None,
        query: str | None = None,
    ) -> Sequence[tuple[PriceSnapshot, Listing, Store]]:
        statement = self._latest_with_listing_query().where(Listing.is_currently_on_sale.is_(True))

        if store_slugs:
            statement = statement.where(Store.slug.in_(list(store_slugs)))
        if max_kes_price is not None:
            statement = statement.where(PriceSnapshot.kes_amount <= max_kes_price)
        if min_discount_percent is not None:
            statement = statement.where(PriceSnapshot.discount_percent >= min_discount_percent)
        if query and query.strip():
            statement = statement.where(Listing.title.ilike(_contains_pattern(query), escape="\\"))

        savings = PriceSnapshot.base_amount - PriceSnapshot.native_amount
        statement = statement.order_by(savings.desc(), Listing.id.asc())
        return (await self._session.execute(statement)).tuples().all()

    async def latest_free_games_with_listing(
        self,
    ) -> Sequence[tuple[PriceSnapshot, Listing, Store]]:
        statement = (
            self._latest_with_listing_query()
            .where(PriceSnapshot.discount_percent == 100)
            .order_by(PriceSnapshot.observed_at.desc())
        )
        return (await self._session.execute(statement)).tuples().all()
