from backend.api.v1.endpoints.auth import router as auth_router
from backend.api.v1.endpoints.employees import router as employees_router
from backend.api.v1.endpoints.health import router as health_router
from backend.api.v1.endpoints.working_time_models import router as working_time_models_router

__all__ = ["health_router", "auth_router", "employees_router", "working_time_models_router"]
