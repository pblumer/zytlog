from backend.models.enums import UserRole
from backend.schemas.common import BaseSchema


class MeRead(BaseSchema):
    user_id: int
    username: str | None
    email: str
    role: UserRole
    tenant_id: int
