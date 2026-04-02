from fastapi import HTTPException, status
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.enums import UserRole
from backend.models.user import User
from backend.repositories.tenant_repository import TenantRepository
from backend.repositories.user_repository import UserRepository

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
            return self._maybe_assign_bootstrap_admin(
                user=existing_by_sub,
                sub=sub,
                email=resolved_email,
            )

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
                    return self._maybe_assign_bootstrap_admin(
                        user=updated_user,
                        sub=sub,
                        email=resolved_email,
                    )

        user = self._create_new_user(
            sub=sub,
            resolved_email=resolved_email,
            preferred_username=preferred_username,
        )
        return self._maybe_assign_bootstrap_admin(
            user=user,
            sub=sub,
            email=resolved_email,
        )

    def _create_new_user(
        self,
        *,
        sub: str,
        resolved_email: str,
        preferred_username: str | None,
    ) -> User:
        default_tenant = self.tenant_repository.get_by_slug(settings.provisioning_tenant_slug)
        if default_tenant is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Default provisioning tenant '{settings.provisioning_tenant_slug}' was not found",
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

    def _maybe_assign_bootstrap_admin(self, *, user: User, sub: str, email: str | None) -> User:
        if not settings.bootstrap_admin_enabled:
            return user
        if not self._matches_bootstrap_identity(sub=sub, email=email):
            return user
        if user.role == UserRole.ADMIN:
            return user

        admin_count = self.user_repository.count_by_tenant_and_role(
            tenant_id=user.tenant_id,
            role=UserRole.ADMIN,
        )
        if admin_count > 0:
            return user

        promoted_user = self.user_repository.update_role(user_id=user.id, role=UserRole.ADMIN)
        return promoted_user or user

    def _matches_bootstrap_identity(self, *, sub: str, email: str | None) -> bool:
        configured_sub = (settings.bootstrap_admin_sub or "").strip()
        if configured_sub:
            return sub == configured_sub

        configured_email = (settings.bootstrap_admin_email or "").strip().lower()
        if configured_email and email:
            return configured_email == email.strip().lower()

        return False
