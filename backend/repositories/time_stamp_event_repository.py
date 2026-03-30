from datetime import date, datetime, time

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.enums import TimeStampEventType
from backend.models.time_stamp_event import TimeStampEvent


class TimeStampEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_event(
        self,
        *,
        tenant_id: int,
        employee_id: int,
        event_type: TimeStampEventType,
        event_timestamp: datetime,
        source: str = "web",
        comment: str | None = None,
    ) -> TimeStampEvent:
        event = TimeStampEvent(
            tenant_id=tenant_id,
            employee_id=employee_id,
            type=event_type,
            timestamp=event_timestamp,
            source=source,
            comment=comment,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_last_clock_event(self, *, tenant_id: int, employee_id: int) -> TimeStampEvent | None:
        stmt = (
            select(TimeStampEvent)
            .where(
                TimeStampEvent.tenant_id == tenant_id,
                TimeStampEvent.employee_id == employee_id,
                TimeStampEvent.type.in_([TimeStampEventType.CLOCK_IN, TimeStampEventType.CLOCK_OUT]),
            )
            .order_by(TimeStampEvent.timestamp.desc(), TimeStampEvent.id.desc())
        )
        return self.db.scalar(stmt)

    def list_clock_events(
        self,
        *,
        tenant_id: int,
        employee_id: int,
        from_date: date,
        to_date: date,
    ) -> list[TimeStampEvent]:
        start = datetime.combine(from_date, time.min)
        end = datetime.combine(to_date, time.max)
        stmt = (
            select(TimeStampEvent)
            .where(
                TimeStampEvent.tenant_id == tenant_id,
                TimeStampEvent.employee_id == employee_id,
                TimeStampEvent.type.in_([TimeStampEventType.CLOCK_IN, TimeStampEventType.CLOCK_OUT]),
                TimeStampEvent.timestamp >= start,
                TimeStampEvent.timestamp <= end,
            )
            .order_by(TimeStampEvent.timestamp.asc(), TimeStampEvent.id.asc())
        )
        return list(self.db.scalars(stmt).all())

    def list_clock_events_for_day(
        self, *, tenant_id: int, employee_id: int, target_date: date
    ) -> list[TimeStampEvent]:
        return self.list_clock_events(
            tenant_id=tenant_id,
            employee_id=employee_id,
            from_date=target_date,
            to_date=target_date,
        )
