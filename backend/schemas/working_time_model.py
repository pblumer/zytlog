from pydantic import Field

from backend.schemas.common import BaseSchema, TimestampedSchema


class WorkingTimeModelCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    weekly_target_hours: float = Field(gt=0, le=80)
    workdays_per_week: int = Field(default=5, ge=1, le=7)
    annual_target_hours: float | None = Field(default=None, gt=0, le=4000)
    active: bool = True


class WorkingTimeModelUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    weekly_target_hours: float | None = Field(default=None, gt=0, le=80)
    workdays_per_week: int | None = Field(default=None, ge=1, le=7)
    annual_target_hours: float | None = Field(default=None, gt=0, le=4000)
    active: bool | None = None


class WorkingTimeModelRead(TimestampedSchema):
    id: int
    tenant_id: int
    name: str
    weekly_target_hours: float
    workdays_per_week: int
    annual_target_hours: float | None
    active: bool
