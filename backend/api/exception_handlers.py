from fastapi import Request, status
from fastapi.responses import JSONResponse


async def domain_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)})


async def infrastructure_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": str(exc)})
