from datetime import date, datetime, timezone
import logging

from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.models.enums import TimeStampEventType, UserRole
from backend.models.time_stamp_event import TimeStampEvent
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.schemas.time_tracking import ClockStatus, CurrentClockStatusRead, ManualTimeStampCreate, TimeStampEventUpdate

logger = logging.getLogger(__name__)


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
            self._validate_employee_day_sequences_for_update(
                tenant_id=tenant_id,
                employee_id=event.employee_id,
                event_id=event.id,
                next_timestamp=next_timestamp,
            )
        # TODO(audit): Persist richer correction metadata (corrected_by_user_id / correction note).
        _ = actor_user_id
        return self.repository.update_event(event=event, timestamp=next_timestamp, comment=next_comment)

    def create_manual_event(
        self,
        *,
        tenant_id: int,
        employee: Employee,
        payload: ManualTimeStampCreate,
    ) -> TimeStampEvent:
        if payload.type not in (TimeStampEventType.CLOCK_IN, TimeStampEventType.CLOCK_OUT):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Manual entry supports only clock_in and clock_out",
            )

        existing_same_day = self.repository.list_clock_events_for_day(
            tenant_id=tenant_id,
            employee_id=employee.id,
            target_date=payload.timestamp.date(),
        )
        self._validate_day_sequence_for_events(
            events=existing_same_day,
            candidate_timestamp=payload.timestamp,
            candidate_type=payload.type,
        )

        return self.repository.create_event(
            tenant_id=tenant_id,
            employee_id=employee.id,
            event_type=payload.type,
            event_timestamp=payload.timestamp,
            source="manual_entry",
            comment=payload.comment,
        )

    def delete_event(
        self,
        *,
        tenant_id: int,
        event_id: int,
        actor_role: UserRole,
        actor_employee_id: int | None,
        actor_user_id: int,
    ) -> TimeStampEvent:
        event = self.repository.get_by_id(tenant_id=tenant_id, event_id=event_id)
        if event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time stamp event not found")

        if actor_role != UserRole.ADMIN and actor_employee_id != event.employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to delete this time stamp event",
            )

        same_day_events = self.repository.list_clock_events_for_day(
            tenant_id=tenant_id,
            employee_id=event.employee_id,
            target_date=event.timestamp.date(),
        )

        day_is_currently_valid = self._is_day_sequence_valid(
            same_day_events=same_day_events,
            day=event.timestamp.date(),
        )

        if not day_is_currently_valid:
            logger.info("Deletion allowed despite invalid day (recovery mode)")
            # TODO(audit): Persist deletion metadata for traceability.
            _ = actor_user_id
            self.repository.delete_event(event=event)
            return event

        reordered = [
            (day_event.timestamp, day_event.id, day_event.type)
            for day_event in same_day_events
            if day_event.id != event.id
        ]
        try:
            self._validate_reordered_day_sequence(reordered, day=event.timestamp.date())
        except HTTPException as exc:
            if exc.status_code == status.HTTP_409_CONFLICT:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Dieser Eintrag kann nicht gelöscht werden, da die Tagessequenz dadurch ungültig würde.",
                ) from exc
            raise

        # TODO(audit): Persist deletion metadata for traceability.
        _ = actor_user_id
        self.repository.delete_event(event=event)
        return event

    def _is_day_sequence_valid(
        self,
        *,
        same_day_events: list[TimeStampEvent],
        day: date,
    ) -> bool:
        reordered = [(day_event.timestamp, day_event.id, day_event.type) for day_event in same_day_events]
        try:
            self._validate_reordered_day_sequence(reordered, day=day)
        except HTTPException as exc:
            if exc.status_code == status.HTTP_409_CONFLICT:
                return False
            raise
        return True

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
        existing = self.repository.list_clock_events_for_day(
            tenant_id=tenant_id,
            employee_id=employee_id,
            target_date=stamp_time.date(),
        )
        self._validate_day_sequence_for_events(
            events=existing,
            candidate_timestamp=stamp_time,
            candidate_type=event_type,
        )

        return self.repository.create_event(
            tenant_id=tenant_id,
            employee_id=employee_id,
            event_type=event_type,
            event_timestamp=stamp_time,
        )

    def _validate_employee_day_sequences_for_update(
        self,
        *,
        tenant_id: int,
        employee_id: int,
        event_id: int,
        next_timestamp: datetime,
    ) -> None:
        events = self.repository.list_all_clock_events(tenant_id=tenant_id, employee_id=employee_id)
        current_event = next((event for event in events if event.id == event_id), None)
        if current_event is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Time stamp event not found")

        reordered_all = [
            (next_timestamp if event.id == event_id else event.timestamp, event.id, event.type)
            for event in events
        ]
        affected_dates = {current_event.timestamp.date(), next_timestamp.date()}
        for target_date in affected_dates:
            reordered_for_day = [item for item in reordered_all if item[0].date() == target_date]
            self._validate_reordered_day_sequence(reordered_for_day, day=target_date)

    def _validate_day_sequence_for_events(
        self,
        *,
        events: list[TimeStampEvent],
        candidate_timestamp: datetime,
        candidate_type: TimeStampEventType,
    ) -> None:
        reordered = [(event.timestamp, event.id, event.type) for event in events]
        reordered.append((candidate_timestamp, 0, candidate_type))
        self._validate_reordered_day_sequence(reordered, day=candidate_timestamp.date())

    def _validate_reordered_day_sequence(
        self,
        reordered: list[tuple[datetime, int, TimeStampEventType]],
        *,
        day: date,
    ) -> None:
        reordered.sort(key=lambda item: (item[0], item[1]))

        expected_type = TimeStampEventType.CLOCK_IN
        open_clock_in_timestamp: datetime | None = None
        for event_timestamp, current_event_id, event_type in reordered:
            if event_type != expected_type:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Invalid same-day stamp sequence on {day.isoformat()} around event "
                        f"{current_event_id}: expected {expected_type.value}"
                    ),
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
