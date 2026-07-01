from fastapi import APIRouter

from domain.catalog import router as catalog_router

router = APIRouter(prefix="/api/v1")
router.include_router(catalog_router)
