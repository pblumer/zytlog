from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.employee import Employee
from backend.schemas.employee import EmployeeCreate


class EmployeeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_tenant(self, tenant_id: int) -> list[Employee]:
        stmt = select(Employee).where(Employee.tenant_id == tenant_id).order_by(Employee.id)
        return list(self.db.scalars(stmt).all())

    def create_for_tenant(self, tenant_id: int, payload: EmployeeCreate) -> Employee:
        employee = Employee(tenant_id=tenant_id, **payload.model_dump())
        self.db.add(employee)
        self.db.commit()
        self.db.refresh(employee)
        return employee
