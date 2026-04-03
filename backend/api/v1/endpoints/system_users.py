from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_system_admin
from backend.repositories.system_user_admin_repository import SystemUserAdminRepository
from backend.repositories.tenant_admin_repository import TenantAdminRepository
from backend.schemas.system_user_admin import SystemUserRead, SystemUserUpdate
from backend.services.system_user_admin_service import SystemUserAdminService

router = APIRouter(prefix="/system/users", tags=["system-users"])


def _service(db: Session) -> SystemUserAdminService:
    return SystemUserAdminService(SystemUserAdminRepository(db), TenantAdminRepository(db))


@router.get("", response_model=list[SystemUserRead])
def list_system_users(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_system_admin),
) -> list[SystemUserRead]:
    return _service(db).list_users()


@router.patch("/{user_id}", response_model=SystemUserRead)
def update_system_user(
    user_id: int,
    payload: SystemUserUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_system_admin),
) -> SystemUserRead:
    return _service(db).update_user(user_id, payload)
