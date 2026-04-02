from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.tenant import Tenant
from backend.schemas.tenant_admin import TenantCreate, TenantUpdate


class TenantAdminRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Tenant]:
        stmt = select(Tenant).order_by(Tenant.name.asc(), Tenant.id.asc())
        return list(self.db.scalars(stmt).all())

    def get_by_id(self, tenant_id: int) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.id == tenant_id)
        return self.db.scalar(stmt)

    def get_by_slug(self, slug: str) -> Tenant | None:
        stmt = select(Tenant).where(Tenant.slug == slug)
        return self.db.scalar(stmt)

    def create(self, payload: TenantCreate) -> Tenant:
        tenant = Tenant(**payload.model_dump())
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant

    def update(self, tenant: Tenant, payload: TenantUpdate) -> Tenant:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(tenant, field, value)
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)
        return tenant
