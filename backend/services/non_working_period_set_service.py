from datetime import date
from datetime import timedelta

from fastapi import HTTPException, status

from backend.models.non_working_period import NonWorkingPeriod
from backend.models.non_working_period_set import NonWorkingPeriodSet
from backend.repositories.non_working_period_set_repository import NonWorkingPeriodSetRepository
from backend.schemas.non_working_period_set import (
    NonWorkingPeriodCreate,
    NonWorkingPeriodSetCreate,
    NonWorkingPeriodSetUpdate,
    NonWorkingPeriodUpdate,
)


class NonWorkingPeriodSetService:
    def __init__(self, repository: NonWorkingPeriodSetRepository) -> None:
        self.repository = repository

    def list_sets(self, tenant_id: int) -> list[tuple[NonWorkingPeriodSet, int]]:
        return self.repository.list_sets_with_period_counts(tenant_id)

    def create_set(self, tenant_id: int, payload: NonWorkingPeriodSetCreate) -> NonWorkingPeriodSet:
        return self.repository.create_set(tenant_id, payload)

    def update_set(
        self,
        tenant_id: int,
        period_set_id: int,
        payload: NonWorkingPeriodSetUpdate,
    ) -> NonWorkingPeriodSet:
        period_set = self.repository.get_set_for_tenant(tenant_id, period_set_id)
        if period_set is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arbeitsfrei-Set nicht gefunden")
        return self.repository.update_set(period_set, payload)

    def delete_set(self, tenant_id: int, period_set_id: int) -> None:
        period_set = self.repository.get_set_for_tenant(tenant_id, period_set_id)
        if period_set is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arbeitsfrei-Set nicht gefunden")

        if self.repository.count_employees_for_set(tenant_id, period_set_id) > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Arbeitsfrei-Set ist Mitarbeitenden zugewiesen.",
            )
        if self.repository.list_periods_for_set(tenant_id, period_set_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Arbeitsfrei-Set enthält noch Zeiträume.",
            )

        self.repository.delete_set(period_set)

    def list_periods(self, tenant_id: int, period_set_id: int) -> list[NonWorkingPeriod]:
        self._require_set(tenant_id, period_set_id)
        return self.repository.list_periods_for_set(tenant_id, period_set_id)

    def create_period(
        self,
        tenant_id: int,
        period_set_id: int,
        payload: NonWorkingPeriodCreate,
    ) -> NonWorkingPeriod:
        self._require_set(tenant_id, period_set_id)
        self._validate_period_date_order(payload.start_date, payload.end_date)
        self._ensure_no_overlap(tenant_id, period_set_id, payload.start_date, payload.end_date)
        return self.repository.create_period(tenant_id, period_set_id, payload)

    def update_period(
        self,
        tenant_id: int,
        period_set_id: int,
        period_id: int,
        payload: NonWorkingPeriodUpdate,
    ) -> NonWorkingPeriod:
        self._require_set(tenant_id, period_set_id)
        period = self.repository.get_period_for_set(tenant_id, period_set_id, period_id)
        if period is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arbeitsfreier Zeitraum nicht gefunden")

        next_start = payload.start_date if payload.start_date is not None else period.start_date
        next_end = payload.end_date if payload.end_date is not None else period.end_date
        self._validate_period_date_order(next_start, next_end)
        self._ensure_no_overlap(
            tenant_id,
            period_set_id,
            next_start,
            next_end,
            exclude_period_id=period.id,
        )
        return self.repository.update_period(period, payload)

    def delete_period(self, tenant_id: int, period_set_id: int, period_id: int) -> None:
        self._require_set(tenant_id, period_set_id)
        period = self.repository.get_period_for_set(tenant_id, period_set_id, period_id)
        if period is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arbeitsfreier Zeitraum nicht gefunden")
        self.repository.delete_period(period)

    def get_non_working_period_on_date(
        self,
        tenant_id: int,
        period_set_id: int | None,
        target_date: date,
    ) -> NonWorkingPeriod | None:
        if period_set_id is None:
            return None
        return self.repository.get_period_covering_date(tenant_id, period_set_id, target_date)

    def has_non_working_period_on_date(self, tenant_id: int, period_set_id: int | None, target_date: date) -> bool:
        if period_set_id is None:
            return False
        return self.repository.exists_date_in_set(tenant_id, period_set_id, target_date)

    def list_non_working_period_days_in_range(
        self,
        *,
        tenant_id: int,
        period_set_id: int | None,
        from_date: date,
        to_date: date,
    ) -> dict[date, NonWorkingPeriod]:
        if period_set_id is None:
            return {}
        periods = self.repository.list_periods_overlapping_range(
            tenant_id,
            period_set_id,
            from_date=from_date,
            to_date=to_date,
        )
        day_map: dict[date, NonWorkingPeriod] = {}
        for period in periods:
            cursor = max(period.start_date, from_date)
            end = min(period.end_date, to_date)
            while cursor <= end:
                if cursor not in day_map:
                    day_map[cursor] = period
                cursor += timedelta(days=1)
        return day_map

    def _require_set(self, tenant_id: int, period_set_id: int) -> NonWorkingPeriodSet:
        period_set = self.repository.get_set_for_tenant(tenant_id, period_set_id)
        if period_set is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arbeitsfrei-Set nicht gefunden")
        return period_set

    def _validate_period_date_order(self, start_date: date, end_date: date) -> None:
        if start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date muss kleiner oder gleich end_date sein",
            )

    def _ensure_no_overlap(
        self,
        tenant_id: int,
        period_set_id: int,
        start_date: date,
        end_date: date,
        exclude_period_id: int | None = None,
    ) -> None:
        if self.repository.has_overlapping_period(
            tenant_id=tenant_id,
            period_set_id=period_set_id,
            start_date=start_date,
            end_date=end_date,
            exclude_period_id=exclude_period_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Arbeitsfreier Zeitraum überlappt mit einem bestehenden Zeitraum.",
            )
