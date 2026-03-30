from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin, require_authenticated_user
from backend.repositories.working_time_model_repository import WorkingTimeModelRepository
from backend.schemas.working_time_model import WorkingTimeModelCreate, WorkingTimeModelRead
from backend.services.working_time_model_service import WorkingTimeModelService

router = APIRouter(prefix="/working-time-models", tags=["working-time-models"])


@router.get("", response_model=list[WorkingTimeModelRead])
def list_working_time_models(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_authenticated_user),
) -> list[WorkingTimeModelRead]:
    service = WorkingTimeModelService(WorkingTimeModelRepository(db))
    return [WorkingTimeModelRead.model_validate(row) for row in service.list_models(context.tenant_id)]


@router.post("", response_model=WorkingTimeModelRead)
def create_working_time_model(
    payload: WorkingTimeModelCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> WorkingTimeModelRead:
    service = WorkingTimeModelService(WorkingTimeModelRepository(db))
    created = service.create_model(context.tenant_id, payload)
    return WorkingTimeModelRead.model_validate(created)
