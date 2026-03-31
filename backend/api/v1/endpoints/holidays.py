from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from backend.api.deps import get_db
from backend.core.auth import AuthContext, require_admin
from backend.repositories.holiday_repository import HolidayRepository
from backend.schemas.holiday import HolidayCreate, HolidayRead, HolidayUpdate
from backend.services.holiday_service import HolidayService

router = APIRouter(prefix="/holidays", tags=["holidays"])


@router.get("", response_model=list[HolidayRead])
def list_holidays(
    year: int | None = Query(default=None, ge=1970, le=2100),
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> list[HolidayRead]:
    service = HolidayService(HolidayRepository(db))
    return [HolidayRead.model_validate(row) for row in service.list_holidays(context.tenant_id, year=year)]


@router.post("", response_model=HolidayRead)
def create_holiday(
    payload: HolidayCreate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> HolidayRead:
    service = HolidayService(HolidayRepository(db))
    return HolidayRead.model_validate(service.create_holiday(context.tenant_id, payload))


@router.patch("/{holiday_id}", response_model=HolidayRead)
def update_holiday(
    holiday_id: int,
    payload: HolidayUpdate,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> HolidayRead:
    service = HolidayService(HolidayRepository(db))
    return HolidayRead.model_validate(service.update_holiday(context.tenant_id, holiday_id, payload))


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_holiday(
    holiday_id: int,
    db: Session = Depends(get_db),
    context: AuthContext = Depends(require_admin),
) -> Response:
    service = HolidayService(HolidayRepository(db))
    service.delete_holiday(context.tenant_id, holiday_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
