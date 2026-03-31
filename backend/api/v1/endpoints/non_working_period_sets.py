from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin
from backend.repositories.non_working_period_set_repository import NonWorkingPeriodSetRepository
from backend.schemas.non_working_period_set import (
    NonWorkingPeriodCreate,
    NonWorkingPeriodRead,
    NonWorkingPeriodSetCreate,
    NonWorkingPeriodSetRead,
    NonWorkingPeriodSetUpdate,
    NonWorkingPeriodUpdate,
)
from backend.services.non_working_period_set_service import NonWorkingPeriodSetService

router = APIRouter(prefix="/non-working-period-sets", tags=["non-working-period-sets"])


@router.get("", response_model=list[NonWorkingPeriodSetRead])
def list_non_working_period_sets(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> list[NonWorkingPeriodSetRead]:
    service = NonWorkingPeriodSetService(NonWorkingPeriodSetRepository(db))
    return [
        NonWorkingPeriodSetRead.model_validate({**row.__dict__, "period_count": count})
        for row, count in service.list_sets(context.tenant_id)
    ]


@router.post("", response_model=NonWorkingPeriodSetRead)
def create_non_working_period_set(
    payload: NonWorkingPeriodSetCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> NonWorkingPeriodSetRead:
    service = NonWorkingPeriodSetService(NonWorkingPeriodSetRepository(db))
    created = service.create_set(context.tenant_id, payload)
    return NonWorkingPeriodSetRead.model_validate({**created.__dict__, "period_count": 0})


@router.patch("/{period_set_id}", response_model=NonWorkingPeriodSetRead)
def update_non_working_period_set(
    period_set_id: int,
    payload: NonWorkingPeriodSetUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> NonWorkingPeriodSetRead:
    service = NonWorkingPeriodSetService(NonWorkingPeriodSetRepository(db))
    updated = service.update_set(context.tenant_id, period_set_id, payload)
    period_count = len(NonWorkingPeriodSetRepository(db).list_periods_for_set(context.tenant_id, period_set_id))
    return NonWorkingPeriodSetRead.model_validate({**updated.__dict__, "period_count": period_count})


@router.delete("/{period_set_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_non_working_period_set(
    period_set_id: int,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> Response:
    service = NonWorkingPeriodSetService(NonWorkingPeriodSetRepository(db))
    service.delete_set(context.tenant_id, period_set_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{period_set_id}/periods", response_model=list[NonWorkingPeriodRead])
def list_non_working_periods(
    period_set_id: int,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> list[NonWorkingPeriodRead]:
    service = NonWorkingPeriodSetService(NonWorkingPeriodSetRepository(db))
    return [NonWorkingPeriodRead.model_validate(item) for item in service.list_periods(context.tenant_id, period_set_id)]


@router.post("/{period_set_id}/periods", response_model=NonWorkingPeriodRead)
def create_non_working_period(
    period_set_id: int,
    payload: NonWorkingPeriodCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> NonWorkingPeriodRead:
    service = NonWorkingPeriodSetService(NonWorkingPeriodSetRepository(db))
    created = service.create_period(context.tenant_id, period_set_id, payload)
    return NonWorkingPeriodRead.model_validate(created)


@router.patch("/{period_set_id}/periods/{period_id}", response_model=NonWorkingPeriodRead)
def update_non_working_period(
    period_set_id: int,
    period_id: int,
    payload: NonWorkingPeriodUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> NonWorkingPeriodRead:
    service = NonWorkingPeriodSetService(NonWorkingPeriodSetRepository(db))
    updated = service.update_period(context.tenant_id, period_set_id, period_id, payload)
    return NonWorkingPeriodRead.model_validate(updated)


@router.delete("/{period_set_id}/periods/{period_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_non_working_period(
    period_set_id: int,
    period_id: int,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> Response:
    service = NonWorkingPeriodSetService(NonWorkingPeriodSetRepository(db))
    service.delete_period(context.tenant_id, period_set_id, period_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
