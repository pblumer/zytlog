from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.db.base import Base
from backend.models.employee import Employee
from backend.models.enums import UserRole
from backend.models.holiday import Holiday
from backend.models.holiday_set import HolidaySet
from backend.models.tenant import Tenant
from backend.models.user import User
from backend.models.working_time_model import WorkingTimeModel
from backend.repositories.absence_repository import AbsenceRepository
from backend.repositories.holiday_repository import HolidayRepository
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository
from backend.services.absence_service import AbsenceService
from backend.services.daily_account_service import DailyAccountService
from backend.services.holiday_service import HolidayService
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
    default_holiday_set = HolidaySet(tenant_id=tenant.id, name="Standard", source="manual", active=True)
    session.add(default_holiday_set)
    session.flush()
    tenant.default_holiday_set_id = default_holiday_set.id

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
    _ = persisted_employee.working_time_model

    holiday_service = HolidayService(HolidayRepository(session))
    service = DailyAccountService(
        TimeStampEventRepository(session),
        holiday_service,
        AbsenceService(AbsenceRepository(session), EmployeeRepository(session)),
    )
    return session, tenant.id, persisted_employee, service, default_holiday_set


def test_100_percent_employee_with_standard_monday_to_friday_target() -> None:
    session, tenant_id, employee, service, _ = _build_service()

    monday_account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 3, 30))
    sunday_account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 4, 5))

    assert monday_account.target_minutes == 483
    assert sunday_account.target_minutes == 0
    session.close()


def test_holiday_on_workday_sets_target_minutes_to_zero() -> None:
    session, tenant_id, employee, service, holiday_set = _build_service()
    session.add(Holiday(tenant_id=tenant_id, holiday_set_id=holiday_set.id, date=date(2026, 3, 30), name="Berchtoldstag", active=True))
    session.commit()

    account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 3, 30))

    assert account.target_minutes == 0
    assert account.is_holiday is True
    assert account.holiday_name == "Berchtoldstag"
    session.close()


def test_holiday_on_non_working_weekday_stays_zero_without_distorting_distribution() -> None:
    session, tenant_id, employee, service, holiday_set = _build_service()
    session.add(Holiday(tenant_id=tenant_id, holiday_set_id=holiday_set.id, date=date(2026, 4, 5), name="Sonntagsfeiertag", active=True))
    session.commit()

    monday = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 3, 30))
    sunday = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 4, 5))

    assert monday.target_minutes == 483
    assert sunday.target_minutes == 0
    assert sunday.is_holiday is True
    session.close()


def test_holidays_reduce_relevant_workdays_and_raise_daily_target_distribution() -> None:
    session, tenant_id, employee, service, holiday_set = _build_service()
    session.add_all(
        [
            Holiday(tenant_id=tenant_id, holiday_set_id=holiday_set.id, date=date(2026, 1, 1), name="Neujahr", active=True),
            Holiday(tenant_id=tenant_id, holiday_set_id=holiday_set.id, date=date(2026, 1, 2), name="Berchtoldstag", active=True),
        ]
    )
    session.commit()

    account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 1, 5))

    # 2100h / (261 - 2 Feiertage) = 486.49min -> 486min
    assert account.target_minutes == 486
    session.close()


def test_80_percent_employee_with_weekday_override_distributes_annual_target_equally() -> None:
    session, tenant_id, employee, service, _ = _build_service(
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

    assert monday_account.target_minutes == 482
    assert wednesday_account.target_minutes == 0
    session.close()


def test_reporting_uses_same_daily_target_logic_consistently() -> None:
    session, tenant_id, employee, service, holiday_set = _build_service(
        employee_percentage=80,
        employee_overrides={
            "workday_monday": True,
            "workday_tuesday": True,
            "workday_wednesday": False,
            "workday_thursday": True,
            "workday_friday": True,
        },
    )
    session.add(Holiday(tenant_id=tenant_id, holiday_set_id=holiday_set.id, date=date(2026, 3, 31), name="Ferien", active=True))
    session.commit()

    reporting = ReportingService(service)
    week = reporting.get_week_overview(tenant_id=tenant_id, employee=employee, iso_year=2026, iso_week=14)

    assert week.totals.target_minutes == 1455
    tuesday = next(day for day in week.days if day.date == date(2026, 3, 31))
    wednesday = next(day for day in week.days if day.date == date(2026, 4, 1))
    assert tuesday.target_minutes == 0
    assert tuesday.is_holiday is True
    assert wednesday.target_minutes == 0
    session.close()


def test_employee_holiday_set_override_takes_precedence_over_tenant_default() -> None:
    session, tenant_id, employee, service, default_holiday_set = _build_service()
    zh_holiday_set = HolidaySet(tenant_id=tenant_id, name="ZH Standard", source="imported", active=True)
    session.add(zh_holiday_set)
    session.flush()
    employee.holiday_set_id = zh_holiday_set.id
    session.add(employee)
    session.add(Holiday(tenant_id=tenant_id, holiday_set_id=default_holiday_set.id, date=date(2026, 4, 6), name="BE Feiertag", active=True))
    session.commit()

    account = service.get_daily_account(tenant_id=tenant_id, employee=employee, target_date=date(2026, 4, 6))
    assert account.target_minutes > 0
    assert account.is_holiday is False
    session.close()
