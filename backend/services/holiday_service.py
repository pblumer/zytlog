from datetime import date
from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from backend.models.holiday import Holiday
from backend.models.tenant import Tenant
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.schemas.holiday import HolidayCreate, HolidayUpdate

if TYPE_CHECKING:
    from backend.models.employee import Employee


class HolidayService:
    def __init__(
        self,
        repository: HolidayRepository,
        holiday_set_repository: HolidaySetRepository | None = None,
    ) -> None:
        self.repository = repository
        self.holiday_set_repository = holiday_set_repository

    def list_holidays(self, tenant_id: int, *, year: int | None = None) -> list[Holiday]:
        return self.repository.list_by_tenant(tenant_id, year=year)

    def list_holidays_for_holiday_set(
        self, tenant_id: int, *, holiday_set_id: int, year: int | None = None
    ) -> list[Holiday]:
        return self.repository.list_by_holiday_set(tenant_id, holiday_set_id=holiday_set_id, year=year)

    def create_holiday(self, tenant_id: int, payload: HolidayCreate) -> Holiday:
        self._assert_holiday_set_belongs_to_tenant(tenant_id, payload.holiday_set_id)
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
        if payload.holiday_set_id is not None:
            self._assert_holiday_set_belongs_to_tenant(tenant_id, payload.holiday_set_id)
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

    def resolve_effective_holiday_set_id(self, *, employee: "Employee", tenant: Tenant) -> int | None:
        return employee.holiday_set_id if employee.holiday_set_id is not None else tenant.default_holiday_set_id

    def get_holiday_name_for_employee_date(self, *, employee: "Employee", tenant: Tenant, target_date: date) -> str | None:
        holiday_set_id = self.resolve_effective_holiday_set_id(employee=employee, tenant=tenant)
        if holiday_set_id is None:
            return None
        holiday = self.repository.get_by_holiday_set_and_date(tenant.id, holiday_set_id, target_date)
        return holiday.name if holiday else None

    def get_active_holiday_dates_for_employee(
        self,
        *,
        employee: "Employee",
        tenant: Tenant,
        from_date: date,
        to_date: date,
    ) -> set[date]:
        holiday_set_id = self.resolve_effective_holiday_set_id(employee=employee, tenant=tenant)
        if holiday_set_id is None:
            return set()
        return self.repository.list_active_dates_in_range_for_holiday_set(
            tenant.id,
            holiday_set_id=holiday_set_id,
            from_date=from_date,
            to_date=to_date,
        )

    def get_active_holidays_for_employee(
        self,
        *,
        employee: "Employee",
        tenant: Tenant,
        from_date: date,
        to_date: date,
    ) -> dict[date, Holiday]:
        holiday_set_id = self.resolve_effective_holiday_set_id(employee=employee, tenant=tenant)
        if holiday_set_id is None:
            return {}
        return self.repository.list_active_by_holiday_set_and_date_range(
            tenant.id,
            holiday_set_id=holiday_set_id,
            from_date=from_date,
            to_date=to_date,
        )

    def _assert_holiday_set_belongs_to_tenant(self, tenant_id: int, holiday_set_id: int) -> None:
        if self.holiday_set_repository is None:
            return
        holiday_set = self.holiday_set_repository.get_by_id_for_tenant(tenant_id, holiday_set_id)
        if holiday_set is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiger Feiertagssatz")
