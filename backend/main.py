from fastapi import FastAPI

from backend.api.v1.router import router as v1_router
from backend.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(v1_router, prefix=settings.api_v1_prefix)
