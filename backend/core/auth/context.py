from pydantic import BaseModel, Field

from backend.models.enums import UserRole


class AuthContext(BaseModel):
    authenticated: bool
    keycloak_subject: str | None = None
    username: str | None = None
    email: str | None = None
    realm_roles: list[str] = Field(default_factory=list)
    resource_roles: dict[str, list[str]] = Field(default_factory=dict)

    internal_user_id: int | None = None
    internal_role: UserRole | None = None
    tenant_id: int | None = None
