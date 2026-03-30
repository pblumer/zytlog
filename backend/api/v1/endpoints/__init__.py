from backend.api.v1.endpoints.auth import router as auth_router
from backend.api.v1.endpoints.daily_accounts import router as daily_accounts_router
from backend.api.v1.endpoints.employees import router as employees_router
from backend.api.v1.endpoints.health import router as health_router
from backend.api.v1.endpoints.reports import router as reports_router
from backend.api.v1.endpoints.time_stamps import router as time_stamps_router
from backend.api.v1.endpoints.working_time_models import router as working_time_models_router

__all__ = [
    "health_router",
    "auth_router",
    "employees_router",
    "working_time_models_router",
    "time_stamps_router",
    "daily_accounts_router",
    "reports_router",
]
