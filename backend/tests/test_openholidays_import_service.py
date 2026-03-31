from datetime import date

from backend.services.openholidays_import_service import OpenHolidaysImportService
from backend.services.openholidays_service import OpenHolidayItem


class SpyHolidayRepository:
    def __init__(self) -> None:
        self.call_order: list[str] = []
        self.added_dates: list[date] = []

    def list_by_holiday_set_and_date_range(self, *_args, **_kwargs) -> dict[date, object]:
        existing_jan = type("ExistingHoliday", (), {"id": 101})()
        existing_apr = type("ExistingHoliday", (), {"id": 102})()
        return {
            date(2026, 1, 1): existing_jan,
            date(2026, 4, 3): existing_apr,
        }

    def delete_by_holiday_set_and_date_range_without_commit(self, *_args, **_kwargs) -> int:
        self.call_order.append("delete")
        return 2

    def flush(self) -> None:
        self.call_order.append("flush")

    def add_without_commit(self, holiday) -> None:
        self.call_order.append("add")
        self.added_dates.append(holiday.date)

    def commit(self) -> None:
        self.call_order.append("commit")


class StubHolidaySetRepository:
    def get_by_id_for_tenant(self, *_args, **_kwargs):
        return object()


def test_replace_existing_in_range_flushes_deletes_before_inserts() -> None:
    holiday_repository = SpyHolidayRepository()
    service = OpenHolidaysImportService(holiday_repository, StubHolidaySetRepository())

    summary = service.commit_import(
        tenant_id=1,
        holiday_set_id=10,
        import_mode="replace_existing_in_range",
        open_holidays=[
            OpenHolidayItem(
                date=date(2026, 1, 1),
                name="Neujahr",
                country_iso_code="CH",
                subdivision_code="CH-BE",
                language_code="DE",
                source_reference="a",
            ),
            OpenHolidayItem(
                date=date(2026, 4, 3),
                name="Karfreitag",
                country_iso_code="CH",
                subdivision_code="CH-BE",
                language_code="DE",
                source_reference="b",
            ),
            OpenHolidayItem(
                date=date(2026, 8, 1),
                name="Bundesfeier",
                country_iso_code="CH",
                subdivision_code="CH-BE",
                language_code="DE",
                source_reference="c",
            ),
        ],
    )

    assert summary == {"created": 3, "skipped": 0, "replaced": 2}
    assert holiday_repository.call_order == ["delete", "flush", "add", "add", "add", "commit"]
    assert holiday_repository.added_dates == [date(2026, 1, 1), date(2026, 4, 3), date(2026, 8, 1)]
