from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.models.enums import TimeStampEventType
from backend.models.time_stamp_event import TimeStampEvent
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import DailyAccountStatus, DailyTimeAccountRead
from backend.services.absence_service import AbsenceService
from backend.services.holiday_service import HolidayService


class DailyAccountService:
    def __init__(
        self,
        repository: TimeStampEventRepository,
        holiday_service: HolidayService,
        absence_service: AbsenceService,
    ) -> None:
        self.repository = repository
        self.holiday_service = holiday_service
        self.absence_service = absence_service

    def get_daily_account(self, *, tenant_id: int, employee: Employee, target_date: date) -> DailyTimeAccountRead:
        holiday_name = self.holiday_service.get_holiday_name_for_employee_date(
            employee=employee,
            tenant=employee.tenant,
            target_date=target_date,
        )
        is_workday = self._is_employee_workday(employee=employee, target_date=target_date)
        target_minutes = self._calculate_target_minutes(
            employee=employee,
            target_date=target_date,
            holiday_name=holiday_name,
        )
        events = self.repository.list_clock_events_for_day(
            tenant_id=tenant_id,
            employee_id=employee.id,
            target_date=target_date,
        )
        actual_minutes, break_minutes, status = self._calculate_minutes_and_status(events)
        absence = self.absence_service.get_absence_context_for_day(
            tenant_id=tenant_id,
            employee_id=employee.id,
            target_date=target_date,
        )
        balance_reference_minutes = actual_minutes
        if (
            absence is not None
            and absence.duration_type == "full_day"
            and target_minutes > 0
            and absence.type in {"vacation", "sickness"}
        ):
            balance_reference_minutes = max(actual_minutes, target_minutes)

        return DailyTimeAccountRead(
            date=target_date,
            target_minutes=target_minutes,
            actual_minutes=actual_minutes,
            break_minutes=break_minutes,
            balance_minutes=balance_reference_minutes - target_minutes,
            status=status,
            event_count=len(events),
            holiday_name=holiday_name,
            is_holiday=holiday_name is not None,
            is_workday=is_workday,
            absence=absence,
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

    def _is_employee_workday(self, *, employee: Employee, target_date: date) -> bool:
        if target_date < employee.entry_date:
            return False
        if employee.exit_date is not None and target_date > employee.exit_date:
            return False

        workday_pattern = self._resolve_employee_workday_pattern(employee=employee)
        return workday_pattern[target_date.weekday()]

    def _calculate_target_minutes(
        self,
        *,
        employee: Employee,
        target_date: date,
        holiday_name: str | None = None,
    ) -> int:
        model = employee.working_time_model
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing working time model for employee",
            )
        if target_date < employee.entry_date:
            return 0
        if employee.exit_date is not None and target_date > employee.exit_date:
            return 0
        if holiday_name is not None:
            return 0

        workday_pattern = self._resolve_employee_workday_pattern(employee=employee)
        weekday_is_active = workday_pattern[target_date.weekday()]
        if not weekday_is_active:
            return 0

        relevant_workdays = self._count_relevant_workdays_for_year(
            employee=employee,
            year=target_date.year,
            workday_pattern=workday_pattern,
        )
        if relevant_workdays <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid working day configuration")

        annual_minutes = Decimal(str(model.annual_target_hours)) * Decimal("60")
        percentage = Decimal(str(employee.employment_percentage)) / Decimal("100")
        effective_annual_minutes = annual_minutes * percentage

        daily_minutes = effective_annual_minutes / Decimal(str(relevant_workdays))
        return int(daily_minutes.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _count_relevant_workdays_for_year(
        self,
        *,
        employee: Employee,
        year: int,
        workday_pattern: list[bool],
    ) -> int:
        period_start = max(employee.entry_date, date(year, 1, 1))
        period_end = date(year, 12, 31)
        if employee.exit_date is not None:
            period_end = min(employee.exit_date, period_end)

        if period_start > period_end:
            return 0

        holiday_dates = self.holiday_service.get_active_holiday_dates_for_employee(
            employee=employee,
            tenant=employee.tenant,
            from_date=period_start,
            to_date=period_end,
        )

        total = 0
        cursor = period_start
        while cursor <= period_end:
            if workday_pattern[cursor.weekday()] and cursor not in holiday_dates:
                total += 1
            cursor += timedelta(days=1)

        return total

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
