from datetime import date, datetime, timezone

from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.models.enums import TimeStampEventType
from backend.models.time_stamp_event import TimeStampEvent
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import ClockStatus, CurrentClockStatusRead


class TimeTrackingService:
    def __init__(self, repository: TimeStampEventRepository) -> None:
        self.repository = repository

    def clock_in(self, *, tenant_id: int, employee: Employee, event_timestamp: datetime | None = None) -> TimeStampEvent:
        return self._create_event(
            tenant_id=tenant_id,
            employee_id=employee.id,
            event_type=TimeStampEventType.CLOCK_IN,
            event_timestamp=event_timestamp,
        )

    def clock_out(
        self, *, tenant_id: int, employee: Employee, event_timestamp: datetime | None = None
    ) -> TimeStampEvent:
        return self._create_event(
            tenant_id=tenant_id,
            employee_id=employee.id,
            event_type=TimeStampEventType.CLOCK_OUT,
            event_timestamp=event_timestamp,
        )

    def current_status(self, *, tenant_id: int, employee: Employee) -> CurrentClockStatusRead:
        last_event = self.repository.get_last_clock_event(tenant_id=tenant_id, employee_id=employee.id)
        is_clocked_in = last_event is not None and last_event.type == TimeStampEventType.CLOCK_IN
        return CurrentClockStatusRead(
            employee_id=employee.id,
            status=ClockStatus.CLOCKED_IN if is_clocked_in else ClockStatus.CLOCKED_OUT,
            last_event_type=last_event.type if last_event else None,
            last_event_timestamp=last_event.timestamp if last_event else None,
        )

    def list_my_events(
        self, *, tenant_id: int, employee: Employee, from_date: date, to_date: date
    ) -> list[TimeStampEvent]:
        if from_date > to_date:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date range")

        return self.repository.list_clock_events(
            tenant_id=tenant_id,
            employee_id=employee.id,
            from_date=from_date,
            to_date=to_date,
        )

    def _create_event(
        self,
        *,
        tenant_id: int,
        employee_id: int,
        event_type: TimeStampEventType,
        event_timestamp: datetime | None,
    ) -> TimeStampEvent:
        last_event = self.repository.get_last_clock_event(tenant_id=tenant_id, employee_id=employee_id)
        if last_event and last_event.type == event_type:
            if event_type == TimeStampEventType.CLOCK_IN:
                detail = "Invalid stamp sequence: already clocked in"
            else:
                detail = "Invalid stamp sequence: already clocked out"
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

        if event_type == TimeStampEventType.CLOCK_OUT and last_event is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot clock out without prior clock in")

        stamp_time = event_timestamp or datetime.now(timezone.utc)

        return self.repository.create_event(
            tenant_id=tenant_id,
            employee_id=employee_id,
            event_type=event_type,
            event_timestamp=stamp_time,
        )
