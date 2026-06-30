import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)},
    )


async def infrastructure_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Infrastructure error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "Upstream service unavailable"},
    )
