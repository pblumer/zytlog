from backend.models.enums import TenantType
from backend.schemas.common import TimestampedSchema


class TenantRead(TimestampedSchema):
    id: int
    name: str
    slug: str
    active: bool
    type: TenantType
    timezone: str
    default_holiday_set_id: int | None
