from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.schemas import DealRead


async def list_deals(repository: PriceSnapshotRepository) -> list[DealRead]:
    rows = await repository.latest_sales_with_listing()

    return [
        DealRead(
            title=listing.title,
            listing_id=listing.id,
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
