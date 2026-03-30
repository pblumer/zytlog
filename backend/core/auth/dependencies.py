from collections.abc import Callable
from functools import lru_cache
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth.context import AuthContext
from backend.core.auth.jwt import JWTValidator, TokenValidationError
from backend.core.config import settings
from backend.models.enums import UserRole
from backend.repositories.user_repository import UserRepository
from backend.services.user_provisioning_service import UserProvisioningService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/token", auto_error=False)
logger = logging.getLogger(__name__)


@lru_cache
def get_jwt_validator() -> JWTValidator:
    return JWTValidator(
        issuer=settings.keycloak_issuer_resolved,
        jwks_url=settings.keycloak_jwks_url_resolved,
        verify_audience=settings.keycloak_verify_audience,
        audience=settings.keycloak_audience,
    )


def _build_context_from_user(
    *,
    keycloak_subject: str | None,
    username: str | None,
    email: str | None,
    realm_roles: list[str],
    resource_roles: dict[str, list[str]],
    user_id: int,
    tenant_id: int,
    role: UserRole,
) -> AuthContext:
    return AuthContext(
        authenticated=True,
        keycloak_subject=keycloak_subject,
        username=username,
        email=email,
        realm_roles=realm_roles,
        resource_roles=resource_roles,
        internal_user_id=user_id,
        tenant_id=tenant_id,
        internal_role=role,
    )


def get_auth_context(
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
    validator: JWTValidator = Depends(get_jwt_validator),
) -> AuthContext:
    user_repository = UserRepository(db)
    provisioning_service = UserProvisioningService(db)

    if not settings.auth_enabled:
        fallback_user = user_repository.get_by_id(settings.auth_disabled_fallback_user_id)
        if fallback_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Auth is disabled, but no fallback user exists",
            )
        return _build_context_from_user(
            keycloak_subject=fallback_user.keycloak_user_id,
            username=fallback_user.full_name,
            email=fallback_user.email,
            realm_roles=[],
            resource_roles={},
            user_id=fallback_user.id,
            tenant_id=fallback_user.tenant_id,
            role=fallback_user.role,
        )

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    try:
        claims = validator.validate_token(token)
    except TokenValidationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = user_repository.get_by_keycloak_user_id(claims.sub)
    if user is None:
        user = provisioning_service.create_user_from_token(
            sub=claims.sub,
            email=claims.email,
            preferred_username=claims.preferred_username,
        )
        logger.info(
            "Auto-provisioned user %s (sub=%s) in tenant demo-co",
            user.email,
            claims.sub,
        )

    return _build_context_from_user(
        keycloak_subject=claims.sub,
        username=claims.preferred_username,
        email=claims.email or user.email,
        realm_roles=claims.realm_roles,
        resource_roles=claims.resource_roles,
        user_id=user.id,
        tenant_id=user.tenant_id,
        role=user.role,
    )


def require_authenticated_user(context: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not context.authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return context


def require_role(*allowed_roles: UserRole) -> Callable[[AuthContext], AuthContext]:
    def _enforce_role(context: AuthContext = Depends(require_authenticated_user)) -> AuthContext:
        if context.internal_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role for this resource",
            )
        return context

    return _enforce_role


def require_admin(context: AuthContext = Depends(require_role(UserRole.ADMIN))) -> AuthContext:
    return context


def require_team_lead_or_admin(
    context: AuthContext = Depends(require_role(UserRole.TEAM_LEAD, UserRole.ADMIN)),
) -> AuthContext:
    return context
