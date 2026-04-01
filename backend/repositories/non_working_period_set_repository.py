from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from backend.models.employee import Employee
from backend.models.non_working_period import NonWorkingPeriod
from backend.models.non_working_period_set import NonWorkingPeriodSet
from backend.schemas.non_working_period_set import (
    NonWorkingPeriodCreate,
    NonWorkingPeriodSetCreate,
    NonWorkingPeriodSetUpdate,
    NonWorkingPeriodUpdate,
)


class NonWorkingPeriodSetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_sets_with_period_counts(self, tenant_id: int) -> list[tuple[NonWorkingPeriodSet, int]]:
        stmt = (
            select(NonWorkingPeriodSet, func.count(NonWorkingPeriod.id))
            .outerjoin(NonWorkingPeriod, NonWorkingPeriod.non_working_period_set_id == NonWorkingPeriodSet.id)
            .where(NonWorkingPeriodSet.tenant_id == tenant_id)
            .group_by(NonWorkingPeriodSet.id)
            .order_by(NonWorkingPeriodSet.name.asc(), NonWorkingPeriodSet.id.asc())
        )
        return [(row[0], int(row[1])) for row in self.db.execute(stmt).all()]

    def get_set_for_tenant(self, tenant_id: int, period_set_id: int) -> NonWorkingPeriodSet | None:
        stmt = select(NonWorkingPeriodSet).where(
            NonWorkingPeriodSet.tenant_id == tenant_id,
            NonWorkingPeriodSet.id == period_set_id,
        )
        return self.db.scalar(stmt)

    def create_set(self, tenant_id: int, payload: NonWorkingPeriodSetCreate) -> NonWorkingPeriodSet:
        period_set = NonWorkingPeriodSet(tenant_id=tenant_id, **payload.model_dump())
        self.db.add(period_set)
        self.db.commit()
        self.db.refresh(period_set)
        return period_set

    def update_set(self, period_set: NonWorkingPeriodSet, payload: NonWorkingPeriodSetUpdate) -> NonWorkingPeriodSet:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(period_set, field, value)
        self.db.add(period_set)
        self.db.commit()
        self.db.refresh(period_set)
        return period_set

    def delete_set(self, period_set: NonWorkingPeriodSet) -> None:
        self.db.delete(period_set)
        self.db.commit()

    def count_employees_for_set(self, tenant_id: int, period_set_id: int) -> int:
        stmt = select(func.count(Employee.id)).where(
            Employee.tenant_id == tenant_id,
            Employee.non_working_period_set_id == period_set_id,
        )
        return int(self.db.scalar(stmt) or 0)

    def list_periods_for_set(self, tenant_id: int, period_set_id: int) -> list[NonWorkingPeriod]:
        stmt = (
            select(NonWorkingPeriod)
            .where(
                NonWorkingPeriod.tenant_id == tenant_id,
                NonWorkingPeriod.non_working_period_set_id == period_set_id,
            )
            .order_by(NonWorkingPeriod.start_date.asc(), NonWorkingPeriod.end_date.asc(), NonWorkingPeriod.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def get_period_for_set(self, tenant_id: int, period_set_id: int, period_id: int) -> NonWorkingPeriod | None:
        stmt = select(NonWorkingPeriod).where(
            NonWorkingPeriod.tenant_id == tenant_id,
            NonWorkingPeriod.non_working_period_set_id == period_set_id,
            NonWorkingPeriod.id == period_id,
        )
        return self.db.scalar(stmt)

    def create_period(self, tenant_id: int, period_set_id: int, payload: NonWorkingPeriodCreate) -> NonWorkingPeriod:
        period = NonWorkingPeriod(
            tenant_id=tenant_id,
            non_working_period_set_id=period_set_id,
            **payload.model_dump(),
        )
        self.db.add(period)
        self.db.commit()
        self.db.refresh(period)
        return period

    def update_period(self, period: NonWorkingPeriod, payload: NonWorkingPeriodUpdate) -> NonWorkingPeriod:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(period, field, value)
        self.db.add(period)
        self.db.commit()
        self.db.refresh(period)
        return period

    def delete_period(self, period: NonWorkingPeriod) -> None:
        self.db.delete(period)
        self.db.commit()

    def has_overlapping_period(
        self,
        *,
        tenant_id: int,
        period_set_id: int,
        start_date: date,
        end_date: date,
        exclude_period_id: int | None = None,
    ) -> bool:
        conditions = [
            NonWorkingPeriod.tenant_id == tenant_id,
            NonWorkingPeriod.non_working_period_set_id == period_set_id,
            and_(
                NonWorkingPeriod.start_date <= end_date,
                NonWorkingPeriod.end_date >= start_date,
            ),
        ]
        if exclude_period_id is not None:
            conditions.append(NonWorkingPeriod.id != exclude_period_id)

        stmt = select(NonWorkingPeriod.id).where(*conditions).limit(1)
        return self.db.scalar(stmt) is not None

    def get_period_covering_date(self, tenant_id: int, period_set_id: int, target_date: date) -> NonWorkingPeriod | None:
        stmt = (
            select(NonWorkingPeriod)
            .where(
                NonWorkingPeriod.tenant_id == tenant_id,
                NonWorkingPeriod.non_working_period_set_id == period_set_id,
                NonWorkingPeriod.start_date <= target_date,
                NonWorkingPeriod.end_date >= target_date,
            )
            .order_by(NonWorkingPeriod.start_date.asc(), NonWorkingPeriod.id.asc())
            .limit(1)
        )
        return self.db.scalar(stmt)

    def exists_date_in_set(self, tenant_id: int, period_set_id: int, target_date: date) -> bool:
        stmt = (
            select(NonWorkingPeriod.id)
            .where(
                NonWorkingPeriod.tenant_id == tenant_id,
                NonWorkingPeriod.non_working_period_set_id == period_set_id,
                NonWorkingPeriod.start_date <= target_date,
                NonWorkingPeriod.end_date >= target_date,
            )
            .limit(1)
        )
        return self.db.scalar(stmt) is not None

    def list_periods_overlapping_range(
        self,
        tenant_id: int,
        period_set_id: int,
        *,
        from_date: date,
        to_date: date,
    ) -> list[NonWorkingPeriod]:
        stmt = (
            select(NonWorkingPeriod)
            .where(
                NonWorkingPeriod.tenant_id == tenant_id,
                NonWorkingPeriod.non_working_period_set_id == period_set_id,
                NonWorkingPeriod.start_date <= to_date,
                NonWorkingPeriod.end_date >= from_date,
            )
            .order_by(NonWorkingPeriod.start_date.asc(), NonWorkingPeriod.id.asc())
        )
        return list(self.db.scalars(stmt).all())
