from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import Listing, PriceSnapshot, Store
from domain.catalog.repositories._latest_per_group import latest_per_group_subquery


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

    async def latest_sales_with_listing(
        self,
    ) -> Sequence[tuple[PriceSnapshot, Listing, Store]]:
        latest_sq = latest_per_group_subquery(PriceSnapshot.listing_id, PriceSnapshot.observed_at)
        statement = (
            select(PriceSnapshot, Listing, Store)
            .join(
                latest_sq,
                (PriceSnapshot.listing_id == latest_sq.c.group_id)
                & (PriceSnapshot.observed_at == latest_sq.c.latest),
            )
            .join(Listing, PriceSnapshot.listing_id == Listing.id)
            .join(Store, Listing.store_id == Store.id)
            .where(Listing.is_currently_on_sale.is_(True))
            .order_by(PriceSnapshot.kes_amount)
        )
        return (await self._session.execute(statement)).tuples().all()

    async def latest_free_games_with_listing(
        self,
    ) -> Sequence[tuple[PriceSnapshot, Listing, Store]]:
        latest_sq = latest_per_group_subquery(PriceSnapshot.listing_id, PriceSnapshot.observed_at)
        statement = (
            select(PriceSnapshot, Listing, Store)
            .join(
                latest_sq,
                (PriceSnapshot.listing_id == latest_sq.c.group_id)
                & (PriceSnapshot.observed_at == latest_sq.c.latest),
            )
            .join(Listing, PriceSnapshot.listing_id == Listing.id)
            .join(Store, Listing.store_id == Store.id)
            .where(PriceSnapshot.discount_percent == 100)
            .order_by(PriceSnapshot.observed_at.desc())
        )
        return (await self._session.execute(statement)).tuples().all()
