from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.tenant import Tenant


class TenantRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()
