from datetime import date

from pydantic import Field, model_validator

from backend.models.enums import AbsenceDurationType, AbsenceType
from backend.schemas.common import BaseSchema, TimestampedSchema


class AbsenceBase(BaseSchema):
    absence_type: AbsenceType
    start_date: date
    end_date: date
    duration_type: AbsenceDurationType
    note: str | None = Field(default=None, max_length=1000)


class AbsenceCreate(AbsenceBase):
    employee_id: int | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "AbsenceCreate":
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        if self.duration_type in {AbsenceDurationType.HALF_DAY_AM, AbsenceDurationType.HALF_DAY_PM}:
            if self.start_date != self.end_date:
                raise ValueError("half-day absences must be single-day")
        return self


class AbsenceUpdate(BaseSchema):
    employee_id: int | None = None
    absence_type: AbsenceType | None = None
    start_date: date | None = None
    end_date: date | None = None
    duration_type: AbsenceDurationType | None = None
    note: str | None = Field(default=None, max_length=1000)


class AbsenceRead(TimestampedSchema):
    id: int
    tenant_id: int
    employee_id: int
    absence_type: AbsenceType
    start_date: date
    end_date: date
    duration_type: AbsenceDurationType
    note: str | None


class AbsenceListFilters(BaseSchema):
    employee_id: int | None = None
    from_date: date | None = None
    to_date: date | None = None
