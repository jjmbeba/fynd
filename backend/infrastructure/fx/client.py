from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable


@runtime_checkable
class FxClient(Protocol):
    @property
    def provider_slug(self) -> str: ...

    async def fetch_rate(self, source: str, target: str, on: date) -> Decimal: ...

    async def health_check(self) -> bool: ...
