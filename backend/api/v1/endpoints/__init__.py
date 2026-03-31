from backend.api.v1.endpoints.absences import admin_router as admin_absences_router
from backend.api.v1.endpoints.absences import router as absences_router
from backend.api.v1.endpoints.auth import router as auth_router
from backend.api.v1.endpoints.calendar import router as calendar_router
from backend.api.v1.endpoints.daily_accounts import router as daily_accounts_router
from backend.api.v1.endpoints.employees import router as employees_router
from backend.api.v1.endpoints.exports import router as exports_router
from backend.api.v1.endpoints.health import router as health_router
from backend.api.v1.endpoints.holiday_sets import router as holiday_sets_router
from backend.api.v1.endpoints.holidays import router as holidays_router
from backend.api.v1.endpoints.reports import router as reports_router
from backend.api.v1.endpoints.time_stamps import router as time_stamps_router
from backend.api.v1.endpoints.working_time_models import router as working_time_models_router

__all__ = [
    "absences_router",
    "admin_absences_router",
    "health_router",
    "auth_router",
    "calendar_router",
    "employees_router",
    "holiday_sets_router",
    "holidays_router",
    "exports_router",
    "working_time_models_router",
    "time_stamps_router",
    "daily_accounts_router",
    "reports_router",
]
