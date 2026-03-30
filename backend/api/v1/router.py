from fastapi import APIRouter

from backend.api.v1.endpoints import auth_router, employees_router, health_router, working_time_models_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(employees_router)
router.include_router(working_time_models_router)
