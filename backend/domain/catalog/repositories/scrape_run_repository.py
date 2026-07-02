from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import ScrapeRun, Store
from domain.catalog.repositories._latest_per_group import latest_per_group_subquery


class ScrapeRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def latest_runs_with_store(self) -> Sequence[tuple[ScrapeRun, Store]]:
        latest_sq = latest_per_group_subquery(ScrapeRun.store_id, ScrapeRun.started_at)
        statement = (
            select(ScrapeRun, Store)
            .join(
                latest_sq,
                (ScrapeRun.store_id == latest_sq.c.group_id)
                & (ScrapeRun.started_at == latest_sq.c.latest),
            )
            .join(Store, ScrapeRun.store_id == Store.id)
            .order_by(Store.slug)
        )
        return (await self._session.execute(statement)).tuples().all()
