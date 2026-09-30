from collections.abc import Sequence
from decimal import Decimal

from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.schemas import DealRead


class DealsService:
    def __init__(self, repository: PriceSnapshotRepository) -> None:
        self._repository = repository

    async def list(
        self,
        *,
        store_slugs: Sequence[str] | None = None,
        max_kes_price: Decimal | None = None,
        min_discount_percent: int | None = None,
        query: str | None = None,
    ) -> list[DealRead]:
        rows = await self._repository.latest_sales_with_listing(
            store_slugs=store_slugs,
            max_kes_price=max_kes_price,
            min_discount_percent=min_discount_percent,
            query=query,
        )
        return [
            DealRead(
                title=listing.title,
                listing_id=listing.id,
                image_url=listing.image_url,
                store_slug=store.slug,
                store_display_name=store.display_name,
                base_amount=snapshot.base_amount,
                native_amount=snapshot.native_amount,
                kes_amount=snapshot.kes_amount,
                currency=snapshot.currency,
                discount_percent=snapshot.discount_percent,
                observed_at=snapshot.observed_at,
            )
            for snapshot, listing, store in rows
        ]
