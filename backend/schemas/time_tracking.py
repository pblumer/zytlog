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


class TimeStampEventRead(TimestampedSchema):
    id: int
    tenant_id: int
    employee_id: int
    timestamp: datetime
    type: TimeStampEventType
    source: str
    comment: str | None


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
