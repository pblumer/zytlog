from backend.models.enums import UserRole
from backend.schemas.common import TimestampedSchema


class UserRead(TimestampedSchema):
    id: int
    tenant_id: int
    email: str
    full_name: str
    role: UserRole
