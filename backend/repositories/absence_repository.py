from datetime import date

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from backend.models.absence import Absence
from backend.schemas.absence import AbsenceCreate


class AbsenceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_tenant(
        self,
        *,
        tenant_id: int,
        employee_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Absence]:
        stmt = select(Absence).where(Absence.tenant_id == tenant_id)
        if employee_id is not None:
            stmt = stmt.where(Absence.employee_id == employee_id)
        if from_date is not None:
            stmt = stmt.where(Absence.end_date >= from_date)
        if to_date is not None:
            stmt = stmt.where(Absence.start_date <= to_date)
        stmt = stmt.order_by(Absence.start_date.desc(), Absence.id.desc())
        return list(self.db.scalars(stmt).all())

    def create_for_tenant(self, *, tenant_id: int, payload: AbsenceCreate, employee_id: int) -> Absence:
        absence = Absence(
            tenant_id=tenant_id,
            employee_id=employee_id,
            absence_type=payload.absence_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            duration_type=payload.duration_type,
            note=payload.note,
        )
        self.db.add(absence)
        self.db.commit()
        self.db.refresh(absence)
        return absence

    def get_by_id_for_tenant(self, *, tenant_id: int, absence_id: int) -> Absence | None:
        stmt = select(Absence).where(Absence.tenant_id == tenant_id, Absence.id == absence_id)
        return self.db.scalar(stmt)

    def update(self, absence: Absence, **updates: object) -> Absence:
        for key, value in updates.items():
            setattr(absence, key, value)
        self.db.add(absence)
        self.db.commit()
        self.db.refresh(absence)
        return absence

    def delete(self, absence: Absence) -> None:
        self.db.delete(absence)
        self.db.commit()

    def find_overlap(
        self,
        *,
        tenant_id: int,
        employee_id: int,
        start_date: date,
        end_date: date,
        exclude_absence_id: int | None = None,
    ) -> Absence | None:
        stmt = select(Absence).where(
            Absence.tenant_id == tenant_id,
            Absence.employee_id == employee_id,
            and_(Absence.start_date <= end_date, Absence.end_date >= start_date),
        )
        if exclude_absence_id is not None:
            stmt = stmt.where(Absence.id != exclude_absence_id)
        stmt = stmt.order_by(Absence.start_date.asc(), Absence.id.asc())
        return self.db.scalar(stmt)

    def list_covering_date(self, *, tenant_id: int, employee_id: int, target_date: date) -> list[Absence]:
        stmt = (
            select(Absence)
            .where(
                Absence.tenant_id == tenant_id,
                Absence.employee_id == employee_id,
                Absence.start_date <= target_date,
                Absence.end_date >= target_date,
            )
            .order_by(Absence.start_date.asc(), Absence.id.asc())
        )
        return list(self.db.scalars(stmt).all())
