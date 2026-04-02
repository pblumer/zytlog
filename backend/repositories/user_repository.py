from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from backend.models.employee import Employee
from backend.models.enums import UserRole
from backend.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_keycloak_user_id(self, keycloak_user_id: str) -> User | None:
        stmt = select(User).where(User.keycloak_user_id == keycloak_user_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.db.execute(stmt).scalar_one_or_none()

    def update_keycloak_user_id(
        self,
        *,
        user_id: int,
        keycloak_user_id: str,
        full_name: str | None = None,
    ) -> User | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.keycloak_user_id = keycloak_user_id
        if full_name:
            user.full_name = full_name
        self.db.commit()
        self.db.refresh(user)
        return user

    def create(
        self,
        *,
        tenant_id: int,
        keycloak_user_id: str,
        email: str,
        full_name: str,
        role: UserRole = UserRole.EMPLOYEE,
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            keycloak_user_id=keycloak_user_id,
            email=email,
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_role(self, *, user_id: int, role: UserRole) -> User | None:
        user = self.get_by_id(user_id)
        if user is None:
            return None
        user.role = role
        self.db.commit()
        self.db.refresh(user)
        return user

    def count_by_tenant_and_role(self, *, tenant_id: int, role: UserRole) -> int:
        stmt = select(func.count(User.id)).where(User.tenant_id == tenant_id, User.role == role)
        return int(self.db.execute(stmt).scalar_one())

    def list_with_employee_status_for_tenant(self, tenant_id: int) -> list[tuple[User, bool]]:
        has_employee = case((Employee.id.is_not(None), True), else_=False).label("has_employee")
        stmt = (
            select(User, has_employee)
            .outerjoin(Employee, Employee.user_id == User.id)
            .where(User.tenant_id == tenant_id)
            .order_by(User.full_name, User.email, User.id)
        )
        return [(row[0], bool(row[1])) for row in self.db.execute(stmt).all()]
