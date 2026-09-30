from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

CatalogJob = Callable[[], Awaitable[None]]


class AppScheduler:
    def __init__(self) -> None:
        self._scheduler = AsyncIOScheduler()

    def start(self, daily_refresh: CatalogJob, hour: int) -> None:
        self._scheduler.add_job(
            daily_refresh,
            CronTrigger(hour=hour, minute=0),
            id="daily_refresh",
            replace_existing=True,
            coalesce=True,
        )
        self._scheduler.start()

    def stop(self) -> None:
        self._scheduler.shutdown(wait=False)
