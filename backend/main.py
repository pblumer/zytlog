from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.router import router as v1_router
from backend.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://pi-server-03.home:5173",
            "http://192.168.1.203:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["system"])
    def root_health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
