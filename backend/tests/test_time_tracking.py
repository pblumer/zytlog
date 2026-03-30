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

        user = User(
            tenant_id=tenant.id,
            email="employee@zytlog.local",
            full_name="Employee User",
            keycloak_user_id="kc-employee",
            role=UserRole.EMPLOYEE,
        )
        session.add(user)
        session.flush()

        model = WorkingTimeModel(
            tenant_id=tenant.id,
            name="Full Time",
            weekly_target_hours=40,
            workdays_per_week=5,
            annual_target_hours=None,
            active=True,
        )
        session.add(model)
        session.flush()

        session.add(
            Employee(
                tenant_id=tenant.id,
                user_id=user.id,
                employee_number="E-1",
                first_name="Test",
                last_name="Employee",
                employment_percentage=100,
                entry_date=date(2026, 1, 1),
                working_time_model_id=model.id,
                team="ENG",
            )
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


def _auth_headers() -> dict[str, str]:
    return {"Authorization": "Bearer valid-employee-token"}


def test_clock_in_success(client: TestClient) -> None:
    response = client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())

    assert response.status_code == 200
    assert response.json()["type"] == "clock_in"


def test_clock_out_success(client: TestClient) -> None:
    client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())
    response = client.post("/api/v1/time-stamps/clock-out", headers=_auth_headers())

    assert response.status_code == 200
    assert response.json()["type"] == "clock_out"


def test_double_clock_in_invalid(client: TestClient) -> None:
    client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())
    response = client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())

    assert response.status_code == 409
    assert response.json()["detail"] == "Invalid stamp sequence: already clocked in"


def test_clock_out_without_clock_in_invalid(client: TestClient) -> None:
    response = client.post("/api/v1/time-stamps/clock-out", headers=_auth_headers())

    assert response.status_code == 409
    assert response.json()["detail"] == "Cannot clock out without prior clock in"


def test_current_status_after_clock_in(client: TestClient) -> None:
    client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())

    response = client.get("/api/v1/time-stamps/my/current-status", headers=_auth_headers())
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "clocked_in"
    assert payload["last_event_type"] == "clock_in"


def test_daily_account_for_valid_pair(client: TestClient) -> None:
    client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())
    client.post("/api/v1/time-stamps/clock-out", headers=_auth_headers())

    response = client.get("/api/v1/daily-accounts/my?date=2026-03-30", headers=_auth_headers())
    assert response.status_code == 200

    payload = response.json()
    assert payload["target_minutes"] == 480
    assert payload["actual_minutes"] >= 0
    assert payload["status"] == "complete"


def test_daily_account_incomplete_day(client: TestClient) -> None:
    client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())

    response = client.get("/api/v1/daily-accounts/my?date=2026-03-30", headers=_auth_headers())
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "incomplete"
    assert payload["event_count"] == 1
