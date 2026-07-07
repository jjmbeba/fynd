from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import Store


class StoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> Sequence[Store]:
        statement = select(Store).where(Store.is_active.is_(True)).order_by(Store.slug)

        return (await self._session.execute(statement)).scalars().all()

    async def upsert_by_slug(self, *, slug: str, display_name: str) -> Store:
        values = {"slug": slug, "display_name": display_name, "is_active": True}

        upsert = (
            sqlite_insert(Store)
            .values(values)
            .on_conflict_do_update(
                index_elements=["slug"], set_={"display_name": display_name, "is_active": True}
            )
            .returning(Store)
        )

        return (await self._session.execute(upsert)).scalar_one()
