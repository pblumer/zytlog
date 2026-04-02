from backend.models.enums import TenantType
from backend.schemas.common import BaseSchema, TimestampedSchema


class TenantCreate(BaseSchema):
    name: str
    slug: str
    active: bool = True
    type: TenantType = TenantType.COMPANY
    timezone: str = "UTC"
    default_holiday_set_id: int | None = None


class TenantUpdate(BaseSchema):
    name: str | None = None
    slug: str | None = None
    active: bool | None = None
    type: TenantType | None = None
    timezone: str | None = None
    default_holiday_set_id: int | None = None


class TenantAdminRead(TimestampedSchema):
    id: int
    name: str
    slug: str
    active: bool
    type: TenantType
    timezone: str
    default_holiday_set_id: int | None
