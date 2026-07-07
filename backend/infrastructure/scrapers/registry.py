from infrastructure.scrapers.client import StoreScraper
from infrastructure.scrapers.steam import SteamScraper

_REGISTRY: list[type[StoreScraper]] = [SteamScraper]


def get_active_scrapers() -> list[StoreScraper]:
    instances: list[StoreScraper] = []

    for cls in _REGISTRY:
        try:
            instance = cls()
        except Exception as exc:
            raise ValueError(f"Failed to instantiate {cls.__name__}: {exc}") from exc
        if not isinstance(instance, StoreScraper):
            raise ValueError(f"{cls.__name__} is not a StoreScraper")
        instances.append(instance)
    return instances
