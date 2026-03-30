from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.models.enums import TimeStampEventType
from backend.models.time_stamp_event import TimeStampEvent
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import DailyAccountStatus, DailyTimeAccountRead


class DailyAccountService:
    def __init__(self, repository: TimeStampEventRepository) -> None:
        self.repository = repository

    def get_daily_account(self, *, tenant_id: int, employee: Employee, target_date: date) -> DailyTimeAccountRead:
        target_minutes = self._calculate_target_minutes(employee)
        events = self.repository.list_clock_events_for_day(
            tenant_id=tenant_id,
            employee_id=employee.id,
            target_date=target_date,
        )
        actual_minutes, break_minutes, status = self._calculate_minutes_and_status(events)

        return DailyTimeAccountRead(
            date=target_date,
            target_minutes=target_minutes,
            actual_minutes=actual_minutes,
            break_minutes=break_minutes,
            balance_minutes=actual_minutes - target_minutes,
            status=status,
            event_count=len(events),
        )

    def _calculate_target_minutes(self, employee: Employee) -> int:
        model = employee.working_time_model
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing working time model for employee",
            )
        if model.workdays_per_week <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid working time model")

        weekly_minutes = Decimal(str(model.weekly_target_hours)) * Decimal("60")
        daily_minutes = weekly_minutes / Decimal(str(model.workdays_per_week))
        percentage = Decimal(str(employee.employment_percentage)) / Decimal("100")
        return int((daily_minutes * percentage).quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _calculate_minutes_and_status(
        self, events: list[TimeStampEvent]
    ) -> tuple[int, int, DailyAccountStatus]:
        if not events:
            return 0, 0, DailyAccountStatus.EMPTY

        actual_minutes = 0
        break_minutes = 0
        has_invalid_sequence = False
        open_clock_in: TimeStampEvent | None = None
        previous_clock_out: TimeStampEvent | None = None

        for event in events:
            if event.type == TimeStampEventType.CLOCK_IN:
                if open_clock_in is not None:
                    has_invalid_sequence = True
                    continue

                if previous_clock_out is not None:
                    break_minutes += max(0, int((event.timestamp - previous_clock_out.timestamp).total_seconds() // 60))

                open_clock_in = event
                continue

            if event.type == TimeStampEventType.CLOCK_OUT:
                if open_clock_in is None:
                    has_invalid_sequence = True
                    previous_clock_out = event
                    continue

                actual_minutes += max(0, int((event.timestamp - open_clock_in.timestamp).total_seconds() // 60))
                open_clock_in = None
                previous_clock_out = event

        if has_invalid_sequence:
            status = DailyAccountStatus.INVALID
        elif open_clock_in is not None:
            status = DailyAccountStatus.INCOMPLETE
        else:
            status = DailyAccountStatus.COMPLETE

        return actual_minutes, break_minutes, status
