from fastapi import HTTPException, status

from backend.models.holiday_set import HolidaySet
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.schemas.holiday_set import HolidaySetCreate, HolidaySetUpdate


class HolidaySetService:
    def __init__(self, repository: HolidaySetRepository) -> None:
        self.repository = repository

    def list_holiday_sets(self, tenant_id: int) -> list[tuple[HolidaySet, int]]:
        return self.repository.list_by_tenant_with_counts(tenant_id)

    def create_holiday_set(self, tenant_id: int, payload: HolidaySetCreate) -> HolidaySet:
        return self.repository.create_for_tenant(tenant_id, payload)

    def update_holiday_set(self, tenant_id: int, holiday_set_id: int, payload: HolidaySetUpdate) -> HolidaySet:
        holiday_set = self.repository.get_by_id_for_tenant(tenant_id, holiday_set_id)
        if holiday_set is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feiertagssatz nicht gefunden")
        return self.repository.update(holiday_set, payload)

    def delete_holiday_set(self, tenant_id: int, holiday_set_id: int) -> None:
        holiday_set = self.repository.get_by_id_for_tenant(tenant_id, holiday_set_id)
        if holiday_set is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feiertagssatz nicht gefunden")

        if self.repository.tenant_uses_as_default(tenant_id, holiday_set_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Feiertagssatz wird als Standard-Feiertagssatz verwendet.",
            )
        if self.repository.count_employees_for_holiday_set(tenant_id, holiday_set_id) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Feiertagssatz ist Mitarbeitern zugewiesen.",
            )
        if self.repository.count_holidays_for_holiday_set(tenant_id, holiday_set_id) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Feiertagssatz enthält noch Feiertage.",
            )

        self.repository.delete(holiday_set)
