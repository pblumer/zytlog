from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.deps import get_db
from backend.core.auth.dependencies import get_jwt_validator
from backend.core.auth.jwt import TokenValidationError
from backend.db.base import Base
from backend.main import create_app
from backend.models.employee import Employee
from backend.models.enums import UserRole
from backend.models.tenant import Tenant
from datetime import date

from backend.models.user import User


class StubJWTValidator:
    def validate_token(self, token: str):
        mapping = {
            "system-admin-token": {
                "sub": "kc-system-admin",
                "preferred_username": "system.admin",
                "email": "system.admin@zytlog.local",
                "realm_roles": ["system_admin"],
                "resource_roles": {"zytlog-api": ["system_admin"]},
            },
            "admin-token": {
                "sub": "kc-admin",
                "preferred_username": "tenant.admin",
                "email": "admin@zytlog.local",
                "realm_roles": ["admin"],
                "resource_roles": {"zytlog-api": ["admin"]},
            },
        }
        claims = mapping.get(token)
        if claims is None:
            raise TokenValidationError("Invalid or expired token")
        return type("Claims", (), claims)()


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
        tenant_one = Tenant(name="Demo Company", slug="demo-co", active=True, timezone="UTC")
        tenant_two = Tenant(name="Second Company", slug="second-co", active=True, timezone="Europe/Zurich")
        session.add_all([tenant_one, tenant_two])
        session.flush()

        system_admin = User(
            tenant_id=tenant_one.id,
            email="system.admin@zytlog.local",
            full_name="System Admin",
            keycloak_user_id="kc-system-admin",
            role=UserRole.SYSTEM_ADMIN,
        )
        tenant_admin = User(
            tenant_id=tenant_one.id,
            email="admin@zytlog.local",
            full_name="Tenant Admin",
            keycloak_user_id="kc-admin",
            role=UserRole.ADMIN,
        )
        employee_user = User(
            tenant_id=tenant_one.id,
            email="employee@zytlog.local",
            full_name="Employee User",
            keycloak_user_id="kc-employee",
            role=UserRole.EMPLOYEE,
        )
        free_user = User(
            tenant_id=tenant_one.id,
            email="free.user@zytlog.local",
            full_name="Free User",
            keycloak_user_id="kc-free-user",
            role=UserRole.EMPLOYEE,
        )
        session.add_all([system_admin, tenant_admin, employee_user, free_user])
        session.flush()

        session.add(
            Employee(
                tenant_id=tenant_one.id,
                user_id=employee_user.id,
                employee_number="E-001",
                first_name="Alex",
                last_name="Muster",
                employment_percentage=100,
                entry_date=date(2026, 1, 1),
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

    with TestClient(app) as test_client:
        yield test_client


def test_list_system_users_requires_system_admin(client: TestClient) -> None:
    response = client.get("/api/v1/system/users", headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 403


def test_system_admin_can_list_users(client: TestClient) -> None:
    response = client.get("/api/v1/system/users", headers={"Authorization": "Bearer system-admin-token"})
    assert response.status_code == 200
    payload = response.json()
    emails = [item["email"] for item in payload]
    assert "system.admin@zytlog.local" in emails
    assert "employee@zytlog.local" in emails
    employee_row = next(item for item in payload if item["email"] == "employee@zytlog.local")
    assert employee_row["has_employee_profile"] is True


def test_system_admin_can_change_role_for_user_without_employee_profile(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/system/users/4",
        headers={"Authorization": "Bearer system-admin-token"},
        json={"role": "admin"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"] == "admin"


def test_system_admin_can_reassign_tenant_for_user_without_employee_profile(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/system/users/4",
        headers={"Authorization": "Bearer system-admin-token"},
        json={"tenant_id": 2},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == 2


def test_reassigning_user_with_employee_profile_is_rejected(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/system/users/3",
        headers={"Authorization": "Bearer system-admin-token"},
        json={"tenant_id": 2},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot reassign tenant for users with an employee profile yet"


def test_promoting_employee_profile_user_to_system_admin_is_rejected(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/system/users/3",
        headers={"Authorization": "Bearer system-admin-token"},
        json={"role": "system_admin"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot promote users with an employee profile to system_admin"


def test_tenant_reassignment_for_existing_system_admin_is_rejected(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/system/users/1",
        headers={"Authorization": "Bearer system-admin-token"},
        json={"tenant_id": 2},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "System admin users are managed system-wide and cannot have tenant reassignment"


def test_tenant_reassignment_is_rejected_when_promoting_to_system_admin(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/system/users/4",
        headers={"Authorization": "Bearer system-admin-token"},
        json={"role": "system_admin", "tenant_id": 2},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "System admin users are managed system-wide and cannot have tenant reassignment"
