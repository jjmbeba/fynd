from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import FxRate
from infrastructure.fx.client import FxClient


class FxRateRepository:
    def __init__(self, session: AsyncSession, fx_client: FxClient) -> None:
        self._session = session
        self._fx_client = fx_client

    async def get_or_fetch(self, *, source: str, on: date) -> FxRate:
        observed_at = datetime.combine(on, datetime.min.time())

        cached = await self._fetch_cached(source, observed_at)

        if cached is not None:
            return cached

        rate: Decimal = await self._fx_client.fetch_rate(source=source, target="KES", on=on)

        return await self._insert(source=source, rate=rate, observed_at=observed_at)

    async def _fetch_cached(self, source: str, observed_at: datetime) -> FxRate | None:
        statement = select(FxRate).where(
            FxRate.source_currency == source,
            FxRate.date == observed_at,
        )

        return (await self._session.execute(statement)).scalar_one_or_none()

    async def _insert(self, *, source: str, observed_at: datetime, rate: Decimal) -> FxRate:
        values = {"source_currency": source, "date": observed_at, "rate_to_kes": rate}

        upsert = (
            sqlite_insert(FxRate)
            .values(values)
            .on_conflict_do_update(
                index_elements=["date", "source_currency"], set_={"rate_to_kes": rate}
            )
        )

        await self._session.execute(upsert)

        statement = select(FxRate).where(
            FxRate.source_currency == source, FxRate.date == observed_at
        )

        return (await self._session.execute(statement)).scalar_one()
