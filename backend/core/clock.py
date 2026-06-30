from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    def __init__(self, frozen: datetime) -> None:
        if frozen.tzinfo is None:
            raise ValueError("FrozenClock requires a timezone-aware datetime")

        self._frozen = frozen

    def now(self) -> datetime:
        return self._frozen
