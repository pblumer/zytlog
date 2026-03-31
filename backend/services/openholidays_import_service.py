from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import logging

from fastapi import HTTPException, status

from backend.models.holiday import Holiday
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.services.openholidays_service import OpenHolidayItem

logger = logging.getLogger(__name__)


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


@dataclass(frozen=True)
class PreparedImportRow:
    date: date
    name: str
    country_iso_code: str
    subdivision_code: str | None
    language_code: str
    source_reference: str
    existing_holiday_id: int | None
    exists_in_holiday_set: bool
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
        prepared_rows = self._prepare_import_rows(
            tenant_id=tenant_id,
            holiday_set_id=holiday_set_id,
            open_holidays=open_holidays,
            import_mode=import_mode,
        )
        return [
            PreviewRow(
                date=row.date,
                name=row.name,
                country_iso_code=row.country_iso_code,
                subdivision_code=row.subdivision_code,
                language_code=row.language_code,
                source="openholidays",
                exists_in_holiday_set=row.exists_in_holiday_set,
                existing_holiday_id=row.existing_holiday_id,
                action_hint=row.action_hint,
            )
            for row in prepared_rows
        ]

    def commit_import(
        self,
        *,
        tenant_id: int,
        holiday_set_id: int,
        open_holidays: list[OpenHolidayItem],
        import_mode: str,
    ) -> dict[str, int]:
        prepared_rows = self._prepare_import_rows(
            tenant_id=tenant_id,
            holiday_set_id=holiday_set_id,
            open_holidays=open_holidays,
            import_mode=import_mode,
        )
        if not prepared_rows:
            return {"created": 0, "skipped": 0, "replaced": 0}
        created = 0
        skipped = 0
        replaced = 0

        if import_mode == "replace_existing_in_range":
            replaced = self.holiday_repository.delete_by_holiday_set_and_date_range_without_commit(
                tenant_id,
                holiday_set_id=holiday_set_id,
                from_date=prepared_rows[0].date,
                to_date=prepared_rows[-1].date,
            )
            rows_to_create = prepared_rows
        else:
            rows_to_create = []
            for row in prepared_rows:
                if row.exists_in_holiday_set:
                    skipped += 1
                    continue
                rows_to_create.append(row)

        logger.info(
            "OpenHolidays commit rows prepared for insert.",
            extra={
                "tenant_id": tenant_id,
                "holiday_set_id": holiday_set_id,
                "import_mode": import_mode,
                "prepared_rows_count": len(prepared_rows),
                "existing_dates_count": sum(1 for row in prepared_rows if row.exists_in_holiday_set),
                "rows_to_create_count": len(rows_to_create),
                "dates_to_create": [row.date.isoformat() for row in rows_to_create],
            },
        )

        for row in rows_to_create:
            self.holiday_repository.add_without_commit(
                Holiday(
                    tenant_id=tenant_id,
                    holiday_set_id=holiday_set_id,
                    date=row.date,
                    name=row.name,
                    active=True,
                )
            )
            created += 1

        self.holiday_repository.commit()
        return {"created": created, "skipped": skipped, "replaced": replaced}

    def _prepare_import_rows(
        self,
        *,
        tenant_id: int,
        holiday_set_id: int,
        open_holidays: list[OpenHolidayItem],
        import_mode: str,
    ) -> list[PreparedImportRow]:
        self._assert_holiday_set_for_tenant(tenant_id=tenant_id, holiday_set_id=holiday_set_id)
        unique_rows = self._deduplicate_open_holidays(open_holidays)
        if not unique_rows:
            return []
        existing_by_date = self.holiday_repository.list_by_holiday_set_and_date_range(
            tenant_id,
            holiday_set_id=holiday_set_id,
            from_date=unique_rows[0].date,
            to_date=unique_rows[-1].date,
        )
        rows: list[PreparedImportRow] = []
        for item in unique_rows:
            existing = existing_by_date.get(item.date)
            action_hint = "create"
            if existing is not None:
                action_hint = "skip" if import_mode == "skip_existing" else "replace"
            rows.append(
                PreparedImportRow(
                    date=item.date,
                    name=item.name,
                    country_iso_code=item.country_iso_code,
                    subdivision_code=item.subdivision_code,
                    language_code=item.language_code,
                    source_reference=item.source_reference,
                    existing_holiday_id=existing.id if existing else None,
                    exists_in_holiday_set=existing is not None,
                    action_hint=action_hint,
                )
            )
        return rows

    def _deduplicate_open_holidays(self, open_holidays: list[OpenHolidayItem]) -> list[OpenHolidayItem]:
        if not open_holidays:
            return []
        unique_by_date: dict[date, OpenHolidayItem] = {}
        for item in sorted(open_holidays, key=lambda row: (row.date, row.source_reference, row.name)):
            if item.date not in unique_by_date:
                unique_by_date[item.date] = item
        return sorted(unique_by_date.values(), key=lambda row: row.date)

    def _assert_holiday_set_for_tenant(self, *, tenant_id: int, holiday_set_id: int) -> None:
        holiday_set = self.holiday_set_repository.get_by_id_for_tenant(tenant_id, holiday_set_id)
        if holiday_set is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feiertagssatz nicht gefunden")
