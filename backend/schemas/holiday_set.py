from pydantic import Field

from backend.schemas.common import BaseSchema, TimestampedSchema


class HolidaySetCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    country_code: str | None = Field(default=None, max_length=8)
    region_code: str | None = Field(default=None, max_length=32)
    source: str | None = Field(default=None, max_length=40)
    active: bool = True


class HolidaySetUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    country_code: str | None = Field(default=None, max_length=8)
    region_code: str | None = Field(default=None, max_length=32)
    source: str | None = Field(default=None, max_length=40)
    active: bool | None = None


class HolidaySetRead(TimestampedSchema):
    id: int
    tenant_id: int
    name: str
    description: str | None
    country_code: str | None
    region_code: str | None
    source: str | None
    active: bool
    holiday_count: int = 0
