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
        if token == "valid-admin-token":
            return type(
                "Claims",
                (),
                {
                    "sub": "kc-admin",
                    "preferred_username": "admin",
                    "email": "admin@zytlog.local",
                    "realm_roles": ["admin"],
                    "resource_roles": {"zytlog-api": ["admin"]},
                },
            )()
        if token == "valid-admin-other-tenant-token":
            return type(
                "Claims",
                (),
                {
                    "sub": "kc-admin-other",
                    "preferred_username": "admin.other",
                    "email": "admin.other@zytlog.local",
                    "realm_roles": ["admin"],
                    "resource_roles": {"zytlog-api": ["admin"]},
                },
            )()
        if token == "valid-employee-token":
            return type(
                "Claims",
                (),
                {
                    "sub": "kc-employee",
                    "preferred_username": "employee",
                    "email": "employee@zytlog.local",
                    "realm_roles": ["employee"],
                    "resource_roles": {"zytlog-api": ["employee"]},
                },
            )()
        raise TokenValidationError("Invalid or expired token")


@pytest.fixture
def test_session_local() -> sessionmaker:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        demo_tenant = Tenant(name="Demo Company", slug="demo-co", active=True, timezone="UTC")
        other_tenant = Tenant(name="Other Tenant", slug="other", active=True, timezone="UTC")
        session.add_all([demo_tenant, other_tenant])
        session.flush()

        admin = User(
            tenant_id=demo_tenant.id,
            email="admin@zytlog.local",
            full_name="Admin User",
            keycloak_user_id="kc-admin",
            role=UserRole.ADMIN,
        )
        employee_user = User(
            tenant_id=demo_tenant.id,
            email="employee@zytlog.local",
            full_name="Employee User",
            keycloak_user_id="kc-employee",
            role=UserRole.EMPLOYEE,
        )
        other_admin = User(
            tenant_id=other_tenant.id,
            email="admin.other@zytlog.local",
            full_name="Other Admin",
            keycloak_user_id="kc-admin-other",
            role=UserRole.ADMIN,
        )
        session.add_all([admin, employee_user, other_admin])
        session.flush()

        tenant_model = WorkingTimeModel(
            tenant_id=demo_tenant.id,
            name="Tenant Model",
            weekly_target_hours=40,
            default_workdays_per_week=5,
            annual_target_hours=2080,
            active=True,
        )
        other_tenant_model = WorkingTimeModel(
            tenant_id=other_tenant.id,
            name="Other Tenant Model",
            weekly_target_hours=35,
            default_workdays_per_week=5,
            annual_target_hours=1820,
            active=True,
        )
        session.add_all([tenant_model, other_tenant_model])
        session.flush()

        session.add(
            Employee(
                tenant_id=demo_tenant.id,
                user_id=employee_user.id,
                employee_number="E-001",
                first_name="Alex",
                last_name="Muster",
                employment_percentage=100,
                entry_date=date(2026, 1, 1),
                working_time_model_id=tenant_model.id,
            )
        )
        session.commit()

    return session_local


@pytest.fixture
def client(test_session_local: sessionmaker) -> TestClient:
    app = create_app()

    def _get_test_db():
        db = test_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_jwt_validator] = lambda: StubJWTValidator()

    previous_auth_enabled = settings.auth_enabled
    settings.auth_enabled = True

    with TestClient(app) as test_client:
        yield test_client

    settings.auth_enabled = previous_auth_enabled


def test_update_employee_success(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/employees/1",
        headers={"Authorization": "Bearer valid-admin-token"},
        json={
            "employee_number": "E-099",
            "first_name": "Alice",
            "last_name": "Admin",
            "employment_percentage": 80,
            "entry_date": "2026-02-01",
            "exit_date": "2026-12-31",
            "working_time_model_id": 1,
            "workday_friday": False,
            "team": "Operations",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["employee_number"] == "E-099"
    assert payload["first_name"] == "Alice"
    assert payload["last_name"] == "Admin"
    assert payload["employment_percentage"] == 80
    assert payload["entry_date"] == "2026-02-01"
    assert payload["exit_date"] == "2026-12-31"
    assert payload["working_time_model_id"] == 1
    assert payload["workday_friday"] is False
    assert payload["team"] == "Operations"


def test_update_employee_rejects_non_admin(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/employees/1",
        headers={"Authorization": "Bearer valid-employee-token"},
        json={"first_name": "Nope"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient role for this resource"


def test_update_employee_cross_tenant_returns_not_found(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/employees/1",
        headers={"Authorization": "Bearer valid-admin-other-tenant-token"},
        json={"first_name": "Cross Tenant"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Mitarbeiter nicht gefunden"


def test_update_employee_rejects_foreign_working_time_model(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/employees/1",
        headers={"Authorization": "Bearer valid-admin-token"},
        json={"working_time_model_id": 2},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Ungültiges Arbeitszeitmodell"
