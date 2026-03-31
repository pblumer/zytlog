from datetime import date as DateType

from pydantic import Field

from backend.schemas.common import BaseSchema, TimestampedSchema


class HolidayCreate(BaseSchema):
    holiday_set_id: int
    date: DateType
    name: str = Field(min_length=1, max_length=120)
    active: bool = True


class HolidayUpdate(BaseSchema):
    holiday_set_id: int | None = None
    date: DateType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    active: bool | None = None


class HolidayRead(TimestampedSchema):
    id: int
    tenant_id: int
    holiday_set_id: int
    date: DateType
    name: str
    active: bool
