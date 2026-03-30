import enum


class EmploymentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class WorkingTimeModelType(str, enum.Enum):
    FIXED = "fixed"
    FLEXIBLE = "flexible"


class TimeStampEventType(str, enum.Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"
