"""Seed reproducible local demo data for Zytlog.

Usage:
    python -m backend.scripts.seed_demo
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from backend.db.session import SessionLocal
from backend.models.employee import Employee
from backend.models.enums import TenantType, TimeStampEventType, UserRole
from backend.models.tenant import Tenant
from backend.models.time_stamp_event import TimeStampEvent
from backend.models.user import User
from backend.models.working_time_model import WorkingTimeModel


@dataclass(frozen=True)
class DemoIdentity:
    email: str
    full_name: str
    keycloak_sub: str
    role: UserRole
    employee_number: str
    first_name: str
    last_name: str


DEMO_IDENTITIES: tuple[DemoIdentity, ...] = (
    DemoIdentity(
        email="sysadmin@demo.local",
        full_name="Demo System Admin",
        keycloak_sub="demo-sysadmin-sub",
        role=UserRole.SYSTEM_ADMIN,
        employee_number="E-9000",
        first_name="Demo",
        last_name="SysAdmin",
    ),
    DemoIdentity(
        email="admin@demo.local",
        full_name="Demo Admin",
        keycloak_sub="demo-admin-sub",
        role=UserRole.ADMIN,
        employee_number="E-1000",
        first_name="Demo",
        last_name="Admin",
    ),
    DemoIdentity(
        email="employee@demo.local",
        full_name="Demo Employee",
        keycloak_sub="demo-employee-sub",
        role=UserRole.EMPLOYEE,
        employee_number="E-2000",
        first_name="Demo",
        last_name="Employee",
    ),
)


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


def _find_or_create_model(tenant_id: int) -> WorkingTimeModel:
    with SessionLocal() as session:
        model = session.scalar(
            select(WorkingTimeModel).where(
                WorkingTimeModel.tenant_id == tenant_id,
                WorkingTimeModel.name == "Vollzeit 2080h",
            )
        )
        if model:
            return model

        model = WorkingTimeModel(
            tenant_id=tenant_id,
            name="Vollzeit 2080h",
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


def _find_or_create_user(tenant_id: int, identity: DemoIdentity) -> User:
    with SessionLocal() as session:
        user = session.scalar(select(User).where(User.email == identity.email))
        if user:
            updated = False
            if user.keycloak_user_id != identity.keycloak_sub:
                user.keycloak_user_id = identity.keycloak_sub
                updated = True
            if user.role != identity.role:
                user.role = identity.role
                updated = True
            if user.tenant_id != tenant_id:
                user.tenant_id = tenant_id
                updated = True
            if user.full_name != identity.full_name:
                user.full_name = identity.full_name
                updated = True
            if updated:
                session.commit()
                session.refresh(user)
            return user

        user = User(
            tenant_id=tenant_id,
            email=identity.email,
            full_name=identity.full_name,
            keycloak_user_id=identity.keycloak_sub,
            role=identity.role,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def _find_or_create_employee_profile(tenant_id: int, user: User, model_id: int, identity: DemoIdentity) -> Employee:
    with SessionLocal() as session:
        employee = session.scalar(select(Employee).where(Employee.user_id == user.id))
        if employee:
            updated = False
            if employee.tenant_id != tenant_id:
                employee.tenant_id = tenant_id
                updated = True
            if employee.working_time_model_id != model_id:
                employee.working_time_model_id = model_id
                updated = True
            if employee.employee_number != identity.employee_number:
                employee.employee_number = identity.employee_number
                updated = True
            if employee.first_name != identity.first_name:
                employee.first_name = identity.first_name
                updated = True
            if employee.last_name != identity.last_name:
                employee.last_name = identity.last_name
                updated = True
            if updated:
                session.commit()
                session.refresh(employee)
            return employee

        employee = Employee(
            tenant_id=tenant_id,
            user_id=user.id,
            employee_number=identity.employee_number,
            first_name=identity.first_name,
            last_name=identity.last_name,
            employment_percentage=100,
            entry_date=date(2026, 1, 1),
            working_time_model_id=model_id,
            team="Demo",
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
    model = _find_or_create_model(tenant.id)

    users: list[User] = []
    employee_profiles: dict[str, Employee] = {}

    for identity in DEMO_IDENTITIES:
        user = _find_or_create_user(tenant.id, identity)
        users.append(user)
        employee_profiles[identity.email] = _find_or_create_employee_profile(tenant.id, user, model.id, identity)

    created_events = _seed_events(tenant.id, employee_profiles["employee@demo.local"].id)

    print("Seed completed")
    print(f"Tenant slug: {tenant.slug}")
    print("Users:")
    for identity in DEMO_IDENTITIES:
        print(f"  - {identity.email} (role={identity.role.value}, keycloak_user_id={identity.keycloak_sub})")
    print(f"Events inserted for employee@demo.local this run: {created_events}")


if __name__ == "__main__":
    main()
