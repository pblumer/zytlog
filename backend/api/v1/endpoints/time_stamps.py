from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_authenticated_user
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import CurrentClockStatusRead, TimeStampEventRead
from backend.services.time_tracking_service import TimeTrackingService

router = APIRouter(prefix="/time-stamps", tags=["time-stamps"])


def _resolve_employee(context: AuthContext, db: Session):
    employee = EmployeeRepository(db).get_by_user_id(context.tenant_id, context.internal_user_id)
    if employee is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    return employee


@router.post("/clock-in", response_model=TimeStampEventRead)
def clock_in(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> TimeStampEventRead:
    employee = _resolve_employee(context, db)
    service = TimeTrackingService(TimeStampEventRepository(db))
    event = service.clock_in(tenant_id=context.tenant_id, employee=employee)
    return TimeStampEventRead.model_validate(event)


@router.post("/clock-out", response_model=TimeStampEventRead)
def clock_out(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> TimeStampEventRead:
    employee = _resolve_employee(context, db)
    service = TimeTrackingService(TimeStampEventRepository(db))
    event = service.clock_out(tenant_id=context.tenant_id, employee=employee)
    return TimeStampEventRead.model_validate(event)


@router.get("/my/current-status", response_model=CurrentClockStatusRead)
def my_current_status(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> CurrentClockStatusRead:
    employee = _resolve_employee(context, db)
    service = TimeTrackingService(TimeStampEventRepository(db))
    return service.current_status(tenant_id=context.tenant_id, employee=employee)


@router.get("/my", response_model=list[TimeStampEventRead])
def my_events(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> list[TimeStampEventRead]:
    employee = _resolve_employee(context, db)
    service = TimeTrackingService(TimeStampEventRepository(db))
    events = service.list_my_events(
        tenant_id=context.tenant_id,
        employee=employee,
        from_date=from_date,
        to_date=to_date,
    )
    return [TimeStampEventRead.model_validate(event) for event in events]
