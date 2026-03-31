from pydantic import Field

from backend.schemas.common import BaseSchema, TimestampedSchema


class WorkingTimeModelCreate(BaseSchema):
    name: str = Field(min_length=1, max_length=100)
    annual_target_hours: float = Field(gt=0, le=4000)
    default_workday_monday: bool = True
    default_workday_tuesday: bool = True
    default_workday_wednesday: bool = True
    default_workday_thursday: bool = True
    default_workday_friday: bool = True
    default_workday_saturday: bool = False
    default_workday_sunday: bool = False
    active: bool = True


class WorkingTimeModelUpdate(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    annual_target_hours: float | None = Field(default=None, gt=0, le=4000)
    default_workday_monday: bool | None = None
    default_workday_tuesday: bool | None = None
    default_workday_wednesday: bool | None = None
    default_workday_thursday: bool | None = None
    default_workday_friday: bool | None = None
    default_workday_saturday: bool | None = None
    default_workday_sunday: bool | None = None
    active: bool | None = None


class WorkingTimeModelRead(TimestampedSchema):
    id: int
    tenant_id: int
    name: str
    annual_target_hours: float
    default_workday_monday: bool
    default_workday_tuesday: bool
    default_workday_wednesday: bool
    default_workday_thursday: bool
    default_workday_friday: bool
    default_workday_saturday: bool
    default_workday_sunday: bool
    active: bool
