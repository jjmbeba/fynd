from datetime import UTC, datetime

from domain.catalog.schemas import CatalogHealth, DealRead, FreeGameRead, RefreshStatus, StoreRead


def get_deals_service() -> list[DealRead]:
    return []


def get_free_games_service() -> list[FreeGameRead]:
    return []


def get_stores_service() -> list[StoreRead]:
    return []


def get_refresh_service() -> RefreshStatus:
    return RefreshStatus(started_at=datetime.now(UTC), stores=[])


def get_health_service() -> CatalogHealth:
    return CatalogHealth(stores=[])
