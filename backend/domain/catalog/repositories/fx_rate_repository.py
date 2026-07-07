from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from domain.catalog.models import FxRate


class FxRateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_date(self, *, source: str, on: date) -> FxRate | None:
        observed_at = datetime.combine(on, datetime.min.time())
        statement = select(FxRate).where(
            FxRate.source_currency == source,
            FxRate.date == observed_at,
        )
        return (await self._session.execute(statement)).scalar_one_or_none()

    async def upsert(self, *, source: str, on: date, rate: Decimal) -> FxRate:
        observed_at = datetime.combine(on, datetime.min.time())
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
