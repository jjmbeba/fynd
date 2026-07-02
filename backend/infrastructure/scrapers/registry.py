from infrastructure.scrapers.client import StoreScraper
from infrastructure.scrapers.steam import SteamScraper

_REGISTRY: list[type[StoreScraper]] = [SteamScraper]


def get_active_scrapers() -> list[StoreScraper]:
    return [cls() for cls in _REGISTRY]
