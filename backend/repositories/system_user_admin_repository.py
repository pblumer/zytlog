from sqlalchemy import case, select
from sqlalchemy.orm import Session

from backend.models.employee import Employee
from backend.models.user import User


class SystemUserAdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all_with_employee_status(self) -> list[tuple[User, bool]]:
        has_employee = case((Employee.id.is_not(None), True), else_=False).label("has_employee")
        stmt = (
            select(User, has_employee)
            .outerjoin(Employee, Employee.user_id == User.id)
            .order_by(User.tenant_id.asc(), User.full_name.asc(), User.email.asc(), User.id.asc())
        )
        return [(row[0], bool(row[1])) for row in self.db.execute(stmt).all()]

    def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.scalar(stmt)

    def has_employee_profile(self, user_id: int) -> bool:
        stmt = select(Employee.id).where(Employee.user_id == user_id)
        return self.db.scalar(stmt) is not None

    def update(self, user: User, *, tenant_id: int | None, role) -> User:
        if tenant_id is not None:
            user.tenant_id = tenant_id
        if role is not None:
            user.role = role
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
