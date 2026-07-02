from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import Store


class StoreRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_active(self) -> Sequence[Store]:
        statement = select(Store).where(Store.is_active.is_(True)).order_by(Store.slug)

        return (await self._session.execute(statement)).scalars().all()
