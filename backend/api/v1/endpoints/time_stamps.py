from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_authenticated_user
from backend.models.enums import UserRole
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import (
    CurrentClockStatusRead,
    ManualTimeStampCreate,
    TimeStampEventRead,
    TimeStampEventUpdate,
)
from backend.services.time_tracking_service import TimeTrackingService

router = APIRouter(prefix="/time-stamps", tags=["time-stamps"])


def _resolve_employee(context: AuthContext, db: Session):
    employee = EmployeeRepository(db).get_by_user_id(context.tenant_id, context.internal_user_id)
    if employee is None:
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


@router.patch("/{time_stamp_id}", response_model=TimeStampEventRead)
def update_time_stamp(
    time_stamp_id: int,
    payload: TimeStampEventUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> TimeStampEventRead:
    actor_employee = None
    if context.internal_role != UserRole.ADMIN:
        actor_employee = _resolve_employee(context, db)

    service = TimeTrackingService(TimeStampEventRepository(db))
    updated = service.update_event(
        tenant_id=context.tenant_id,
        event_id=time_stamp_id,
        payload=payload,
        actor_role=context.internal_role,
        actor_employee_id=actor_employee.id if actor_employee else None,
        actor_user_id=context.internal_user_id,
    )
    return TimeStampEventRead.model_validate(updated)


@router.post("/manual", response_model=TimeStampEventRead)
def create_manual_time_stamp(
    payload: ManualTimeStampCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> TimeStampEventRead:
    employee = _resolve_employee(context, db)
    service = TimeTrackingService(TimeStampEventRepository(db))
    event = service.create_manual_event(
        tenant_id=context.tenant_id,
        employee=employee,
        payload=payload,
    )
    return TimeStampEventRead.model_validate(event)


@router.delete("/{time_stamp_id}", response_model=TimeStampEventRead)
def delete_time_stamp(
    time_stamp_id: int,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> TimeStampEventRead:
    actor_employee = None
    if context.internal_role != UserRole.ADMIN:
        actor_employee = _resolve_employee(context, db)

    service = TimeTrackingService(TimeStampEventRepository(db))
    deleted = service.delete_event(
        tenant_id=context.tenant_id,
        event_id=time_stamp_id,
        actor_role=context.internal_role,
        actor_employee_id=actor_employee.id if actor_employee else None,
        actor_user_id=context.internal_user_id,
    )
    return TimeStampEventRead.model_validate(deleted)
