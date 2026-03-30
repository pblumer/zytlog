from datetime import date

from pydantic import Field

from backend.schemas.common import BaseSchema, TimestampedSchema


class EmployeeCreate(BaseSchema):
    user_id: int
    employee_number: str | None = Field(default=None, max_length=40)
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    employment_percentage: float = Field(default=100, ge=0, le=100)
    entry_date: date
    exit_date: date | None = None
    working_time_model_id: int | None = None
    team: str | None = Field(default=None, max_length=80)


class EmployeeUpdate(BaseSchema):
    employee_number: str | None = Field(default=None, max_length=40)
    first_name: str | None = Field(default=None, min_length=1, max_length=80)
    last_name: str | None = Field(default=None, min_length=1, max_length=80)
    employment_percentage: float | None = Field(default=None, ge=0, le=100)
    entry_date: date | None = None
    exit_date: date | None = None
    working_time_model_id: int | None = None
    team: str | None = Field(default=None, max_length=80)


class EmployeeRead(TimestampedSchema):
    id: int
    tenant_id: int
    user_id: int
    employee_number: str | None
    first_name: str
    last_name: str
    employment_percentage: float
    entry_date: date
    exit_date: date | None
    working_time_model_id: int | None
    team: str | None
