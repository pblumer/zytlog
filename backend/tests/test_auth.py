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
from backend.models.enums import UserRole
from backend.models.tenant import Tenant
from backend.models.user import User


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
def client() -> TestClient:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        tenant = Tenant(name="Test Tenant", slug="test", active=True, timezone="UTC")
        session.add(tenant)
        session.flush()

        session.add_all(
            [
                User(
                    tenant_id=tenant.id,
                    email="admin@zytlog.local",
                    full_name="Admin User",
                    keycloak_user_id="kc-admin",
                    role=UserRole.ADMIN,
                ),
                User(
                    tenant_id=tenant.id,
                    email="employee@zytlog.local",
                    full_name="Employee User",
                    keycloak_user_id="kc-employee",
                    role=UserRole.EMPLOYEE,
                ),
            ]
        )
        session.commit()

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


def test_me_requires_token(client: TestClient) -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"


def test_me_rejects_invalid_token(client: TestClient) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_employee_create_requires_admin_role(client: TestClient) -> None:
    response = client.post(
        "/api/v1/employees",
        headers={"Authorization": "Bearer valid-employee-token"},
        json={
            "user_id": 2,
            "employee_number": "E-123",
            "first_name": "Jane",
            "last_name": "Doe",
            "employment_percentage": 100,
            "entry_date": str(date(2026, 1, 1)),
            "exit_date": None,
            "working_time_model_id": None,
            "team": "A",
        },
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient role for this resource"


def test_me_returns_authenticated_user_context(client: TestClient) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-admin-token"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == 1
    assert payload["email"] == "admin@zytlog.local"
    assert payload["role"] == "admin"
    assert payload["tenant_id"] == 1
