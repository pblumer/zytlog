from datetime import date, datetime, timezone

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
from backend.repositories.time_stamp_event_repository import TimeStampEventRepository


class StubJWTValidator:
    def validate_token(self, token: str):
        token_mapping = {
            "valid-employee-token": {
                "sub": "kc-employee",
                "preferred_username": "employee",
                "email": "employee@zytlog.local",
            },
            "valid-admin-token": {
                "sub": "kc-admin",
                "preferred_username": "admin",
                "email": "admin@zytlog.local",
            },
            "valid-team-lead-token": {
                "sub": "kc-team-lead",
                "preferred_username": "team-lead",
                "email": "team-lead@zytlog.local",
            },
            "other-tenant-admin-token": {
                "sub": "kc-other-admin",
                "preferred_username": "other-admin",
                "email": "other-admin@zytlog.local",
            },
        }
        claims = token_mapping.get(token)
        if claims is None:
            raise TokenValidationError("Invalid or expired token")

        return type(
            "Claims",
            (),
            {
                **claims,
                "realm_roles": ["employee"],
                "resource_roles": {"zytlog-api": ["employee"]},
            },
        )()


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
        other_tenant = Tenant(name="Other Tenant", slug="other", active=True, timezone="UTC")
        session.add_all([tenant, other_tenant])
        session.flush()

        model = WorkingTimeModel(
            tenant_id=tenant.id,
            name="Full Time",
            weekly_target_hours=40,
            workdays_per_week=5,
            annual_target_hours=None,
            active=True,
        )
        other_model = WorkingTimeModel(
            tenant_id=other_tenant.id,
            name="Other Full Time",
            weekly_target_hours=40,
            workdays_per_week=5,
            annual_target_hours=None,
            active=True,
        )
        session.add_all([model, other_model])
        session.flush()

        employee_user = User(
            tenant_id=tenant.id,
            email="employee@zytlog.local",
            full_name="Employee User",
            keycloak_user_id="kc-employee",
            role=UserRole.EMPLOYEE,
        )
        admin_user = User(
            tenant_id=tenant.id,
            email="admin@zytlog.local",
            full_name="Tenant Admin",
            keycloak_user_id="kc-admin",
            role=UserRole.ADMIN,
        )
        other_tenant_admin_user = User(
            tenant_id=other_tenant.id,
            email="other-admin@zytlog.local",
            full_name="Other Tenant Admin",
            keycloak_user_id="kc-other-admin",
            role=UserRole.ADMIN,
        )
        team_lead_user = User(
            tenant_id=tenant.id,
            email="team-lead@zytlog.local",
            full_name="Team Lead",
            keycloak_user_id="kc-team-lead",
            role=UserRole.TEAM_LEAD,
        )
        session.add_all([employee_user, admin_user, other_tenant_admin_user, team_lead_user])
        session.flush()

        employee = Employee(
            tenant_id=tenant.id,
            user_id=employee_user.id,
            employee_number="E-1",
            first_name="Test",
            last_name="Employee",
            employment_percentage=100,
            entry_date=date(2026, 1, 1),
            working_time_model_id=model.id,
            team="ENG",
        )
        admin_employee = Employee(
            tenant_id=tenant.id,
            user_id=admin_user.id,
            employee_number="A-1",
            first_name="Test",
            last_name="Admin",
            employment_percentage=100,
            entry_date=date(2026, 1, 1),
            working_time_model_id=model.id,
            team="ENG",
        )
        other_admin_employee = Employee(
            tenant_id=other_tenant.id,
            user_id=other_tenant_admin_user.id,
            employee_number="OA-1",
            first_name="Other",
            last_name="Admin",
            employment_percentage=100,
            entry_date=date(2026, 1, 1),
            working_time_model_id=other_model.id,
            team="OPS",
        )
        team_lead_employee = Employee(
            tenant_id=tenant.id,
            user_id=team_lead_user.id,
            employee_number="TL-1",
            first_name="Team",
            last_name="Lead",
            employment_percentage=100,
            entry_date=date(2026, 1, 1),
            working_time_model_id=model.id,
            team="ENG",
        )
        session.add_all([employee, admin_employee, other_admin_employee, team_lead_employee])
        session.commit()

    app = create_app()
    app.state.test_session_local = test_session_local

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


def _auth_headers(token: str = "valid-employee-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed_event_timestamps(client: TestClient, day: date = date(2026, 3, 30)) -> list[dict]:
    # create in/out/in/out with endpoint API, then rewrite exact timestamps for deterministic tests
    for endpoint in [
        "/api/v1/time-stamps/clock-in",
        "/api/v1/time-stamps/clock-out",
        "/api/v1/time-stamps/clock-in",
        "/api/v1/time-stamps/clock-out",
    ]:
        result = client.post(endpoint, headers=_auth_headers())
        assert result.status_code == 200

    events_response = client.get(
        f"/api/v1/time-stamps/my?from={day.isoformat()}&to={day.isoformat()}",
        headers=_auth_headers(),
    )
    assert events_response.status_code == 200
    events = events_response.json()

    exact = [
        datetime(day.year, day.month, day.day, 8, 0, tzinfo=timezone.utc),
        datetime(day.year, day.month, day.day, 12, 0, tzinfo=timezone.utc),
        datetime(day.year, day.month, day.day, 12, 30, tzinfo=timezone.utc),
        datetime(day.year, day.month, day.day, 17, 0, tzinfo=timezone.utc),
    ]

    # direct repository update for deterministic event order in tests
    with client.app.state.test_session_local() as db:
        repo = TimeStampEventRepository(db)
        for index, event in enumerate(events):
            persisted = repo.get_by_id(tenant_id=event["tenant_id"], event_id=event["id"])
            assert persisted is not None
            repo.update_event(event=persisted, timestamp=exact[index], comment=persisted.comment)

    refreshed = client.get(
        f"/api/v1/time-stamps/my?from={day.isoformat()}&to={day.isoformat()}",
        headers=_auth_headers(),
    )
    assert refreshed.status_code == 200
    return refreshed.json()


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


def test_patch_time_stamp_comment_success(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    event_id = events[0]["id"]

    response = client.patch(
        f"/api/v1/time-stamps/{event_id}",
        json={"comment": "Adjusted after manual review"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["comment"] == "Adjusted after manual review"


def test_patch_time_stamp_timestamp_success(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    event_id = events[0]["id"]

    response = client.patch(
        f"/api/v1/time-stamps/{event_id}",
        json={"timestamp": "2026-03-30T08:15:00Z"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["timestamp"] == "2026-03-30T08:15:00Z"


def test_patch_time_stamp_cross_day_preserves_same_day_validity(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    second_clock_in_id = events[2]["id"]

    response = client.patch(
        f"/api/v1/time-stamps/{second_clock_in_id}",
        json={"timestamp": "2026-03-31T08:00:00Z"},
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["timestamp"] == "2026-03-31T08:00:00Z"



def test_patch_time_stamp_invalid_sequence_conflict(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    first_clock_in_id = events[0]["id"]

    # move first clock-in behind first clock-out => first event would become clock_out
    response = client.patch(
        f"/api/v1/time-stamps/{first_clock_in_id}",
        json={"timestamp": "2026-03-30T12:10:00Z"},
        headers=_auth_headers(),
    )

    assert response.status_code == 409
    assert "Invalid same-day stamp sequence" in response.json()["detail"]


def test_patch_time_stamp_forbidden_for_unauthorized_user(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    event_id = events[0]["id"]

    response = client.patch(
        f"/api/v1/time-stamps/{event_id}",
        json={"comment": "team lead correction"},
        headers=_auth_headers("valid-team-lead-token"),
    )

    assert response.status_code == 403


def test_patch_time_stamp_allowed_for_tenant_admin(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    event_id = events[0]["id"]

    response = client.patch(
        f"/api/v1/time-stamps/{event_id}",
        json={"comment": "admin correction"},
        headers=_auth_headers("valid-admin-token"),
    )

    assert response.status_code == 200
    assert response.json()["comment"] == "admin correction"


def test_patch_time_stamp_cross_tenant_not_found(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    event_id = events[0]["id"]

    response = client.patch(
        f"/api/v1/time-stamps/{event_id}",
        json={"comment": "cross-tenant"},
        headers=_auth_headers("other-tenant-admin-token"),
    )

    assert response.status_code == 404


def test_delete_single_clock_in_makes_day_empty(client: TestClient) -> None:
    created = client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())
    assert created.status_code == 200
    event_id = created.json()["id"]

    deleted = client.delete(f"/api/v1/time-stamps/{event_id}", headers=_auth_headers())
    assert deleted.status_code == 200
    assert deleted.json()["id"] == event_id

    events = client.get("/api/v1/time-stamps/my?from=2026-03-30&to=2026-03-30", headers=_auth_headers())
    assert events.status_code == 200
    assert events.json() == []

    account = client.get("/api/v1/daily-accounts/my?date=2026-03-30", headers=_auth_headers())
    assert account.status_code == 200
    assert account.json()["status"] == "empty"
    assert account.json()["event_count"] == 0


def test_delete_clock_out_leaves_day_incomplete_but_valid(client: TestClient) -> None:
    in_event = client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())
    assert in_event.status_code == 200
    out_event = client.post("/api/v1/time-stamps/clock-out", headers=_auth_headers())
    assert out_event.status_code == 200

    deleted = client.delete(f"/api/v1/time-stamps/{out_event.json()['id']}", headers=_auth_headers())
    assert deleted.status_code == 200

    events = client.get("/api/v1/time-stamps/my?from=2026-03-30&to=2026-03-30", headers=_auth_headers())
    assert events.status_code == 200
    payload = events.json()
    assert len(payload) == 1
    assert payload[0]["id"] == in_event.json()["id"]
    assert payload[0]["type"] == "clock_in"

    account = client.get("/api/v1/daily-accounts/my?date=2026-03-30", headers=_auth_headers())
    assert account.status_code == 200
    assert account.json()["status"] == "incomplete"
    assert account.json()["event_count"] == 1


def test_delete_rejected_when_resulting_same_day_sequence_invalid(client: TestClient) -> None:
    first = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-30T08:00:00Z", "type": "clock_in"},
        headers=_auth_headers(),
    )
    assert first.status_code == 200
    middle = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-30T12:00:00Z", "type": "clock_out"},
        headers=_auth_headers(),
    )
    assert middle.status_code == 200
    third = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-30T12:30:00Z", "type": "clock_in"},
        headers=_auth_headers(),
    )
    assert third.status_code == 200

    response = client.delete(f"/api/v1/time-stamps/{middle.json()['id']}", headers=_auth_headers())
    assert response.status_code == 409
    assert "Tagessequenz" in response.json()["detail"]


def test_delete_time_stamp_forbidden_for_unauthorized_user(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    event_id = events[0]["id"]

    response = client.delete(f"/api/v1/time-stamps/{event_id}", headers=_auth_headers("valid-team-lead-token"))
    assert response.status_code == 403


def test_delete_time_stamp_cross_tenant_not_found(client: TestClient) -> None:
    events = _seed_event_timestamps(client)
    event_id = events[0]["id"]

    response = client.delete(f"/api/v1/time-stamps/{event_id}", headers=_auth_headers("other-tenant-admin-token"))
    assert response.status_code == 404


def test_manual_clock_in_in_past_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/time-stamps/manual",
        json={
            "timestamp": "2026-03-29T08:00:00+01:00",
            "type": "clock_in",
            "comment": "Forgot to stamp yesterday",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "clock_in"
    assert payload["source"] == "manual_entry"
    assert payload["comment"] == "Forgot to stamp yesterday"


def test_manual_clock_in_in_past_allows_open_day_elsewhere(client: TestClient) -> None:
    open_today = client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())
    assert open_today.status_code == 200

    response = client.post(
        "/api/v1/time-stamps/manual",
        json={
            "timestamp": "2026-03-29T08:00:00Z",
            "type": "clock_in",
            "comment": "Back entry for previous day",
        },
        headers=_auth_headers(),
    )

    assert response.status_code == 200
    assert response.json()["type"] == "clock_in"


def test_manual_clock_out_in_past_success(client: TestClient) -> None:
    first = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-29T08:00:00Z", "type": "clock_in"},
        headers=_auth_headers(),
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-29T16:00:00Z", "type": "clock_out"},
        headers=_auth_headers(),
    )
    assert second.status_code == 200
    assert second.json()["type"] == "clock_out"
    assert second.json()["source"] == "manual_entry"


def test_manual_clock_out_without_same_day_clock_in_fails(client: TestClient) -> None:
    response = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-29T16:00:00Z", "type": "clock_out"},
        headers=_auth_headers(),
    )

    assert response.status_code == 409
    assert "Invalid same-day stamp sequence" in response.json()["detail"]


def test_manual_entry_invalid_sequence_conflict(client: TestClient) -> None:
    first = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-29T08:00:00Z", "type": "clock_in"},
        headers=_auth_headers(),
    )
    assert first.status_code == 200

    conflict = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-29T09:00:00Z", "type": "clock_in"},
        headers=_auth_headers(),
    )
    assert conflict.status_code == 409
    assert "Invalid same-day stamp sequence" in conflict.json()["detail"]


def test_manual_entry_auth_required(client: TestClient) -> None:
    response = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-29T08:00:00Z", "type": "clock_in"},
    )
    assert response.status_code == 401


def test_manual_entry_is_tenant_scoped_to_authenticated_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-29T08:00:00Z", "type": "clock_in"},
        headers=_auth_headers("other-tenant-admin-token"),
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == 2


def test_current_status_uses_latest_event_overall_with_back_entry(client: TestClient) -> None:
    current_clock_in = client.post("/api/v1/time-stamps/clock-in", headers=_auth_headers())
    assert current_clock_in.status_code == 200

    past_manual_entry = client.post(
        "/api/v1/time-stamps/manual",
        json={"timestamp": "2026-03-29T08:00:00Z", "type": "clock_in"},
        headers=_auth_headers(),
    )
    assert past_manual_entry.status_code == 200

    response = client.get("/api/v1/time-stamps/my/current-status", headers=_auth_headers())
    assert response.status_code == 200
    assert response.json()["status"] == "clocked_in"
