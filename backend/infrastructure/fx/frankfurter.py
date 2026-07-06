import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import ClassVar, TypedDict

from httpx import AsyncClient, HTTPError, codes

logger = logging.getLogger(__name__)


class _FrankfurterResponse(TypedDict, total=False):
    amount: float
    base: str
    date: str
    rates: dict[str, float]


class FrankfurterClient:
    BASE_URL: ClassVar[str] = "https://api.frankfurter.app"
    REQUEST_TIMEOUT: ClassVar[float] = 30.0

    def __init__(self, http_client: AsyncClient | None = None) -> None:
        self._owns_client = http_client is None
        self._client = http_client or AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.REQUEST_TIMEOUT,
            headers={"Accept": "application/json"},
        )

    @property
    def provider_slug(self) -> str:
        return "frankfurter"

    async def fetch_rate(self, source: str, target: str, on: date) -> Decimal:
        endpoint = "latest" if on >= datetime.now(UTC).date() else on.isoformat()
        response = await self._client.get(endpoint, params={"from": source, "to": target})

        response.raise_for_status()
        payload: _FrankfurterResponse = response.json()

        rates = payload.get("rates") or {}
        rate = rates.get(target)

        if rate is None:
            raise ValueError(f"Frankfurter response missing rate for {target}")

        return Decimal(str(rate))

    async def health_check(self) -> bool:
        try:
            response = await self._client.get("currencies")
            return response.status_code == codes.OK
        except HTTPError as exc:
            logger.warning("Frankfurter health check failed", extra={"error": str(exc)})
            return False

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()
