"""Seed pragmatic local demo data for Zytlog MVP.

Usage:
    python -m backend.scripts.seed_demo
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from backend.db.session import SessionLocal
from backend.models.employee import Employee
from backend.models.enums import TenantType, TimeStampEventType, UserRole
from backend.models.tenant import Tenant
from backend.models.time_stamp_event import TimeStampEvent
from backend.models.user import User
from backend.models.working_time_model import WorkingTimeModel


def _find_or_create_tenant(slug: str = "demo-co") -> Tenant:
    with SessionLocal() as session:
        tenant = session.scalar(select(Tenant).where(Tenant.slug == slug))
        if tenant:
            return tenant

        tenant = Tenant(
            name="Demo Company",
            slug=slug,
            active=True,
            type=TenantType.DEMO,
            timezone="UTC",
        )
        session.add(tenant)
        session.commit()
        session.refresh(tenant)
        return tenant


def _find_or_create_admin(tenant_id: int) -> User:
    with SessionLocal() as session:
        admin = session.scalar(select(User).where(User.email == "admin@demo.local"))
        if admin:
            return admin

        admin = User(
            tenant_id=tenant_id,
            email="admin@demo.local",
            full_name="Demo Admin",
            keycloak_user_id="demo-admin-sub",
            role=UserRole.ADMIN,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)
        return admin


def _find_or_create_employee_user(tenant_id: int) -> User:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == "employee@demo.local"))
        if user:
            return user

        user = User(
            tenant_id=tenant_id,
            email="employee@demo.local",
            full_name="Demo Employee",
            keycloak_user_id="demo-employee-sub",
            role=UserRole.EMPLOYEE,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _find_or_create_model(tenant_id: int) -> WorkingTimeModel:
    with SessionLocal() as session:
        model = session.scalar(
            select(WorkingTimeModel).where(
                WorkingTimeModel.tenant_id == tenant_id,
                WorkingTimeModel.name == "Full Time 40h",
            )
        )
        if model:
            return model

        model = WorkingTimeModel(
            tenant_id=tenant_id,
            name="Full Time 40h",
            weekly_target_hours=40,
            default_workdays_per_week=5,
            default_workday_monday=True,
            default_workday_tuesday=True,
            default_workday_wednesday=True,
            default_workday_thursday=True,
            default_workday_friday=True,
            default_workday_saturday=False,
            default_workday_sunday=False,
            annual_target_hours=2080,
            active=True,
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        return model


def _find_or_create_employee(tenant_id: int, user_id: int, model_id: int) -> Employee:
    with SessionLocal() as session:
        employee = session.scalar(select(Employee).where(Employee.user_id == user_id))
        if employee:
            return employee

        employee = Employee(
            tenant_id=tenant_id,
            user_id=user_id,
            employee_number="E-1000",
            first_name="Demo",
            last_name="Employee",
            employment_percentage=100,
            entry_date=date(2026, 1, 1),
            working_time_model_id=model_id,
            team="Operations",
        )
        session.add(employee)
        session.commit()
        session.refresh(employee)
        return employee


def _seed_events(tenant_id: int, employee_id: int) -> int:
    with SessionLocal() as session:
        day = date.today()
        start = datetime(day.year, day.month, day.day, 8, 0, tzinfo=UTC)
        points: list[tuple[datetime, TimeStampEventType, str | None]] = [
            (start - timedelta(days=1), TimeStampEventType.CLOCK_IN, None),
            (start - timedelta(days=1) + timedelta(hours=4), TimeStampEventType.BREAK_START, "Lunch"),
            (start - timedelta(days=1) + timedelta(hours=4, minutes=30), TimeStampEventType.BREAK_END, None),
            (start - timedelta(days=1) + timedelta(hours=8, minutes=30), TimeStampEventType.CLOCK_OUT, None),
            (start, TimeStampEventType.CLOCK_IN, "Demo day start"),
            (start + timedelta(hours=4), TimeStampEventType.BREAK_START, None),
            (start + timedelta(hours=4, minutes=30), TimeStampEventType.BREAK_END, None),
            (start + timedelta(hours=8, minutes=30), TimeStampEventType.CLOCK_OUT, "Demo day end"),
        ]

        created = 0
        for timestamp, event_type, comment in points:
            exists = session.scalar(
                select(TimeStampEvent).where(
                    TimeStampEvent.tenant_id == tenant_id,
                    TimeStampEvent.employee_id == employee_id,
                    TimeStampEvent.timestamp == timestamp,
                    TimeStampEvent.type == event_type,
                )
            )
            if exists:
                continue

            session.add(
                TimeStampEvent(
                    tenant_id=tenant_id,
                    employee_id=employee_id,
                    timestamp=timestamp,
                    type=event_type,
                    source="demo_seed",
                    comment=comment,
                )
            )
            created += 1

        if created:
            session.commit()
        return created


def main() -> None:
    tenant = _find_or_create_tenant()
    _find_or_create_admin(tenant.id)
    employee_user = _find_or_create_employee_user(tenant.id)
    model = _find_or_create_model(tenant.id)
    employee = _find_or_create_employee(tenant.id, employee_user.id, model.id)
    created_events = _seed_events(tenant.id, employee.id)

    print("Seed completed")
    print(f"Tenant slug: {tenant.slug}")
    print("Users:")
    print("  - admin@demo.local (role=admin, keycloak_user_id=demo-admin-sub)")
    print("  - employee@demo.local (role=employee, keycloak_user_id=demo-employee-sub)")
    print(f"Employee id: {employee.id}")
    print(f"Events inserted this run: {created_events}")


if __name__ == "__main__":
    main()
