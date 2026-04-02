from backend.models.enums import UserRole
from backend.schemas.common import BaseSchema, TimestampedSchema


class SystemUserRead(TimestampedSchema):
    id: int
    tenant_id: int
    email: str
    full_name: str
    keycloak_user_id: str
    role: UserRole
    has_employee_profile: bool


class SystemUserUpdate(BaseSchema):
    tenant_id: int | None = None
    role: UserRole | None = None
