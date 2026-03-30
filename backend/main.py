from fastapi import FastAPI

from backend.api.v1.router import router as v1_router
from backend.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.include_router(v1_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    def root_health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
