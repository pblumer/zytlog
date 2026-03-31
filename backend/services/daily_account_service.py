from datetime import date, timedelta
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
        target_minutes = self._calculate_target_minutes(employee=employee, target_date=target_date)
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

    def get_daily_accounts_in_range(
        self,
        *,
        tenant_id: int,
        employee: Employee,
        from_date: date,
        to_date: date,
    ) -> list[DailyTimeAccountRead]:
        if from_date > to_date:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date range")

        accounts: list[DailyTimeAccountRead] = []
        cursor = from_date
        while cursor <= to_date:
            accounts.append(self.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=cursor))
            cursor += timedelta(days=1)

        return accounts

    def _calculate_target_minutes(self, *, employee: Employee, target_date: date) -> int:
        model = employee.working_time_model
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing working time model for employee",
            )
        if model.default_workdays_per_week <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid working time model")
        if target_date < employee.entry_date:
            return 0
        if employee.exit_date is not None and target_date > employee.exit_date:
            return 0

        weekday_is_active = self._resolve_employee_workday_pattern(employee=employee)[target_date.weekday()]
        if not weekday_is_active:
            return 0

        weekly_minutes = Decimal(str(model.weekly_target_hours)) * Decimal("60")
        percentage = Decimal(str(employee.employment_percentage)) / Decimal("100")
        effective_weekly_minutes = weekly_minutes * percentage
        active_days = self._count_active_weekdays(employee=employee)
        if active_days <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid working day configuration")

        daily_minutes = effective_weekly_minutes / Decimal(str(active_days))
        return int(daily_minutes.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _count_active_weekdays(self, *, employee: Employee) -> int:
        return sum(1 for weekday_active in self._resolve_employee_workday_pattern(employee=employee) if weekday_active)

    def _resolve_employee_workday_pattern(self, *, employee: Employee) -> list[bool]:
        model = employee.working_time_model
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing working time model for employee",
            )

        defaults = [
            model.default_workday_monday,
            model.default_workday_tuesday,
            model.default_workday_wednesday,
            model.default_workday_thursday,
            model.default_workday_friday,
            model.default_workday_saturday,
            model.default_workday_sunday,
        ]
        overrides = [
            employee.workday_monday,
            employee.workday_tuesday,
            employee.workday_wednesday,
            employee.workday_thursday,
            employee.workday_friday,
            employee.workday_saturday,
            employee.workday_sunday,
        ]
        return [override if override is not None else defaults[idx] for idx, override in enumerate(overrides)]

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
