from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin, require_authenticated_user
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.repositories.non_working_period_set_repository import NonWorkingPeriodSetRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.working_time_model_repository import WorkingTimeModelRepository
from backend.schemas.employee import EmployeeCreate, EmployeeRead, EmployeeUpdate, EmployeeUserOptionRead
from backend.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeRead])
def list_employees(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> list[EmployeeRead]:
    service = EmployeeService(
        EmployeeRepository(db),
        UserRepository(db),
        WorkingTimeModelRepository(db),
        HolidaySetRepository(db),
        NonWorkingPeriodSetRepository(db),
    )
    return [EmployeeRead.model_validate(row) for row in service.list_employees(context.tenant_id)]


@router.get("/user-options", response_model=list[EmployeeUserOptionRead])
def list_employee_user_options(
    without_employee_only: bool = True,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> list[EmployeeUserOptionRead]:
    service = EmployeeService(
        EmployeeRepository(db),
        UserRepository(db),
        WorkingTimeModelRepository(db),
        HolidaySetRepository(db),
        NonWorkingPeriodSetRepository(db),
    )
    return service.list_user_options(context.tenant_id, without_employee_only)


@router.post("", response_model=EmployeeRead)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> EmployeeRead:
    service = EmployeeService(
        EmployeeRepository(db),
        UserRepository(db),
        WorkingTimeModelRepository(db),
        HolidaySetRepository(db),
        NonWorkingPeriodSetRepository(db),
    )
    created = service.create_employee(context.tenant_id, payload)
    return EmployeeRead.model_validate(created)


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(
    employee_id: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> EmployeeRead:
    service = EmployeeService(
        EmployeeRepository(db),
        UserRepository(db),
        WorkingTimeModelRepository(db),
        HolidaySetRepository(db),
        NonWorkingPeriodSetRepository(db),
    )
    updated = service.update_employee(context.tenant_id, employee_id, payload)
    return EmployeeRead.model_validate(updated)
