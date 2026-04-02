from fastapi import HTTPException, status
import logging
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.enums import UserRole
from backend.models.user import User
from backend.core.config import settings
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

        user: User | None = self.user_repository.get_by_keycloak_user_id(sub)
        if user is None and email:
            existing_by_email = self.user_repository.get_by_email(email)
            if existing_by_email is not None:
                user = self.user_repository.update_keycloak_user_id(
                    user_id=existing_by_email.id,
                    keycloak_user_id=sub,
                    full_name=preferred_username,
                )
                if user is not None:
                    logger.info(
                        "Relinked existing user %s from legacy keycloak subject to %s",
                        user.email,
                        sub,
                    )

        if user is None:
            user = self._create_new_user(
                sub=sub,
                resolved_email=resolved_email,
                preferred_username=preferred_username,
            )

        return self._maybe_promote_bootstrap_admin(
            user=user,
            sub=sub,
            email=email,
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

    def _maybe_promote_bootstrap_admin(
        self,
        *,
        user: User,
        sub: str,
        email: str | None,
    ) -> User:
        if not settings.bootstrap_admin_enabled:
            return user
        if user.role == UserRole.ADMIN:
            return user

        provisioning_tenant = self.tenant_repository.get_by_slug(settings.provisioning_tenant_slug)
        if provisioning_tenant is None or user.tenant_id != provisioning_tenant.id:
            return user

        bootstrap_sub = settings.bootstrap_admin_sub
        bootstrap_email = settings.bootstrap_admin_email
        if bootstrap_sub:
            matches_identity = sub == bootstrap_sub
        elif bootstrap_email:
            matches_identity = bool(email) and email.lower() == bootstrap_email.lower()
        else:
            matches_identity = False

        if not matches_identity:
            return user
        if self.user_repository.count_admins_by_tenant(user.tenant_id) > 0:
            return user

        user.role = UserRole.ADMIN
        self.user_repository.db.commit()
        self.user_repository.db.refresh(user)
        logger.info("Promoted bootstrap admin user %s in tenant %s", user.email, settings.provisioning_tenant_slug)
        return user
