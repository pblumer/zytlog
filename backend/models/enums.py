import enum


class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    TEAM_LEAD = "team_lead"
    ADMIN = "admin"


class TenantType(str, enum.Enum):
    COMPANY = "company"
    DEMO = "demo"


class TimeStampEventType(str, enum.Enum):
    CLOCK_IN = "clock_in"
    CLOCK_OUT = "clock_out"
    BREAK_START = "break_start"
    BREAK_END = "break_end"


class DailyTimeAccountStatus(str, enum.Enum):
    OPEN = "open"
    LOCKED = "locked"
    CORRECTED = "corrected"
