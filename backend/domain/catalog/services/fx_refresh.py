import logging

from sqlalchemy.ext.asyncio import AsyncSession

from core.clock import Clock, SystemClock
from domain.catalog.repositories.fx_rate_repository import FxRateRepository
from infrastructure.fx.client import FxClient

logger = logging.getLogger(__name__)

TRACKED_CURRENCIES = ("USD", "EUR", "GBP")


class FxRefreshService:
    def __init__(
        self,
        *,
        fx_repository: FxRateRepository,
        fx_client: FxClient,
        clock: Clock | None = None,
    ) -> None:
        self._rates = fx_repository
        self._fx_client = fx_client
        self._clock = clock or SystemClock()

    async def refresh(self) -> None:
        today = self._clock.now().date()

        for source in TRACKED_CURRENCIES:
            if await self._rates.get_by_date(source=source, on=today) is not None:
                continue

            try:
                rate = await self._fx_client.fetch_rate(source=source, target="KES", on=today)
            except Exception:
                logger.warning(
                    "FX refresh failed",
                    extra={"source": source, "target": "KES"},
                    exc_info=True,
                )
                continue

            await self._rates.upsert(source=source, rate=rate, on=today)


def build_fx_refresh_service(
    *,
    session: AsyncSession,
    fx_client: FxClient,
    clock: Clock | None = None,
) -> FxRefreshService:
    return FxRefreshService(
        fx_repository=FxRateRepository(session),
        fx_client=fx_client,
        clock=clock,
    )
