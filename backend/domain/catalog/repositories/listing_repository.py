from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import Listing


class ListingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self, *, store_id: int, store_product_id: str, title: str, is_currently_on_sale: bool
    ) -> Listing:
        values = {
            "store_id": store_id,
            "store_product_id": store_product_id,
            "title": title,
            "is_currently_on_sale": is_currently_on_sale,
        }

        upsert = (
            sqlite_insert(Listing)
            .values(values)
            .on_conflict_do_update(
                index_elements=["store_id", "store_product_id"],
                set_={"title": title, "is_currently_on_sale": is_currently_on_sale},
            )
        )

        await self._session.execute(upsert)

        statement = select(Listing).where(
            Listing.store_id == store_id, Listing.store_product_id == store_product_id
        )

        return (await self._session.execute(statement)).scalar_one()
