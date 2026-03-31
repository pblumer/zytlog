from fastapi import HTTPException, status

from backend.models.working_time_model import WorkingTimeModel
from backend.repositories.working_time_model_repository import WorkingTimeModelRepository
from backend.schemas.working_time_model import WorkingTimeModelCreate, WorkingTimeModelUpdate


class WorkingTimeModelService:
    def __init__(self, repository: WorkingTimeModelRepository) -> None:
        self.repository = repository

    def list_models(self, tenant_id: int) -> list[WorkingTimeModel]:
        return self.repository.list_by_tenant(tenant_id)

    def create_model(self, tenant_id: int, payload: WorkingTimeModelCreate) -> WorkingTimeModel:
        # TODO: enforce role checks and validation rules in this service.
        return self.repository.create_for_tenant(tenant_id, payload)

    def update_model(self, tenant_id: int, model_id: int, payload: WorkingTimeModelUpdate) -> WorkingTimeModel:
        model = self.repository.get_by_id_for_tenant(tenant_id, model_id)
        if model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arbeitszeitmodell nicht gefunden")
        return self.repository.update(model, payload)

    def delete_model(self, tenant_id: int, model_id: int) -> None:
        model = self.repository.get_by_id_for_tenant(tenant_id, model_id)
        if model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arbeitszeitmodell nicht gefunden")

        if self.repository.count_assigned_employees(tenant_id, model_id) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Arbeitszeitmodell kann nicht gelöscht werden, da es noch Mitarbeitenden zugeordnet ist.",
            )

        self.repository.delete(model)
