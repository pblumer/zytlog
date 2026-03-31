from datetime import date, datetime
import enum

from pydantic import Field

from backend.models.enums import TimeStampEventType
from backend.schemas.common import BaseSchema, TimestampedSchema


class ClockStatus(str, enum.Enum):
    CLOCKED_IN = "clocked_in"
    CLOCKED_OUT = "clocked_out"


class DailyAccountStatus(str, enum.Enum):
    EMPTY = "empty"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class CalendarDayStatus(str, enum.Enum):
    NO_DATA = "no_data"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    INVALID = "invalid"


class TimeStampEventRead(TimestampedSchema):
    id: int
    tenant_id: int
    employee_id: int
    timestamp: datetime
    type: TimeStampEventType
    source: str
    comment: str | None


class TimeStampEventUpdate(BaseSchema):
    timestamp: datetime | None = None
    comment: str | None = Field(default=None, max_length=300)


class ManualTimeStampCreate(BaseSchema):
    timestamp: datetime
    type: TimeStampEventType
    comment: str | None = Field(default=None, max_length=300)


class CurrentClockStatusRead(BaseSchema):
    employee_id: int
    status: ClockStatus
    last_event_type: TimeStampEventType | None
    last_event_timestamp: datetime | None


class DailyTimeAccountRead(BaseSchema):
    date: date
    target_minutes: int
    actual_minutes: int
    break_minutes: int
    balance_minutes: int
    status: DailyAccountStatus
    event_count: int = Field(ge=0)
    is_holiday: bool = False
    holiday_name: str | None = None
    is_workday: bool = False


class DailyOverviewRow(BaseSchema):
    date: date
    target_minutes: int
    actual_minutes: int
    break_minutes: int
    balance_minutes: int
    status: DailyAccountStatus
    event_count: int = Field(ge=0)
    is_holiday: bool = False
    holiday_name: str | None = None
    is_workday: bool = False


class OverviewTotals(BaseSchema):
    target_minutes: int = 0
    actual_minutes: int = 0
    break_minutes: int = 0
    balance_minutes: int = 0
    days_total: int = Field(default=0, ge=0)
    days_complete: int = Field(default=0, ge=0)
    days_incomplete: int = Field(default=0, ge=0)
    days_invalid: int = Field(default=0, ge=0)
    days_empty: int = Field(default=0, ge=0)


class WeeklyOverviewRead(BaseSchema):
    iso_year: int
    iso_week: int
    range_start: date
    range_end: date
    days: list[DailyOverviewRow]
    totals: OverviewTotals


class MonthlyOverviewRead(BaseSchema):
    year: int
    month: int
    range_start: date
    range_end: date
    days: list[DailyOverviewRow]
    totals: OverviewTotals


class CalendarMonthDayRead(BaseSchema):
    date: date
    status: CalendarDayStatus
    target_minutes: int
    actual_minutes: int
    balance_minutes: int
    event_count: int = Field(ge=0)


class CalendarMonthRead(BaseSchema):
    year: int
    month: int
    days: list[CalendarMonthDayRead]


class MonthlySummaryRow(BaseSchema):
    month: int = Field(ge=1, le=12)
    target_minutes: int
    actual_minutes: int
    break_minutes: int
    balance_minutes: int
    days_total: int = Field(ge=0)
    days_complete: int = Field(ge=0)
    days_incomplete: int = Field(ge=0)
    days_invalid: int = Field(ge=0)
    days_empty: int = Field(ge=0)


class YearlyOverviewRead(BaseSchema):
    year: int
    months: list[MonthlySummaryRow]
    totals: OverviewTotals
