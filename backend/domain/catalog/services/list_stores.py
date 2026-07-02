from domain.catalog.repositories.store_repository import StoreRepository
from domain.catalog.schemas import StoreRead


async def list_stores(repository: StoreRepository) -> list[StoreRead]:
    stores = await repository.list_active()

    return [StoreRead.model_validate(store) for store in stores]
