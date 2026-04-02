from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_system_admin
from backend.repositories.tenant_admin_repository import TenantAdminRepository
from backend.schemas.tenant_admin import TenantAdminRead, TenantCreate, TenantUpdate
from backend.services.tenant_admin_service import TenantAdminService

router = APIRouter(prefix="/system/tenants", tags=["system-tenants"])


def _service(db: Session) -> TenantAdminService:
    return TenantAdminService(TenantAdminRepository(db))


@router.get("", response_model=list[TenantAdminRead])
def list_tenants(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_system_admin),
) -> list[TenantAdminRead]:
    return [TenantAdminRead.model_validate(row) for row in _service(db).list_tenants()]


@router.post("", response_model=TenantAdminRead)
def create_tenant(
    payload: TenantCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_system_admin),
) -> TenantAdminRead:
    created = _service(db).create_tenant(payload)
    return TenantAdminRead.model_validate(created)


@router.patch("/{tenant_id}", response_model=TenantAdminRead)
def update_tenant(
    tenant_id: int,
    payload: TenantUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_system_admin),
) -> TenantAdminRead:
    updated = _service(db).update_tenant(tenant_id, payload)
    return TenantAdminRead.model_validate(updated)
