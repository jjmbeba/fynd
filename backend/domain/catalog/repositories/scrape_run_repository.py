from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import ScrapeRun, ScrapeStatus, Store
from domain.catalog.repositories._latest_per_group import latest_per_group_subquery


class ScrapeRunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, store_id: int) -> ScrapeRun:
        run = ScrapeRun(store_id=store_id, status=ScrapeStatus.RUNNING)

        self._session.add(run)
        await self._session.flush()

        return run

    async def complete(
        self, *, run_id: int, listings_observed: int, error_message: str | None = None
    ) -> None:
        run = await self._session.get(ScrapeRun, run_id)
        if run is None:
            return

        run.status = ScrapeStatus.ERROR if error_message else ScrapeStatus.SUCCESS
        run.finished_at = datetime.now(UTC)
        run.listings_observed = listings_observed
        run.error_message = error_message

        await self._session.flush()

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
