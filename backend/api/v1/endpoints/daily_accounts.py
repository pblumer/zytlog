from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_authenticated_user
from backend.repositories.absence_repository import AbsenceRepository
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import DailyTimeAccountRead
from backend.services.absence_service import AbsenceService
from backend.services.daily_account_service import DailyAccountService
from backend.services.holiday_service import HolidayService

router = APIRouter(prefix="/daily-accounts", tags=["daily-accounts"])


@router.get("/my", response_model=DailyTimeAccountRead | list[DailyTimeAccountRead])
def my_daily_account(
    date_value: date | None = Query(default=None, alias="date"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
):
    employee = EmployeeRepository(db).get_by_user_id(context.tenant_id, context.internal_user_id)
    if employee is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")

    service = DailyAccountService(
        TimeStampEventRepository(db),
        HolidayService(HolidayRepository(db)),
        AbsenceService(AbsenceRepository(db), EmployeeRepository(db)),
    )

    if date_value is not None:
        return service.get_daily_account(tenant_id=context.tenant_id, employee=employee, target_date=date_value)

    if from_date is None or to_date is None:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either ?date= or both ?from= and ?to=",
        )

    if from_date > to_date:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date range")

    return service.get_daily_accounts_in_range(
        tenant_id=context.tenant_id,
        employee=employee,
        from_date=from_date,
        to_date=to_date,
    )
