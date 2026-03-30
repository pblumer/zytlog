from fastapi import APIRouter

from backend.api.v1.endpoints import (
    auth_router,
    daily_accounts_router,
    employees_router,
    exports_router,
    health_router,
    reports_router,
    time_stamps_router,
    working_time_models_router,
)

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router)
router.include_router(employees_router)
router.include_router(exports_router)
router.include_router(working_time_models_router)
router.include_router(time_stamps_router)
router.include_router(daily_accounts_router)

router.include_router(reports_router)
