from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from backend.models.holiday import Holiday
from backend.repositories.holiday_repository import HolidayRepository
from backend.schemas.holiday import HolidayCreate, HolidayUpdate


class HolidayService:
    def __init__(self, repository: HolidayRepository) -> None:
        self.repository = repository

    def list_holidays(self, tenant_id: int, *, year: int | None = None) -> list[Holiday]:
        return self.repository.list_by_tenant(tenant_id, year=year)

    def create_holiday(self, tenant_id: int, payload: HolidayCreate) -> Holiday:
        try:
            return self.repository.create_for_tenant(tenant_id, payload)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Für dieses Datum existiert bereits ein Feiertag.",
            ) from exc

    def update_holiday(self, tenant_id: int, holiday_id: int, payload: HolidayUpdate) -> Holiday:
        holiday = self.repository.get_by_id_for_tenant(tenant_id, holiday_id)
        if holiday is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feiertag nicht gefunden")
        try:
            return self.repository.update(holiday, payload)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Für dieses Datum existiert bereits ein Feiertag.",
            ) from exc

    def delete_holiday(self, tenant_id: int, holiday_id: int) -> None:
        holiday = self.repository.get_by_id_for_tenant(tenant_id, holiday_id)
        if holiday is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feiertag nicht gefunden")
        self.repository.delete(holiday)

    def get_holiday_name_for_date(self, tenant_id: int, target_date: date) -> str | None:
        holiday = self.repository.get_by_tenant_and_date(tenant_id, target_date)
        return holiday.name if holiday else None

    def get_active_holiday_dates(self, tenant_id: int, *, from_date: date, to_date: date) -> set[date]:
        return self.repository.list_active_dates_in_range(tenant_id, from_date=from_date, to_date=to_date)
