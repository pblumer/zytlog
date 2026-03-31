from datetime import date

from pydantic import Field

from backend.schemas.common import BaseSchema, TimestampedSchema


class NonWorkingPeriodSetCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    active: bool = True


class NonWorkingPeriodSetUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    active: bool | None = None


class NonWorkingPeriodSetRead(TimestampedSchema):
    id: int
    tenant_id: int
    name: str
    description: str | None
    active: bool
    period_count: int = 0


class NonWorkingPeriodCreate(BaseSchema):
    start_date: date
    end_date: date
    name: str = Field(min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=40)


class NonWorkingPeriodUpdate(BaseSchema):
    start_date: date | None = None
    end_date: date | None = None
    name: str | None = Field(default=None, min_length=1, max_length=120)
    category: str | None = Field(default=None, max_length=40)


class NonWorkingPeriodRead(TimestampedSchema):
    id: int
    tenant_id: int
    non_working_period_set_id: int
    start_date: date
    end_date: date
    name: str
    category: str | None
