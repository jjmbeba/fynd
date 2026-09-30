from collections.abc import Sequence

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import Listing


class ListingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        *,
        store_id: int,
        store_product_id: str,
        title: str,
        image_url: str | None,
        is_currently_on_sale: bool,
    ) -> Listing:
        values = {
            "store_id": store_id,
            "store_product_id": store_product_id,
            "title": title,
            "image_url": image_url,
            "is_currently_on_sale": is_currently_on_sale,
        }

        upsert = (
            sqlite_insert(Listing)
            .values(values)
            .on_conflict_do_update(
                index_elements=["store_id", "store_product_id"],
                set_={
                    "title": title,
                    "image_url": image_url,
                    "is_currently_on_sale": is_currently_on_sale,
                },
            )
        )

        await self._session.execute(upsert)

        statement = select(Listing).where(
            Listing.store_id == store_id, Listing.store_product_id == store_product_id
        )

        return (await self._session.execute(statement)).scalar_one()

    async def list_on_sale_product_ids(self, *, store_id: int) -> Sequence[str]:
        statement = select(Listing.store_product_id).where(
            Listing.store_id == store_id,
            Listing.is_currently_on_sale.is_(True),
        )
        return (await self._session.execute(statement)).scalars().all()

    async def mark_off_sale(self, *, store_id: int, store_product_ids: Sequence[str]) -> None:
        if not store_product_ids:
            return

        statement = (
            update(Listing)
            .where(
                Listing.store_id == store_id,
                Listing.store_product_id.in_(list(store_product_ids)),
            )
            .values(is_currently_on_sale=False)
        )
        await self._session.execute(statement)
