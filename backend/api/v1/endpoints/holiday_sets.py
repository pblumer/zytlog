from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.schemas.holiday_set import HolidaySetCreate, HolidaySetRead, HolidaySetUpdate
from backend.services.holiday_set_service import HolidaySetService

router = APIRouter(prefix="/holiday-sets", tags=["holiday-sets"])


@router.get("", response_model=list[HolidaySetRead])
def list_holiday_sets(
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> list[HolidaySetRead]:
    service = HolidaySetService(HolidaySetRepository(db))
    return [
        HolidaySetRead.model_validate({**row.__dict__, "holiday_count": count})
        for row, count in service.list_holiday_sets(context.tenant_id)
    ]


@router.post("", response_model=HolidaySetRead)
def create_holiday_set(
    payload: HolidaySetCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> HolidaySetRead:
    service = HolidaySetService(HolidaySetRepository(db))
    created = service.create_holiday_set(context.tenant_id, payload)
    return HolidaySetRead.model_validate({**created.__dict__, "holiday_count": 0})


@router.patch("/{holiday_set_id}", response_model=HolidaySetRead)
def update_holiday_set(
    holiday_set_id: int,
    payload: HolidaySetUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> HolidaySetRead:
    service = HolidaySetService(HolidaySetRepository(db))
    updated = service.update_holiday_set(context.tenant_id, holiday_set_id, payload)
    holiday_count = HolidaySetRepository(db).count_holidays_for_holiday_set(context.tenant_id, holiday_set_id)
    return HolidaySetRead.model_validate({**updated.__dict__, "holiday_count": holiday_count})


@router.delete("/{holiday_set_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_holiday_set(
    holiday_set_id: int,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> Response:
    service = HolidaySetService(HolidaySetRepository(db))
    service.delete_holiday_set(context.tenant_id, holiday_set_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
