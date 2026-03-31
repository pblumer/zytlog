from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.repositories.non_working_period_set_repository import NonWorkingPeriodSetRepository
from backend.repositories.working_time_model_repository import WorkingTimeModelRepository
from backend.schemas.employee import EmployeeCreate, EmployeeUpdate


class EmployeeService:
    def __init__(
        self,
        repository: EmployeeRepository,
        working_time_model_repository: WorkingTimeModelRepository,
        holiday_set_repository: HolidaySetRepository,
        non_working_period_set_repository: NonWorkingPeriodSetRepository,
    ) -> None:
        self.repository = repository
        self.working_time_model_repository = working_time_model_repository
        self.holiday_set_repository = holiday_set_repository
        self.non_working_period_set_repository = non_working_period_set_repository

    def list_employees(self, tenant_id: int) -> list[Employee]:
        return self.repository.list_by_tenant(tenant_id)

    def create_employee(self, tenant_id: int, payload: EmployeeCreate) -> Employee:
        if payload.working_time_model_id is not None:
            model = self.working_time_model_repository.get_by_id_for_tenant(tenant_id, payload.working_time_model_id)
            if model is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiges Arbeitszeitmodell")
        if payload.holiday_set_id is not None:
            holiday_set = self.holiday_set_repository.get_by_id_for_tenant(tenant_id, payload.holiday_set_id)
            if holiday_set is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiger Feiertagssatz")
        if payload.non_working_period_set_id is not None:
            non_working_period_set = self.non_working_period_set_repository.get_set_for_tenant(
                tenant_id,
                payload.non_working_period_set_id,
            )
            if non_working_period_set is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiges Arbeitsfrei-Set")
        return self.repository.create_for_tenant(tenant_id, payload)

    def update_employee(self, tenant_id: int, employee_id: int, payload: EmployeeUpdate) -> Employee:
        employee = self.repository.get_by_id_for_tenant(tenant_id, employee_id)
        if employee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mitarbeiter nicht gefunden")

        if payload.working_time_model_id is not None:
            model = self.working_time_model_repository.get_by_id_for_tenant(tenant_id, payload.working_time_model_id)
            if model is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiges Arbeitszeitmodell")
        if payload.holiday_set_id is not None:
            holiday_set = self.holiday_set_repository.get_by_id_for_tenant(tenant_id, payload.holiday_set_id)
            if holiday_set is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiger Feiertagssatz")
        if payload.non_working_period_set_id is not None:
            non_working_period_set = self.non_working_period_set_repository.get_set_for_tenant(
                tenant_id,
                payload.non_working_period_set_id,
            )
            if non_working_period_set is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültiges Arbeitsfrei-Set")

        return self.repository.update(employee, payload)
