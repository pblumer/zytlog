from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin, require_authenticated_user
from backend.repositories.employee_repository import EmployeeRepository
from backend.schemas.employee import EmployeeCreate, EmployeeRead
from backend.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeRead])
def list_employees(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> list[EmployeeRead]:
    service = EmployeeService(EmployeeRepository(db))
    return [EmployeeRead.model_validate(row) for row in service.list_employees(context.tenant_id)]


@router.post("", response_model=EmployeeRead)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> EmployeeRead:
    service = EmployeeService(EmployeeRepository(db))
    created = service.create_employee(context.tenant_id, payload)
    return EmployeeRead.model_validate(created)
