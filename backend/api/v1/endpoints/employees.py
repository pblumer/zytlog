from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import AuthContext, get_auth_context, get_db
from backend.repositories.employee_repository import EmployeeRepository
from backend.schemas.employee import EmployeeCreate, EmployeeRead
from backend.services.employee_service import EmployeeService

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=list[EmployeeRead])
def list_employees(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(get_auth_context),
) -> list[EmployeeRead]:
    service = EmployeeService(EmployeeRepository(db))
    return [EmployeeRead.model_validate(row) for row in service.list_employees(context.tenant_id)]


@router.post("", response_model=EmployeeRead)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(get_auth_context),
) -> EmployeeRead:
    service = EmployeeService(EmployeeRepository(db))
    created = service.create_employee(context.tenant_id, payload)
    return EmployeeRead.model_validate(created)
