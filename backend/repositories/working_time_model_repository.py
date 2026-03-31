from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.employee import Employee
from backend.models.working_time_model import WorkingTimeModel
from backend.schemas.working_time_model import WorkingTimeModelCreate, WorkingTimeModelUpdate


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

    def get_by_id_for_tenant(self, tenant_id: int, model_id: int) -> WorkingTimeModel | None:
        stmt = select(WorkingTimeModel).where(
            WorkingTimeModel.tenant_id == tenant_id,
            WorkingTimeModel.id == model_id,
        )
        return self.db.scalar(stmt)

    def update(self, model: WorkingTimeModel, payload: WorkingTimeModelUpdate) -> WorkingTimeModel:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(model, field, value)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def count_assigned_employees(self, tenant_id: int, model_id: int) -> int:
        stmt = select(func.count(Employee.id)).where(
            Employee.tenant_id == tenant_id,
            Employee.working_time_model_id == model_id,
        )
        return int(self.db.scalar(stmt) or 0)

    def delete(self, model: WorkingTimeModel) -> None:
        self.db.delete(model)
        self.db.commit()
