from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_authenticated_user
from backend.repositories.absence_repository import AbsenceRepository
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import CalendarMonthRead
from backend.services.absence_service import AbsenceService
from backend.services.calendar_service import CalendarService
from backend.services.daily_account_service import DailyAccountService
from backend.services.holiday_service import HolidayService
from backend.services.reporting_service import ReportingService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/my/month", response_model=CalendarMonthRead)
def my_month_calendar(
    year: int = Query(ge=1970, le=2100),
    month: int = Query(ge=1, le=12),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> CalendarMonthRead:
    employee = EmployeeRepository(db).get_by_user_id(context.tenant_id, context.internal_user_id)
    if employee is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")

    repository = TimeStampEventRepository(db)
    daily_service = DailyAccountService(
        repository,
        HolidayService(HolidayRepository(db)),
        AbsenceService(AbsenceRepository(db), EmployeeRepository(db)),
    )
    reporting_service = ReportingService(daily_service)
    calendar_service = CalendarService(reporting_service)
    return calendar_service.get_month_calendar(
        tenant_id=context.tenant_id,
        employee=employee,
        year=year,
        month=month,
    )
