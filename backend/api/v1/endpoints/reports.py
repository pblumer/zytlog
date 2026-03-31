from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_authenticated_user
from backend.models.employee import Employee
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import MonthlyOverviewRead, WeeklyOverviewRead, YearlyOverviewRead
from backend.services.daily_account_service import DailyAccountService
from backend.services.holiday_service import HolidayService
from backend.services.reporting_service import ReportingService

router = APIRouter(prefix="/reports", tags=["reports"])


def _resolve_employee(db: Session, context: AuthContext) -> Employee:
    employee = EmployeeRepository(db).get_by_user_id(context.tenant_id, context.internal_user_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    return employee


@router.get("/my/week", response_model=WeeklyOverviewRead)
def my_week_overview(
    year: int = Query(ge=1970, le=2100),
    week: int = Query(ge=1, le=53),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    service = ReportingService(DailyAccountService(TimeStampEventRepository(db), HolidayService(HolidayRepository(db))))
    return service.get_week_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        iso_year=year,
        iso_week=week,
    )


@router.get("/my/month", response_model=MonthlyOverviewRead)
def my_month_overview(
    year: int = Query(ge=1970, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    service = ReportingService(DailyAccountService(TimeStampEventRepository(db), HolidayService(HolidayRepository(db))))
    return service.get_month_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        year=year,
        month=month,
    )


@router.get("/my/year", response_model=YearlyOverviewRead)
def my_year_overview(
    year: int = Query(ge=1970, le=2100),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = _resolve_employee(db, context)
    service = ReportingService(DailyAccountService(TimeStampEventRepository(db), HolidayService(HolidayRepository(db))))
    return service.get_year_overview(
        tenant_id=context.tenant_id,
        employee=employee,
        year=year,
    )
