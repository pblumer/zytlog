from datetime import date

from sqlalchemy import and_, extract, select
from sqlalchemy.orm import Session

from backend.models.holiday import Holiday
from backend.schemas.holiday import HolidayCreate, HolidayUpdate


class HolidayRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_tenant(self, tenant_id: int, *, year: int | None = None) -> list[Holiday]:
        stmt = select(Holiday).where(Holiday.tenant_id == tenant_id)
        if year is not None:
            stmt = stmt.where(extract("year", Holiday.date) == year)
        stmt = stmt.order_by(Holiday.date.asc(), Holiday.id.asc())
        return list(self.db.scalars(stmt).all())

    def create_for_tenant(self, tenant_id: int, payload: HolidayCreate) -> Holiday:
        holiday = Holiday(tenant_id=tenant_id, **payload.model_dump())
        self.db.add(holiday)
        self.db.commit()
        self.db.refresh(holiday)
        return holiday

    def get_by_id_for_tenant(self, tenant_id: int, holiday_id: int) -> Holiday | None:
        stmt = select(Holiday).where(Holiday.tenant_id == tenant_id, Holiday.id == holiday_id)
        return self.db.scalar(stmt)

    def get_by_tenant_and_date(self, tenant_id: int, target_date: date) -> Holiday | None:
        stmt = select(Holiday).where(
            Holiday.tenant_id == tenant_id,
            Holiday.date == target_date,
            Holiday.active.is_(True),
        )
        return self.db.scalar(stmt)

    def list_active_dates_in_range(self, tenant_id: int, *, from_date: date, to_date: date) -> set[date]:
        stmt = select(Holiday.date).where(
            and_(
                Holiday.tenant_id == tenant_id,
                Holiday.active.is_(True),
                Holiday.date >= from_date,
                Holiday.date <= to_date,
            )
        )
        return set(self.db.scalars(stmt).all())

    def update(self, holiday: Holiday, payload: HolidayUpdate) -> Holiday:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(holiday, field, value)
        self.db.add(holiday)
        self.db.commit()
        self.db.refresh(holiday)
        return holiday

    def delete(self, holiday: Holiday) -> None:
        self.db.delete(holiday)
        self.db.commit()
