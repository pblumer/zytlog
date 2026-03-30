from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.working_time_model import WorkingTimeModel
from backend.schemas.working_time_model import WorkingTimeModelCreate


class WorkingTimeModelRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_tenant(self, tenant_id: int) -> list[WorkingTimeModel]:
        stmt = (
            select(WorkingTimeModel)
            .where(WorkingTimeModel.tenant_id == tenant_id)
            .order_by(WorkingTimeModel.id)
        )
        return list(self.db.scalars(stmt).all())

    def create_for_tenant(self, tenant_id: int, payload: WorkingTimeModelCreate) -> WorkingTimeModel:
        model = WorkingTimeModel(tenant_id=tenant_id, **payload.model_dump())
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
