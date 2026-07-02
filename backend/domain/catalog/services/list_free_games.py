from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.schemas import FreeGameRead


async def list_free_games(repository: PriceSnapshotRepository) -> list[FreeGameRead]:
    rows = await repository.latest_free_games_with_listing()

    return [
        FreeGameRead(
            title=listing.title,
            listing_id=listing.id,
            store_slug=store.slug,
            store_display_name=store.display_name,
            currency=snapshot.currency,
            base_amount=snapshot.base_amount,
            observed_at=snapshot.observed_at,
        )
        for snapshot, listing, store in rows
    ]
