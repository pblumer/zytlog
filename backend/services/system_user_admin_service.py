from fastapi import HTTPException, status

from backend.models.enums import UserRole
from backend.repositories.system_user_admin_repository import SystemUserAdminRepository
from backend.repositories.tenant_admin_repository import TenantAdminRepository
from backend.schemas.system_user_admin import SystemUserRead, SystemUserUpdate


class SystemUserAdminService:
    def __init__(
        self,
        repository: SystemUserAdminRepository,
        tenant_repository: TenantAdminRepository,
    ) -> None:
        self.repository = repository
        self.tenant_repository = tenant_repository

    def list_users(self) -> list[SystemUserRead]:
        rows = self.repository.list_all_with_employee_status()
        return [
            SystemUserRead(
                id=user.id,
                tenant_id=user.tenant_id,
                email=user.email,
                full_name=user.full_name,
                keycloak_user_id=user.keycloak_user_id,
                role=user.role,
                has_employee_profile=has_employee,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user, has_employee in rows
        ]

    def update_user(self, user_id: int, payload: SystemUserUpdate) -> SystemUserRead:
        user = self.repository.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        target_tenant_id = payload.tenant_id
        if target_tenant_id is not None:
            tenant = self.tenant_repository.get_by_id(target_tenant_id)
            if tenant is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid tenant_id")
            if self.repository.has_employee_profile(user.id) and target_tenant_id != user.tenant_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot reassign tenant for users with an employee profile yet",
                )

        if payload.role == UserRole.SYSTEM_ADMIN and user.role != UserRole.SYSTEM_ADMIN and self.repository.has_employee_profile(user.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot promote users with an employee profile to system_admin",
            )

        updated = self.repository.update(user, tenant_id=payload.tenant_id, role=payload.role)
        return SystemUserRead(
            id=updated.id,
            tenant_id=updated.tenant_id,
            email=updated.email,
            full_name=updated.full_name,
            keycloak_user_id=updated.keycloak_user_id,
            role=updated.role,
            has_employee_profile=self.repository.has_employee_profile(updated.id),
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )
