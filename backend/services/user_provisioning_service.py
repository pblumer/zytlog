from fastapi import HTTPException, status
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.enums import UserRole
from backend.models.user import User
from backend.repositories.tenant_repository import TenantRepository
from backend.repositories.user_repository import UserRepository

DEFAULT_PROVISIONING_TENANT_SLUG = "demo-co"
logger = logging.getLogger(__name__)


class UserProvisioningService:
    def __init__(self, db: Session) -> None:
        self.user_repository = UserRepository(db)
        self.tenant_repository = TenantRepository(db)

    def provision_user_from_token(
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

        existing_by_sub = self.user_repository.get_by_keycloak_user_id(sub)
        if existing_by_sub is not None:
            return existing_by_sub

        if email:
            existing_by_email = self.user_repository.get_by_email(email)
            if existing_by_email is not None:
                updated_user = self.user_repository.update_keycloak_user_id(
                    user_id=existing_by_email.id,
                    keycloak_user_id=sub,
                    full_name=preferred_username,
                )
                if updated_user is not None:
                    logger.info(
                        "Relinked existing user %s from legacy keycloak subject to %s",
                        updated_user.email,
                        sub,
                    )
                    return updated_user

        return self._create_new_user(
            sub=sub,
            resolved_email=resolved_email,
            preferred_username=preferred_username,
        )

    def _create_new_user(
        self,
        *,
        sub: str,
        resolved_email: str,
        preferred_username: str | None,
    ) -> User:
        default_tenant = self.tenant_repository.get_by_slug(DEFAULT_PROVISIONING_TENANT_SLUG)
        if default_tenant is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Default provisioning tenant 'demo-co' was not found",
            )

        try:
            return self.user_repository.create(
                tenant_id=default_tenant.id,
                keycloak_user_id=sub,
                email=resolved_email,
                full_name=preferred_username or resolved_email,
                role=UserRole.EMPLOYEE,
            )
        except IntegrityError as exc:
            self.user_repository.db.rollback()
            existing_user = self.user_repository.get_by_keycloak_user_id(sub)
            if existing_user is None:
                existing_user = self.user_repository.get_by_email(resolved_email)
            if existing_user is not None:
                return existing_user
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unable to provision user for this identity",
            ) from exc
