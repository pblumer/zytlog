from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models.enums import UserRole
from backend.models.user import User
from backend.repositories.tenant_repository import TenantRepository
from backend.repositories.user_repository import UserRepository

DEFAULT_PROVISIONING_TENANT_SLUG = "demo-co"


class UserProvisioningService:
    def __init__(self, db: Session) -> None:
        self.user_repository = UserRepository(db)
        self.tenant_repository = TenantRepository(db)

    def create_user_from_token(
        self,
        *,
        sub: str,
        email: str | None,
        preferred_username: str | None,
    ) -> User:
        resolved_email = email or preferred_username
        if not resolved_email:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token is missing both email and preferred_username for provisioning",
            )

        default_tenant = self.tenant_repository.get_by_slug(DEFAULT_PROVISIONING_TENANT_SLUG)
        if default_tenant is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default provisioning tenant 'demo-co' was not found",
            )

        return self.user_repository.create(
            tenant_id=default_tenant.id,
            keycloak_user_id=sub,
            email=resolved_email,
            full_name=preferred_username or resolved_email,
            role=UserRole.EMPLOYEE,
        )
