from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException, status

from backend.models.holiday import Holiday
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.services.openholidays_service import OpenHolidayItem


@dataclass(frozen=True)
class PreviewRow:
    date: date
    name: str
    country_iso_code: str
    subdivision_code: str | None
    language_code: str
    source: str
    exists_in_holiday_set: bool
    existing_holiday_id: int | None
    action_hint: str


class OpenHolidaysImportService:
    def __init__(
        self,
        holiday_repository: HolidayRepository,
        holiday_set_repository: HolidaySetRepository,
    ) -> None:
        self.holiday_repository = holiday_repository
        self.holiday_set_repository = holiday_set_repository

    def preview_import(
        self,
        *,
        tenant_id: int,
        holiday_set_id: int,
        open_holidays: list[OpenHolidayItem],
        import_mode: str,
    ) -> list[PreviewRow]:
        self._assert_holiday_set_for_tenant(tenant_id=tenant_id, holiday_set_id=holiday_set_id)
        existing_by_date = self.holiday_repository.list_active_by_holiday_set_and_date_range(
            tenant_id,
            holiday_set_id=holiday_set_id,
            from_date=min(item.date for item in open_holidays) if open_holidays else date.today(),
            to_date=max(item.date for item in open_holidays) if open_holidays else date.today(),
        )

        rows: list[PreviewRow] = []
        for item in open_holidays:
            existing = existing_by_date.get(item.date)
            action_hint = "create"
            if existing is not None:
                action_hint = "skip" if import_mode == "skip_existing" else "replace"
            rows.append(
                PreviewRow(
                    date=item.date,
                    name=item.name,
                    country_iso_code=item.country_iso_code,
                    subdivision_code=item.subdivision_code,
                    language_code=item.language_code,
                    source="openholidays",
                    exists_in_holiday_set=existing is not None,
                    existing_holiday_id=existing.id if existing else None,
                    action_hint=action_hint,
                )
            )
        return rows

    def commit_import(
        self,
        *,
        tenant_id: int,
        holiday_set_id: int,
        open_holidays: list[OpenHolidayItem],
        import_mode: str,
    ) -> dict[str, int]:
        self._assert_holiday_set_for_tenant(tenant_id=tenant_id, holiday_set_id=holiday_set_id)
        if not open_holidays:
            return {"created": 0, "skipped": 0, "replaced": 0}

        existing_by_date = self.holiday_repository.list_active_by_holiday_set_and_date_range(
            tenant_id,
            holiday_set_id=holiday_set_id,
            from_date=min(item.date for item in open_holidays),
            to_date=max(item.date for item in open_holidays),
        )
        created = 0
        skipped = 0
        replaced = 0

        for item in open_holidays:
            existing = existing_by_date.get(item.date)
            if existing is not None and import_mode == "skip_existing":
                skipped += 1
                continue
            if existing is not None:
                self.holiday_repository.delete_without_commit(existing)
                replaced += 1

            self.holiday_repository.add_without_commit(
                Holiday(
                    tenant_id=tenant_id,
                    holiday_set_id=holiday_set_id,
                    date=item.date,
                    name=item.name,
                    active=True,
                )
            )
            created += 1

        self.holiday_repository.commit()
        return {"created": created, "skipped": skipped, "replaced": replaced}

    def _assert_holiday_set_for_tenant(self, *, tenant_id: int, holiday_set_id: int) -> None:
        holiday_set = self.holiday_set_repository.get_by_id_for_tenant(tenant_id, holiday_set_id)
        if holiday_set is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feiertagssatz nicht gefunden")
