from backend.models.working_time_model import WorkingTimeModel
from backend.repositories.working_time_model_repository import WorkingTimeModelRepository
from backend.schemas.working_time_model import WorkingTimeModelCreate


class WorkingTimeModelService:
    def __init__(self, repository: WorkingTimeModelRepository) -> None:
        self.repository = repository

    def list_models(self, tenant_id: int) -> list[WorkingTimeModel]:
        return self.repository.list_by_tenant(tenant_id)

    def create_model(self, tenant_id: int, payload: WorkingTimeModelCreate) -> WorkingTimeModel:
        # TODO: enforce role checks and validation rules in this service.
        return self.repository.create_for_tenant(tenant_id, payload)
