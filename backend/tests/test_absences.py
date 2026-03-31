from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.deps import get_db
from backend.core.auth.dependencies import get_jwt_validator
from backend.core.auth.jwt import TokenValidationError
from backend.core.config import settings
from backend.db.base import Base
from backend.main import create_app
from backend.models.employee import Employee
from backend.models.enums import UserRole
from backend.models.tenant import Tenant
from backend.models.user import User
from backend.models.working_time_model import WorkingTimeModel


class StubJWTValidator:
    def validate_token(self, token: str):
        if token == "employee-token":
            sub = "kc-employee"
        elif token == "admin-token":
            sub = "kc-admin"
        else:
            raise TokenValidationError("Invalid token")
        return type(
            "Claims",
            (),
            {
                "sub": sub,
                "preferred_username": sub,
                "email": f"{sub}@zytlog.local",
                "realm_roles": ["employee"],
                "resource_roles": {"zytlog-api": ["employee"]},
            },
        )()


@pytest.fixture
def client() -> TestClient:
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        tenant = Tenant(name="Tenant A", slug="tenant-a", active=True, timezone="UTC")
        tenant_b = Tenant(name="Tenant B", slug="tenant-b", active=True, timezone="UTC")
        session.add_all([tenant, tenant_b])
        session.flush()

        model = WorkingTimeModel(
            tenant_id=tenant.id,
            name="Std",
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
        model_b = WorkingTimeModel(
            tenant_id=tenant_b.id,
            name="Std",
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
        session.add_all([model, model_b])
        session.flush()

        admin = User(tenant_id=tenant.id, email="admin@a", full_name="Admin", keycloak_user_id="kc-admin", role=UserRole.ADMIN)
        employee_user = User(tenant_id=tenant.id, email="employee@a", full_name="Emp", keycloak_user_id="kc-employee", role=UserRole.EMPLOYEE)
        employee_user_b = User(tenant_id=tenant_b.id, email="employee@b", full_name="EmpB", keycloak_user_id="kc-employee-b", role=UserRole.EMPLOYEE)
        session.add_all([admin, employee_user, employee_user_b])
        session.flush()

        session.add_all(
            [
                Employee(tenant_id=tenant.id, user_id=admin.id, first_name="A", last_name="D", employment_percentage=100, entry_date=date(2026, 1, 1), working_time_model_id=model.id),
                Employee(tenant_id=tenant.id, user_id=employee_user.id, first_name="E", last_name="M", employment_percentage=100, entry_date=date(2026, 1, 1), working_time_model_id=model.id),
                Employee(tenant_id=tenant_b.id, user_id=employee_user_b.id, first_name="B", last_name="M", employment_percentage=100, entry_date=date(2026, 1, 1), working_time_model_id=model_b.id),
            ]
        )
        session.commit()

    app = create_app()

    def _get_test_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_jwt_validator] = lambda: StubJWTValidator()
    prev = settings.auth_enabled
    settings.auth_enabled = True
    with TestClient(app) as c:
        yield c
    settings.auth_enabled = prev


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_my_absence_create_and_daily_context(client: TestClient) -> None:
    create = client.post(
        "/api/v1/absences/my",
        json={
            "absence_type": "vacation",
            "start_date": "2026-03-31",
            "end_date": "2026-03-31",
            "duration_type": "full_day",
            "note": "Trip",
        },
        headers=_headers("employee-token"),
    )
    assert create.status_code == 201

    day = client.get("/api/v1/daily-accounts/my?date=2026-03-31", headers=_headers("employee-token"))
    assert day.status_code == 200
    payload = day.json()
    assert payload["absence"]["type"] == "vacation"
    assert payload["absence"]["duration_type"] == "full_day"


def test_half_day_validation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/absences/my",
        json={
            "absence_type": "sickness",
            "start_date": "2026-03-31",
            "end_date": "2026-04-01",
            "duration_type": "half_day_am",
            "note": None,
        },
        headers=_headers("employee-token"),
    )
    assert response.status_code == 422


def test_overlap_rejected(client: TestClient) -> None:
    payload = {
        "absence_type": "vacation",
        "start_date": "2026-04-10",
        "end_date": "2026-04-12",
        "duration_type": "full_day",
        "note": None,
    }
    first = client.post("/api/v1/absences/my", json=payload, headers=_headers("employee-token"))
    assert first.status_code == 201
    second = client.post("/api/v1/absences/my", json=payload, headers=_headers("employee-token"))
    assert second.status_code == 409


def test_admin_tenant_isolation_for_employee_id(client: TestClient) -> None:
    response = client.post(
        "/api/v1/admin/absences",
        json={
            "employee_id": 3,
            "absence_type": "vacation",
            "start_date": "2026-05-01",
            "end_date": "2026-05-01",
            "duration_type": "full_day",
            "note": None,
        },
        headers=_headers("admin-token"),
    )
    assert response.status_code == 404
