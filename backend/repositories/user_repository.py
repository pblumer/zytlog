from sqlalchemy import select
from sqlalchemy.orm import Session

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
