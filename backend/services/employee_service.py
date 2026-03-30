from backend.models.employee import Employee
from backend.repositories.employee_repository import EmployeeRepository
from backend.schemas.employee import EmployeeCreate


class EmployeeService:
    def __init__(self, repository: EmployeeRepository) -> None:
        self.repository = repository

    def list_employees(self, tenant_id: int) -> list[Employee]:
        return self.repository.list_by_tenant(tenant_id)

    def create_employee(self, tenant_id: int, payload: EmployeeCreate) -> Employee:
        # TODO: enforce role checks and tenant/user membership via real auth context.
        return self.repository.create_for_tenant(tenant_id, payload)
