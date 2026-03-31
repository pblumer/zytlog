from datetime import date

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin, require_authenticated_user
from backend.repositories.absence_repository import AbsenceRepository
from backend.repositories.employee_repository import EmployeeRepository
from backend.schemas.absence import AbsenceCreate, AbsenceRead, AbsenceUpdate
from backend.services.absence_service import AbsenceService

router = APIRouter(prefix="/absences", tags=["absences"])
admin_router = APIRouter(prefix="/admin/absences", tags=["admin-absences"])


def _service(db: Session) -> AbsenceService:
    return AbsenceService(AbsenceRepository(db), EmployeeRepository(db))


@router.get("/my", response_model=list[AbsenceRead])
def list_my_absences(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> list[AbsenceRead]:
    employee = EmployeeRepository(db).get_by_user_id(context.tenant_id, context.internal_user_id)
    if employee is None:
        return []
    items = _service(db).list_absences(
        tenant_id=context.tenant_id,
        employee_id=employee.id,
        from_date=from_date,
        to_date=to_date,
    )
    return [AbsenceRead.model_validate(item) for item in items]


@router.post("/my", response_model=AbsenceRead, status_code=status.HTTP_201_CREATED)
def create_my_absence(
    payload: AbsenceCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> AbsenceRead:
    employee = EmployeeRepository(db).get_by_user_id(context.tenant_id, context.internal_user_id)
    if employee is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
    created = _service(db).create_absence(
        tenant_id=context.tenant_id,
        payload=payload,
        requester_user_id=context.internal_user_id,
        force_employee_id=employee.id,
    )
    return AbsenceRead.model_validate(created)


@admin_router.get("", response_model=list[AbsenceRead])
def list_admin_absences(
    employee_id: int | None = Query(default=None),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> list[AbsenceRead]:
    items = _service(db).list_absences(
        tenant_id=context.tenant_id,
        employee_id=employee_id,
        from_date=from_date,
        to_date=to_date,
    )
    return [AbsenceRead.model_validate(item) for item in items]


@admin_router.post("", response_model=AbsenceRead, status_code=status.HTTP_201_CREATED)
def create_admin_absence(
    payload: AbsenceCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> AbsenceRead:
    if payload.employee_id is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="employee_id is required")
    created = _service(db).create_absence(
        tenant_id=context.tenant_id,
        payload=payload,
        requester_user_id=context.internal_user_id,
        force_employee_id=payload.employee_id,
    )
    return AbsenceRead.model_validate(created)


@admin_router.patch("/{absence_id}", response_model=AbsenceRead)
def update_admin_absence(
    absence_id: int,
    payload: AbsenceUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> AbsenceRead:
    updated = _service(db).update_absence(tenant_id=context.tenant_id, absence_id=absence_id, payload=payload)
    return AbsenceRead.model_validate(updated)


@admin_router.delete("/{absence_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_admin_absence(
    absence_id: int,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> Response:
    _service(db).delete_absence(tenant_id=context.tenant_id, absence_id=absence_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
