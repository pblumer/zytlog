from collections.abc import Generator

from fastapi import Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.db.session import SessionLocal
from backend.models.enums import UserRole


class AuthContext(BaseModel):
    user_id: int
    tenant_id: int
    role: UserRole


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_context(
    x_tenant_id: int = Header(default=1, alias="X-Tenant-Id"),
    x_user_id: int = Header(default=1, alias="X-User-Id"),
) -> AuthContext:
    """Temporary auth stub to provide tenant/user context.

    TODO: Replace this with Keycloak JWT validation and role extraction.
    """
    return AuthContext(user_id=x_user_id, tenant_id=x_tenant_id, role=UserRole.ADMIN)
