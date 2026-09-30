from domain.catalog.repositories.price_snapshot_repository import PriceSnapshotRepository
from domain.catalog.schemas import FreeGameRead


class FreeGamesService:
    def __init__(self, repository: PriceSnapshotRepository) -> None:
        self._repository = repository

    async def list(self) -> list[FreeGameRead]:
        rows = await self._repository.latest_free_games_with_listing()
        return [
            FreeGameRead(
                title=listing.title,
                listing_id=listing.id,
                image_url=listing.image_url,
                store_slug=store.slug,
                store_display_name=store.display_name,
                currency=snapshot.currency,
                base_amount=snapshot.base_amount,
                observed_at=snapshot.observed_at,
            )
            for snapshot, listing, store in rows
        ]
