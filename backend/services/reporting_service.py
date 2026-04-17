from datetime import date, timedelta

from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.schemas.time_tracking import (
    DailyAccountStatus,
    DailyOverviewRow,
    MonthlyOverviewRead,
    MonthlySummaryRow,
    OverviewTotals,
    WeeklyOverviewRead,
    YearlyOverviewRead,
)
from backend.services.daily_account_service import DailyAccountService


class ReportingService:
    def __init__(self, daily_account_service: DailyAccountService) -> None:
        self.daily_account_service = daily_account_service

    def get_week_overview(
        self,
        *,
        tenant_id: int,
        employee: Employee,
        iso_year: int,
        iso_week: int,
    ) -> WeeklyOverviewRead:
        self._validate_year(iso_year)
        range_start, range_end = self._resolve_iso_week_range(iso_year=iso_year, iso_week=iso_week)
        days = self._build_daily_rows(
            tenant_id=tenant_id,
            employee=employee,
            range_start=range_start,
            range_end=range_end,
        )
        return WeeklyOverviewRead(
            iso_year=iso_year,
            iso_week=iso_week,
            range_start=range_start,
            range_end=range_end,
            days=days,
            totals=self._aggregate_totals(days),
        )

    def get_month_overview(
        self,
        *,
        tenant_id: int,
        employee: Employee,
        year: int,
        month: int,
    ) -> MonthlyOverviewRead:
        self._validate_year(year)
        if month < 1 or month > 12:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="month must be in 1..12")

        range_start = date(year, month, 1)
        next_month_start = date(year + (1 if month == 12 else 0), 1 if month == 12 else month + 1, 1)
        range_end = next_month_start - timedelta(days=1)

        days = self._build_daily_rows(
            tenant_id=tenant_id,
            employee=employee,
            range_start=range_start,
            range_end=range_end,
        )

        return MonthlyOverviewRead(
            year=year,
            month=month,
            range_start=range_start,
            range_end=range_end,
            days=days,
            totals=self._aggregate_totals(days),
        )

    def get_year_overview(self, *, tenant_id: int, employee: Employee, year: int) -> YearlyOverviewRead:
        self._validate_year(year)

        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        rows = self._build_daily_rows(
            tenant_id=tenant_id,
            employee=employee,
            range_start=year_start,
            range_end=year_end,
        )

        monthly_rows: dict[int, list[DailyOverviewRow]] = {month: [] for month in range(1, 13)}
        for row in rows:
            monthly_rows[row.date.month].append(row)

        months: list[MonthlySummaryRow] = []
        annual_totals = OverviewTotals()
        for month in range(1, 13):
            month_totals = self._aggregate_totals(monthly_rows[month])
            months.append(
                MonthlySummaryRow(
                    month=month,
                    target_minutes=month_totals.target_minutes,
                    actual_minutes=month_totals.actual_minutes,
                    break_minutes=month_totals.break_minutes,
                    balance_minutes=month_totals.balance_minutes,
                    days_total=month_totals.days_total,
                    days_complete=month_totals.days_complete,
                    days_incomplete=month_totals.days_incomplete,
                    days_invalid=month_totals.days_invalid,
                    days_empty=month_totals.days_empty,
                    days_target_bearing=month_totals.days_target_bearing,
                    days_workdays_excluding_non_working_period=month_totals.days_workdays_excluding_non_working_period,
                    days_non_working=month_totals.days_non_working,
                    days_in_non_working_period=month_totals.days_in_non_working_period,
                )
            )
            annual_totals = self._sum_totals(annual_totals, month_totals)

        return YearlyOverviewRead(year=year, months=months, totals=annual_totals)

    def _build_daily_rows(
        self,
        *,
        tenant_id: int,
        employee: Employee,
        range_start: date,
        range_end: date,
    ) -> list[DailyOverviewRow]:
        accounts = self.daily_account_service.get_daily_accounts_in_range(
            tenant_id=tenant_id,
            employee=employee,
            from_date=range_start,
            to_date=range_end,
        )
        return [DailyOverviewRow(**account.model_dump()) for account in accounts]

    def _resolve_iso_week_range(self, *, iso_year: int, iso_week: int) -> tuple[date, date]:
        last_week = date(iso_year, 12, 28).isocalendar().week
        if iso_week < 1 or iso_week > last_week:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"week must be in 1..{last_week} for year {iso_year}",
            )

        range_start = date.fromisocalendar(iso_year, iso_week, 1)
        range_end = date.fromisocalendar(iso_year, iso_week, 7)
        return range_start, range_end

    def _validate_year(self, year: int) -> None:
        if year < 1970 or year > 2100:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="year must be in 1970..2100")

    def _aggregate_totals(self, days: list[DailyOverviewRow]) -> OverviewTotals:
        totals = OverviewTotals(days_total=len(days))
        for day in days:
            totals.target_minutes += day.target_minutes
            totals.actual_minutes += day.actual_minutes
            totals.break_minutes += day.break_minutes
            totals.balance_minutes += day.balance_minutes

            if day.status == DailyAccountStatus.COMPLETE:
                totals.days_complete += 1
            elif day.status == DailyAccountStatus.INCOMPLETE:
                totals.days_incomplete += 1
            elif day.status == DailyAccountStatus.INVALID:
                totals.days_invalid += 1
            else:
                totals.days_empty += 1

            if day.target_minutes > 0:
                totals.days_target_bearing += 1
            if day.is_workday and not day.is_in_non_working_period:
                totals.days_workdays_excluding_non_working_period += 1
            if not day.is_workday:
                totals.days_non_working += 1
            if day.is_in_non_working_period:
                totals.days_in_non_working_period += 1

        return totals

    def _sum_totals(self, left: OverviewTotals, right: OverviewTotals) -> OverviewTotals:
        return OverviewTotals(
            target_minutes=left.target_minutes + right.target_minutes,
            actual_minutes=left.actual_minutes + right.actual_minutes,
            break_minutes=left.break_minutes + right.break_minutes,
            balance_minutes=left.balance_minutes + right.balance_minutes,
            days_total=left.days_total + right.days_total,
            days_complete=left.days_complete + right.days_complete,
            days_incomplete=left.days_incomplete + right.days_incomplete,
            days_invalid=left.days_invalid + right.days_invalid,
            days_empty=left.days_empty + right.days_empty,
            days_target_bearing=left.days_target_bearing + right.days_target_bearing,
            days_workdays_excluding_non_working_period=left.days_workdays_excluding_non_working_period
            + right.days_workdays_excluding_non_working_period,
            days_non_working=left.days_non_working + right.days_non_working,
            days_in_non_working_period=left.days_in_non_working_period + right.days_in_non_working_period,
        )
