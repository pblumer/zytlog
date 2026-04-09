from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.models.enums import TimeStampEventType
from backend.models.non_working_period import NonWorkingPeriod
from backend.models.time_stamp_event import TimeStampEvent
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import DailyAccountStatus, DailyTimeAccountRead
from backend.services.absence_service import AbsenceService
from backend.services.holiday_service import HolidayService
from backend.services.non_working_period_set_service import NonWorkingPeriodSetService


@dataclass(frozen=True)
class _YearCalculationContext:
    year: int
    period_start: date
    period_end: date
    workday_pattern: list[bool]
    holidays_by_date: dict[date, str]
    non_working_period_by_date: dict[date, NonWorkingPeriod]
    relevant_workdays: int
    daily_target_minutes_by_date: dict[date, int]


class DailyAccountService:
    def __init__(
        self,
        repository: TimeStampEventRepository,
        holiday_service: HolidayService,
        absence_service: AbsenceService,
        non_working_period_set_service: NonWorkingPeriodSetService,
    ) -> None:
        self.repository = repository
        self.holiday_service = holiday_service
        self.absence_service = absence_service
        self.non_working_period_set_service = non_working_period_set_service

    def get_daily_account(self, *, tenant_id: int, employee: Employee, target_date: date) -> DailyTimeAccountRead:
        year_context = self._build_year_calculation_context(employee=employee, year=target_date.year)
        holiday_name = year_context.holidays_by_date.get(target_date)
        non_working_period = year_context.non_working_period_by_date.get(target_date)
        is_in_non_working_period = non_working_period is not None

        target_minutes = self._calculate_target_minutes(
            employee=employee,
            target_date=target_date,
            context=year_context,
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
            is_workday=self._is_employee_workday(
                employee=employee,
                target_date=target_date,
                workday_pattern=year_context.workday_pattern,
            ),
            absence=absence,
            is_in_non_working_period=is_in_non_working_period,
            non_working_period_label=non_working_period.name if non_working_period is not None else None,
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

        events = self.repository.list_clock_events(
            tenant_id=tenant_id,
            employee_id=employee.id,
            from_date=from_date,
            to_date=to_date,
        )
        events_by_day: dict[date, list[TimeStampEvent]] = {}
        for event in events:
            event_date = event.timestamp.date()
            events_by_day.setdefault(event_date, []).append(event)

        absences_by_day = self.absence_service.get_absence_contexts_in_range(
            tenant_id=tenant_id,
            employee_id=employee.id,
            from_date=from_date,
            to_date=to_date,
        )

        context_cache: dict[int, _YearCalculationContext] = {}
        accounts: list[DailyTimeAccountRead] = []
        cursor = from_date
        while cursor <= to_date:
            context = context_cache.get(cursor.year)
            if context is None:
                context = self._build_year_calculation_context(employee=employee, year=cursor.year)
                context_cache[cursor.year] = context

            day_events = events_by_day.get(cursor, [])
            holiday_name = context.holidays_by_date.get(cursor)
            non_working_period = context.non_working_period_by_date.get(cursor)
            target_minutes = self._calculate_target_minutes(
                employee=employee,
                target_date=cursor,
                context=context,
            )
            actual_minutes, break_minutes, status = self._calculate_minutes_and_status(day_events)
            absence = absences_by_day.get(cursor)
            balance_reference_minutes = actual_minutes
            if (
                absence is not None
                and absence.duration_type == "full_day"
                and target_minutes > 0
                and absence.type in {"vacation", "sickness"}
            ):
                balance_reference_minutes = max(actual_minutes, target_minutes)

            accounts.append(
                DailyTimeAccountRead(
                    date=cursor,
                    target_minutes=target_minutes,
                    actual_minutes=actual_minutes,
                    break_minutes=break_minutes,
                    balance_minutes=balance_reference_minutes - target_minutes,
                    status=status,
                    event_count=len(day_events),
                    holiday_name=holiday_name,
                    is_holiday=holiday_name is not None,
                    is_workday=self._is_employee_workday(
                        employee=employee,
                        target_date=cursor,
                        workday_pattern=context.workday_pattern,
                    ),
                    absence=absence,
                    is_in_non_working_period=non_working_period is not None,
                    non_working_period_label=non_working_period.name if non_working_period is not None else None,
                )
            )
            cursor += timedelta(days=1)

        return accounts

    def _is_employee_workday(self, *, employee: Employee, target_date: date, workday_pattern: list[bool] | None = None) -> bool:
        if target_date < employee.entry_date:
            return False
        if employee.exit_date is not None and target_date > employee.exit_date:
            return False

        pattern = workday_pattern if workday_pattern is not None else self._resolve_employee_workday_pattern(employee=employee)
        return pattern[target_date.weekday()]

    def _calculate_target_minutes(
        self,
        *,
        employee: Employee,
        target_date: date,
        context: _YearCalculationContext | None = None,
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

        resolved_context = context if context is not None else self._build_year_calculation_context(employee=employee, year=target_date.year)
        if resolved_context.holidays_by_date.get(target_date) is not None:
            return 0
        if resolved_context.non_working_period_by_date.get(target_date) is not None:
            return 0

        if not resolved_context.workday_pattern[target_date.weekday()]:
            return 0

        relevant_workdays = resolved_context.relevant_workdays
        if relevant_workdays <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid working day configuration")

        return resolved_context.daily_target_minutes_by_date.get(target_date, 0)

    def _build_year_calculation_context(self, *, employee: Employee, year: int) -> _YearCalculationContext:
        period_start = max(employee.entry_date, date(year, 1, 1))
        period_end = date(year, 12, 31)
        if employee.exit_date is not None:
            period_end = min(employee.exit_date, period_end)

        workday_pattern = self._resolve_employee_workday_pattern(employee=employee)
        if period_start > period_end:
            return _YearCalculationContext(
                year=year,
                period_start=period_start,
                period_end=period_end,
                workday_pattern=workday_pattern,
                holidays_by_date={},
                non_working_period_by_date={},
                relevant_workdays=0,
                daily_target_minutes_by_date={},
            )

        holidays = self.holiday_service.get_active_holidays_for_employee(
            employee=employee,
            tenant=employee.tenant,
            from_date=period_start,
            to_date=period_end,
        )
        non_working_period_by_date = self.non_working_period_set_service.list_non_working_period_days_in_range(
            tenant_id=employee.tenant_id,
            period_set_id=employee.non_working_period_set_id,
            from_date=period_start,
            to_date=period_end,
        )

        holiday_dates = set(holidays.keys())
        non_working_period_dates = set(non_working_period_by_date.keys())
        relevant_workday_dates = self._list_relevant_workdays_for_year(
            period_start=period_start,
            period_end=period_end,
            workday_pattern=workday_pattern,
            holiday_dates=holiday_dates,
            non_working_period_dates=non_working_period_dates,
        )
        daily_target_minutes_by_date = self._build_daily_target_distribution(
            employee=employee,
            relevant_workday_dates=relevant_workday_dates,
        )
        holidays_by_date = {day: holiday.name for day, holiday in holidays.items()}

        return _YearCalculationContext(
            year=year,
            period_start=period_start,
            period_end=period_end,
            workday_pattern=workday_pattern,
            holidays_by_date=holidays_by_date,
            non_working_period_by_date=non_working_period_by_date,
            relevant_workdays=len(relevant_workday_dates),
            daily_target_minutes_by_date=daily_target_minutes_by_date,
        )

    def _list_relevant_workdays_for_year(
        self,
        *,
        period_start: date,
        period_end: date,
        workday_pattern: list[bool],
        holiday_dates: set[date],
        non_working_period_dates: set[date],
    ) -> list[date]:
        if period_start > period_end:
            return []

        relevant_days: list[date] = []
        cursor = period_start
        while cursor <= period_end:
            if (
                workday_pattern[cursor.weekday()]
                and cursor not in holiday_dates
                and cursor not in non_working_period_dates
            ):
                relevant_days.append(cursor)
            cursor += timedelta(days=1)

        return relevant_days

    def _build_daily_target_distribution(
        self,
        *,
        employee: Employee,
        relevant_workday_dates: list[date],
    ) -> dict[date, int]:
        if not relevant_workday_dates:
            return {}

        model = employee.working_time_model
        if model is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing working time model for employee",
            )

        annual_minutes = Decimal(str(model.annual_target_hours)) * Decimal("60")
        percentage = Decimal(str(employee.employment_percentage)) / Decimal("100")
        effective_annual_minutes = (annual_minutes * percentage).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        effective_annual_minutes_int = int(effective_annual_minutes)

        total_days = len(relevant_workday_dates)
        base_daily_minutes = effective_annual_minutes_int // total_days
        remainder_minutes = effective_annual_minutes_int % total_days

        distribution: dict[date, int] = {}
        for index, target_day in enumerate(relevant_workday_dates):
            distribution[target_day] = base_daily_minutes + (1 if index < remainder_minutes else 0)

        return distribution

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
