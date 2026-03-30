from sqlalchemy import Select
from sqlalchemy.orm import Session


class TenantScopedRepository:
    def __init__(self, db: Session, tenant_id: int) -> None:
        self.db = db
        self.tenant_id = tenant_id

    def _tenant_scope(self, stmt: Select, tenant_field) -> Select:
        return stmt.where(tenant_field == self.tenant_id)
