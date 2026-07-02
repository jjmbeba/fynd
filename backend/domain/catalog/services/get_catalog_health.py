from domain.catalog.repositories.scrape_run_repository import ScrapeRunRepository
from domain.catalog.schemas import CatalogHealth, StoreScrapeStatus


async def get_catalog_health(repository: ScrapeRunRepository) -> CatalogHealth:
    rows = await repository.latest_runs_with_store()
    stores = [
        StoreScrapeStatus(
            store_slug=store.slug,
            status=run.status,
            listings_observed=run.listings_observed,
            error_message=run.error_message,
            started_at=run.started_at,
            last_scrape_at=run.finished_at,
        )
        for run, store in rows
    ]

    return CatalogHealth(stores=stores)
