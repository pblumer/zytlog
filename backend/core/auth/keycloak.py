from pydantic import BaseModel, Field


class KeycloakClaims(BaseModel):
    sub: str
    preferred_username: str | None = None
    email: str | None = None
    realm_roles: list[str] = Field(default_factory=list)
    resource_roles: dict[str, list[str]] = Field(default_factory=dict)


def extract_keycloak_claims(payload: dict[str, object]) -> KeycloakClaims:
    realm_access = payload.get("realm_access")
    realm_roles: list[str] = []
    if isinstance(realm_access, dict):
        raw_realm_roles = realm_access.get("roles")
        if isinstance(raw_realm_roles, list):
            realm_roles = [str(role) for role in raw_realm_roles]

    resource_access = payload.get("resource_access")
    resource_roles: dict[str, list[str]] = {}
    if isinstance(resource_access, dict):
        for client, value in resource_access.items():
            if not isinstance(value, dict):
                continue
            raw_roles = value.get("roles")
            if isinstance(raw_roles, list):
                resource_roles[str(client)] = [str(role) for role in raw_roles]

    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise ValueError("JWT is missing required subject claim")

    preferred_username = payload.get("preferred_username")
    email = payload.get("email")

    return KeycloakClaims(
        sub=sub,
        preferred_username=str(preferred_username) if preferred_username is not None else None,
        email=str(email) if email is not None else None,
        realm_roles=realm_roles,
        resource_roles=resource_roles,
    )
