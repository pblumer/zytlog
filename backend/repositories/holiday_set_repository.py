from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.employee import Employee
from backend.models.holiday import Holiday
from backend.models.holiday_set import HolidaySet
from backend.models.tenant import Tenant
from backend.schemas.holiday_set import HolidaySetCreate, HolidaySetUpdate


class HolidaySetRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_tenant_with_counts(self, tenant_id: int) -> list[tuple[HolidaySet, int]]:
        stmt = (
            select(HolidaySet, func.count(Holiday.id))
            .outerjoin(Holiday, Holiday.holiday_set_id == HolidaySet.id)
            .where(HolidaySet.tenant_id == tenant_id)
            .group_by(HolidaySet.id)
            .order_by(HolidaySet.name.asc(), HolidaySet.id.asc())
        )
        return [(row[0], int(row[1])) for row in self.db.execute(stmt).all()]

    def get_by_id_for_tenant(self, tenant_id: int, holiday_set_id: int) -> HolidaySet | None:
        stmt = select(HolidaySet).where(HolidaySet.tenant_id == tenant_id, HolidaySet.id == holiday_set_id)
        return self.db.scalar(stmt)

    def create_for_tenant(self, tenant_id: int, payload: HolidaySetCreate) -> HolidaySet:
        holiday_set = HolidaySet(tenant_id=tenant_id, **payload.model_dump())
        self.db.add(holiday_set)
        self.db.commit()
        self.db.refresh(holiday_set)
        return holiday_set

    def update(self, holiday_set: HolidaySet, payload: HolidaySetUpdate) -> HolidaySet:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(holiday_set, field, value)
        self.db.add(holiday_set)
        self.db.commit()
        self.db.refresh(holiday_set)
        return holiday_set

    def delete(self, holiday_set: HolidaySet) -> None:
        self.db.delete(holiday_set)
        self.db.commit()

    def count_employees_for_holiday_set(self, tenant_id: int, holiday_set_id: int) -> int:
        stmt = select(func.count(Employee.id)).where(
            Employee.tenant_id == tenant_id,
            Employee.holiday_set_id == holiday_set_id,
        )
        return int(self.db.scalar(stmt) or 0)

    def count_holidays_for_holiday_set(self, tenant_id: int, holiday_set_id: int) -> int:
        stmt = select(func.count(Holiday.id)).where(
            Holiday.tenant_id == tenant_id,
            Holiday.holiday_set_id == holiday_set_id,
        )
        return int(self.db.scalar(stmt) or 0)

    def tenant_uses_as_default(self, tenant_id: int, holiday_set_id: int) -> bool:
        stmt = select(Tenant.id).where(
            Tenant.id == tenant_id,
            Tenant.default_holiday_set_id == holiday_set_id,
        )
        return self.db.scalar(stmt) is not None
