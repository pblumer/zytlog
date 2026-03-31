from datetime import date

from backend.models.employee import Employee
from backend.schemas.time_tracking import (
    CalendarDayStatus,
    CalendarMonthDayRead,
    CalendarMonthRead,
    DailyAccountStatus,
)
from backend.services.reporting_service import ReportingService


class CalendarService:
    def __init__(self, reporting_service: ReportingService) -> None:
        self.reporting_service = reporting_service

    def get_month_calendar(
        self,
        *,
        tenant_id: int,
        employee: Employee,
        year: int,
        month: int,
    ) -> CalendarMonthRead:
        month_overview = self.reporting_service.get_month_overview(
            tenant_id=tenant_id,
            employee=employee,
            year=year,
            month=month,
        )

        return CalendarMonthRead(
            year=year,
            month=month,
            days=[
                CalendarMonthDayRead(
                    date=day.date,
                    status=self._map_status(day.status),
                    target_minutes=day.target_minutes,
                    actual_minutes=day.actual_minutes,
                    balance_minutes=day.balance_minutes,
                    event_count=day.event_count,
                    absence=day.absence,
                )
                for day in month_overview.days
            ],
        )

    def _map_status(self, status: DailyAccountStatus) -> CalendarDayStatus:
        # Calendar uses "no_data" as the UI label for daily "empty" rows.
        if status == DailyAccountStatus.COMPLETE:
            return CalendarDayStatus.COMPLETE
        if status == DailyAccountStatus.INCOMPLETE:
            return CalendarDayStatus.INCOMPLETE
        if status == DailyAccountStatus.INVALID:
            return CalendarDayStatus.INVALID
        return CalendarDayStatus.NO_DATA
