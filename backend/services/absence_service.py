from datetime import date

from fastapi import HTTPException, status

from backend.models.absence import Absence
from backend.models.employee import Employee
from backend.models.enums import AbsenceDurationType, AbsenceType
from backend.repositories.absence_repository import AbsenceRepository
from backend.repositories.employee_repository import EmployeeRepository
from backend.schemas.absence import AbsenceCreate, AbsenceUpdate
from backend.schemas.time_tracking import DayAbsenceContext


class AbsenceService:
    def __init__(self, repository: AbsenceRepository, employee_repository: EmployeeRepository) -> None:
        self.repository = repository
        self.employee_repository = employee_repository

    def list_absences(
        self,
        *,
        tenant_id: int,
        employee_id: int | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[Absence]:
        return self.repository.list_by_tenant(
            tenant_id=tenant_id,
            employee_id=employee_id,
            from_date=from_date,
            to_date=to_date,
        )

    def create_absence(
        self,
        *,
        tenant_id: int,
        payload: AbsenceCreate,
        requester_user_id: int,
        force_employee_id: int | None = None,
    ) -> Absence:
        employee_id = force_employee_id if force_employee_id is not None else payload.employee_id
        if employee_id is None:
            employee = self.employee_repository.get_by_user_id(tenant_id, requester_user_id)
            if employee is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found")
            employee_id = employee.id
        employee = self._get_employee_or_404(tenant_id=tenant_id, employee_id=employee_id)
        self._validate_payload(employee=employee, payload=payload)
        self._reject_overlap(tenant_id=tenant_id, employee_id=employee_id, start_date=payload.start_date, end_date=payload.end_date)
        return self.repository.create_for_tenant(tenant_id=tenant_id, payload=payload, employee_id=employee_id)

    def update_absence(self, *, tenant_id: int, absence_id: int, payload: AbsenceUpdate) -> Absence:
        absence = self.repository.get_by_id_for_tenant(tenant_id=tenant_id, absence_id=absence_id)
        if absence is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Absence not found")

        employee_id = payload.employee_id if payload.employee_id is not None else absence.employee_id
        employee = self._get_employee_or_404(tenant_id=tenant_id, employee_id=employee_id)
        absence_type = payload.absence_type if payload.absence_type is not None else absence.absence_type
        start_date = payload.start_date if payload.start_date is not None else absence.start_date
        end_date = payload.end_date if payload.end_date is not None else absence.end_date
        duration_type = payload.duration_type if payload.duration_type is not None else absence.duration_type
        merged_payload = AbsenceCreate(
            employee_id=employee_id,
            absence_type=absence_type,
            start_date=start_date,
            end_date=end_date,
            duration_type=duration_type,
            note=payload.note if payload.note is not None else absence.note,
        )
        self._validate_payload(employee=employee, payload=merged_payload)
        self._reject_overlap(
            tenant_id=tenant_id,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            exclude_absence_id=absence.id,
        )
        return self.repository.update(
            absence,
            employee_id=employee_id,
            absence_type=absence_type,
            start_date=start_date,
            end_date=end_date,
            duration_type=duration_type,
            note=payload.note if payload.note is not None else absence.note,
        )

    def delete_absence(self, *, tenant_id: int, absence_id: int) -> None:
        absence = self.repository.get_by_id_for_tenant(tenant_id=tenant_id, absence_id=absence_id)
        if absence is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Absence not found")
        self.repository.delete(absence)

    def get_absence_context_for_day(self, *, tenant_id: int, employee_id: int, target_date: date) -> DayAbsenceContext | None:
        absences = self.repository.list_covering_date(
            tenant_id=tenant_id,
            employee_id=employee_id,
            target_date=target_date,
        )
        if not absences:
            return None
        absence = absences[0]
        return DayAbsenceContext(
            type=absence.absence_type.value,
            label=self._absence_label(absence.absence_type),
            duration_type=absence.duration_type.value,
        )

    def _validate_payload(self, *, employee: Employee, payload: AbsenceCreate) -> None:
        if payload.end_date < payload.start_date:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="end_date must not be before start_date")
        if payload.duration_type in {AbsenceDurationType.HALF_DAY_AM, AbsenceDurationType.HALF_DAY_PM}:
            if payload.start_date != payload.end_date:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="half-day absences must be single-day",
                )
        if payload.start_date < employee.entry_date:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Absence starts before employee entry date")
        if employee.exit_date is not None and payload.end_date > employee.exit_date:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Absence ends after employee exit date")

    def _reject_overlap(
        self,
        *,
        tenant_id: int,
        employee_id: int,
        start_date: date,
        end_date: date,
        exclude_absence_id: int | None = None,
    ) -> None:
        overlap = self.repository.find_overlap(
            tenant_id=tenant_id,
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            exclude_absence_id=exclude_absence_id,
        )
        if overlap is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Overlapping absence already exists")

    def _get_employee_or_404(self, *, tenant_id: int, employee_id: int) -> Employee:
        employee = self.employee_repository.get_by_id_for_tenant(tenant_id, employee_id)
        if employee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
        return employee

    def _absence_label(self, absence_type: AbsenceType) -> str:
        if absence_type == AbsenceType.VACATION:
            return "Vacation"
        return "Sickness"
