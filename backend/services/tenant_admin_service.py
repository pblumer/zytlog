from fastapi import HTTPException, status

from backend.repositories.tenant_admin_repository import TenantAdminRepository
from backend.schemas.tenant_admin import TenantCreate, TenantUpdate


class TenantAdminService:
    def __init__(self, repository: TenantAdminRepository) -> None:
        self.repository = repository

    def list_tenants(self):
        return self.repository.list_all()

    def create_tenant(self, payload: TenantCreate):
        existing = self.repository.get_by_slug(payload.slug)
        if existing is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant slug already exists")
        return self.repository.create(payload)

    def update_tenant(self, tenant_id: int, payload: TenantUpdate):
        tenant = self.repository.get_by_id(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

        if payload.slug is not None and payload.slug != tenant.slug:
            existing = self.repository.get_by_slug(payload.slug)
            if existing is not None and existing.id != tenant.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant slug already exists")

        return self.repository.update(tenant, payload)
