from datetime import UTC, datetime
from decimal import Decimal

import httpx
import respx

from infrastructure.fx.frankfurter import FrankfurterClient


async def test_fetch_rate_follows_redirect_to_frankfurter_v2() -> None:
    today = datetime.now(UTC).date()
    with respx.mock:
        respx.get("https://api.frankfurter.dev/v2/rate/USD/KES").mock(
            return_value=httpx.Response(
                301,
                headers={"location": "https://api.frankfurter.dev/v2/rate/USD/KES/current"},
            )
        )
        respx.get("https://api.frankfurter.dev/v2/rate/USD/KES/current").mock(
            return_value=httpx.Response(
                200,
                json={"date": today.isoformat(), "base": "USD", "quote": "KES", "rate": "129.12"},
            )
        )
        client = FrankfurterClient()
        try:
            rate = await client.fetch_rate("USD", "KES", today)
        finally:
            await client.aclose()

    assert rate == Decimal("129.12")
