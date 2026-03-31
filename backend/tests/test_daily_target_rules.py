from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.db.base import Base
from backend.models.employee import Employee
from backend.models.enums import UserRole
from backend.models.tenant import Tenant
from backend.models.user import User
from backend.models.working_time_model import WorkingTimeModel
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.services.daily_account_service import DailyAccountService
from backend.services.reporting_service import ReportingService


def _build_service(*, employee_percentage: float = 100, employee_overrides: dict | None = None, exit_date: date | None = None):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    session = Session(engine)
    tenant = Tenant(name="Tenant", slug="tenant", active=True, timezone="UTC")
    session.add(tenant)
    session.flush()

    user = User(
        tenant_id=tenant.id,
        email="employee@tenant.local",
        full_name="Employee",
        keycloak_user_id="kc-employee",
        role=UserRole.EMPLOYEE,
    )
    session.add(user)
    session.flush()

    model = WorkingTimeModel(
        tenant_id=tenant.id,
        name="42h Model",
        default_workday_monday=True,
        default_workday_tuesday=True,
        default_workday_wednesday=True,
        default_workday_thursday=True,
        default_workday_friday=True,
        default_workday_saturday=False,
        default_workday_sunday=False,
        annual_target_hours=2100,
        active=True,
    )
    session.add(model)
    session.flush()

    employee_data = {
        "tenant_id": tenant.id,
        "user_id": user.id,
        "first_name": "Test",
        "last_name": "Employee",
        "employment_percentage": employee_percentage,
        "entry_date": date(2026, 1, 1),
        "exit_date": exit_date,
        "working_time_model_id": model.id,
    }
    if employee_overrides:
        employee_data.update(employee_overrides)

    employee = Employee(**employee_data)
    session.add(employee)
    session.commit()

    persisted_employee = session.get(Employee, employee.id)
    assert persisted_employee is not None
    # ensure relationship is loaded for service logic
    _ = persisted_employee.working_time_model

    service = DailyAccountService(TimeStampEventRepository(session))
    return session, tenant.id, persisted_employee, service


def test_100_percent_employee_with_standard_monday_to_friday_target() -> None:
    session, tenant_id, employee, service = _build_service()

    monday_account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 3, 30))
    sunday_account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 4, 5))

    assert monday_account.target_minutes == 483  # 2100h / 261 Arbeitstage in 2026
    assert sunday_account.target_minutes == 0
    session.close()


def test_80_percent_employee_with_weekday_override_distributes_annual_target_equally() -> None:
    session, tenant_id, employee, service = _build_service(
        employee_percentage=80,
        employee_overrides={
            "workday_monday": True,
            "workday_tuesday": True,
            "workday_wednesday": False,
            "workday_thursday": True,
            "workday_friday": True,
        },
    )

    monday_account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 3, 30))
    wednesday_account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 4, 1))

    assert monday_account.target_minutes == 482  # (2100h * 80%) / 209 Arbeitstage in 2026
    assert wednesday_account.target_minutes == 0
    session.close()


def test_non_working_weekday_results_in_zero_target_minutes() -> None:
    session, tenant_id, employee, service = _build_service(
        employee_overrides={"workday_monday": False, "workday_saturday": True}
    )

    monday_account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 3, 30))

    assert monday_account.target_minutes == 0
    session.close()


def test_date_before_entry_date_results_in_zero_target_minutes() -> None:
    session, tenant_id, employee, service = _build_service()

    account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2025, 12, 31))

    assert account.target_minutes == 0
    session.close()


def test_date_after_exit_date_results_in_zero_target_minutes() -> None:
    session, tenant_id, employee, service = _build_service(exit_date=date(2026, 6, 30))

    account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 7, 1))

    assert account.target_minutes == 0
    session.close()


def test_reporting_uses_same_daily_target_logic_consistently() -> None:
    session, tenant_id, employee, service = _build_service(
        employee_percentage=80,
        employee_overrides={
            "workday_monday": True,
            "workday_tuesday": True,
            "workday_wednesday": False,
            "workday_thursday": True,
            "workday_friday": True,
        },
    )
    reporting = ReportingService(service)

    week = reporting.get_week_overview(tenant_id=tenant_id, employee=employee, iso_year=2026, iso_week=14)

    assert week.totals.target_minutes == 1928  # 4 active days * 482
    wednesday = next(day for day in week.days if day.date == date(2026, 4, 1))
    assert wednesday.target_minutes == 0
    session.close()
