from fastapi import HTTPException, status

from backend.models.employee import Employee
from backend.repositories.employee_repository import EmployeeRepository
from backend.repositories.holiday_set_repository import HolidaySetRepository
from backend.repositories.non_working_period_set_repository import NonWorkingPeriodSetRepository
from backend.repositories.user_repository import UserRepository
from backend.repositories.working_time_model_repository import WorkingTimeModelRepository
from backend.schemas.employee import EmployeeCreate, EmployeeUpdate, EmployeeUserOptionRead


class EmployeeService:
    def __init__(
        self,
        repository: EmployeeRepository,
        user_repository: UserRepository,
        working_time_model_repository: WorkingTimeModelRepository,
        holiday_set_repository: HolidaySetRepository,
        non_working_period_set_repository: NonWorkingPeriodSetRepository,
    ) -> None:
        self.repository = repository
        self.user_repository = user_repository
        self.working_time_model_repository = working_time_model_repository
        self.holiday_set_repository = holiday_set_repository
        self.non_working_period_set_repository = non_working_period_set_repository

    def list_employees(self, tenant_id: int) -> list[Employee]:
        return self.repository.list_by_tenant(tenant_id)

    def list_user_options(self, tenant_id: int, without_employee_only: bool) -> list[EmployeeUserOptionRead]:
        rows = self.user_repository.list_with_employee_status_for_tenant(tenant_id)
        result: list[EmployeeUserOptionRead] = []
        for user, has_employee in rows:
            if without_employee_only and has_employee:
                continue
            result.append(
                EmployeeUserOptionRead(
                    id=user.id,
                    email=user.email,
                    full_name=user.full_name,
                    keycloak_user_id=user.keycloak_user_id,
                    role=user.role,
                    has_employee=has_employee,
                )
            )
        return result

    def create_employee(self, tenant_id: int, payload: EmployeeCreate) -> Employee:
        user = self.user_repository.get_by_id(payload.user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ungültige user_id")
        if user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Benutzer gehört nicht zum aktuellen Tenant",
            )
        existing_employee = self.repository.get_by_user_id(tenant_id, payload.user_id)
        if existing_employee is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Für diesen Benutzer existiert bereits ein Mitarbeiterprofil",
            )

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
