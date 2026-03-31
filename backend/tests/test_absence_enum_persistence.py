from datetime import date

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.db.base import Base
from backend.models.absence import Absence
from backend.models.employee import Employee
from backend.models.enums import AbsenceDurationType, AbsenceType, UserRole
from backend.models.tenant import Tenant
from backend.models.user import User
from backend.repositories.absence_repository import AbsenceRepository
from backend.schemas.absence import AbsenceCreate


def test_absence_enum_values_are_persisted_and_round_trip() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        tenant = Tenant(name="Tenant", slug="tenant", active=True, timezone="UTC")
        session.add(tenant)
        session.flush()

        user = User(
            tenant_id=tenant.id,
            email="employee@tenant",
            full_name="Employee",
            keycloak_user_id="kc-employee",
            role=UserRole.EMPLOYEE,
        )
        session.add(user)
        session.flush()

        employee = Employee(
            tenant_id=tenant.id,
            user_id=user.id,
            first_name="E",
            last_name="M",
            employment_percentage=100,
            entry_date=date(2026, 1, 1),
            working_time_model_id=None,
        )
        session.add(employee)
        session.commit()

        created = AbsenceRepository(session).create_for_tenant(
            tenant_id=tenant.id,
            employee_id=employee.id,
            payload=AbsenceCreate(
                employee_id=employee.id,
                absence_type=AbsenceType.VACATION,
                start_date=date(2026, 3, 31),
                end_date=date(2026, 3, 31),
                duration_type=AbsenceDurationType.FULL_DAY,
                note="Trip",
            ),
        )

        stored_row = session.execute(
            text("SELECT absence_type, duration_type FROM absences WHERE id = :absence_id"),
            {"absence_id": created.id},
        ).one()
        assert stored_row[0] == "vacation"
        assert stored_row[1] == "full_day"

        round_tripped = session.get(Absence, created.id)
        assert round_tripped is not None
        assert round_tripped.absence_type == AbsenceType.VACATION
        assert round_tripped.duration_type == AbsenceDurationType.FULL_DAY
        assert round_tripped.absence_type.value == "vacation"
        assert round_tripped.duration_type.value == "full_day"
