from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.schemas.holiday import HolidayCreate, HolidayRead, HolidayUpdate
from backend.services.holiday_service import HolidayService

router = APIRouter(prefix="/holidays", tags=["holidays"])


@router.get("", response_model=list[HolidayRead])
def list_holidays(
    year: int | None = Query(default=None, ge=1970, le=2100),
    holiday_set_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> list[HolidayRead]:
    service = HolidayService(HolidayRepository(db), HolidaySetRepository(db))
    rows = (
        service.list_holidays_for_holiday_set(context.tenant_id, holiday_set_id=holiday_set_id, year=year)
        if holiday_set_id is not None
        else service.list_holidays(context.tenant_id, year=year)
    )
    return [HolidayRead.model_validate(row) for row in rows]


@router.post("", response_model=HolidayRead)
def create_holiday(
    payload: HolidayCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> HolidayRead:
    service = HolidayService(HolidayRepository(db), HolidaySetRepository(db))
    return HolidayRead.model_validate(service.create_holiday(context.tenant_id, payload))


@router.patch("/{holiday_id}", response_model=HolidayRead)
def update_holiday(
    holiday_id: int,
    payload: HolidayUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> HolidayRead:
    service = HolidayService(HolidayRepository(db), HolidaySetRepository(db))
    return HolidayRead.model_validate(service.update_holiday(context.tenant_id, holiday_id, payload))


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> Response:
    service = HolidayService(HolidayRepository(db), HolidaySetRepository(db))
    service.delete_holiday(context.tenant_id, holiday_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
