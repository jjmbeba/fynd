from fastapi import FastAPI

from api.exception_handlers import domain_error_handler, infrastructure_error_handler
from api.lifespan import lifespan
from core.config import Settings, get_settings
from core.exceptions import DomainError, InfrastructureError


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(title="Fynd", lifespan=lifespan)
    app.state.settings = settings or get_settings()

    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(InfrastructureError, infrastructure_error_handler)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "Hello World"}

    return app


app = create_app()
