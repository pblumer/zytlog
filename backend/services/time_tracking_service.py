from datetime import date, datetime, timezone

from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.models.enums import TimeStampEventType, UserRole
from backend.models.time_stamp_event import TimeStampEvent
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import ClockStatus, CurrentClockStatusRead, TimeStampEventUpdate


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

    def update_event(
        self,
        *,
        tenant_id: int,
        event_id: int,
        payload: TimeStampEventUpdate,
        actor_role: UserRole,
        actor_employee_id: int | None,
        actor_user_id: int,
    ) -> TimeStampEvent:
        timestamp_provided = "timestamp" in payload.model_fields_set
        comment_provided = "comment" in payload.model_fields_set
        if not timestamp_provided and not comment_provided:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields provided to update")

        event = self.repository.get_by_id(tenant_id=tenant_id, event_id=event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time stamp event not found")

        if actor_role != UserRole.ADMIN and actor_employee_id != event.employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to edit this time stamp event")

        next_timestamp = payload.timestamp if timestamp_provided else event.timestamp
        next_comment = payload.comment if comment_provided else event.comment
        if timestamp_provided:
            self._validate_employee_sequence(
                tenant_id=tenant_id,
                employee_id=event.employee_id,
                event_id=event.id,
                next_timestamp=next_timestamp,
            )
        # TODO(audit): Persist richer correction metadata (corrected_by_user_id / correction note).
        _ = actor_user_id
        return self.repository.update_event(event=event, timestamp=next_timestamp, comment=next_comment)

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

    def _validate_employee_sequence(
        self,
        *,
        tenant_id: int,
        employee_id: int,
        event_id: int,
        next_timestamp: datetime,
    ) -> None:
        events = self.repository.list_all_clock_events(tenant_id=tenant_id, employee_id=employee_id)

        reordered = [
            (next_timestamp if event.id == event_id else event.timestamp, event.id, event.type)
            for event in events
        ]
        reordered.sort(key=lambda item: (item[0], item[1]))

        expected_type = TimeStampEventType.CLOCK_IN
        open_clock_in_timestamp: datetime | None = None
        for event_timestamp, current_event_id, event_type in reordered:
            if event_type != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Invalid stamp sequence around event {current_event_id}: expected {expected_type.value}",
                )

            if event_type == TimeStampEventType.CLOCK_IN:
                open_clock_in_timestamp = event_timestamp
                expected_type = TimeStampEventType.CLOCK_OUT
                continue

            if open_clock_in_timestamp is None or event_timestamp < open_clock_in_timestamp:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Correction would create a negative work interval",
                )
            expected_type = TimeStampEventType.CLOCK_IN
