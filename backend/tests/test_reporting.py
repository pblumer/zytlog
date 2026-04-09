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
from backend.models.enums import TimeStampEventType, UserRole
from backend.models.tenant import Tenant
from backend.models.time_stamp_event import TimeStampEvent
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
        session.flush()

        employee = Employee(
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
        session.add(employee)
        session.flush()

        events = [
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 3, 30, 9, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_IN,
                source="test",
            ),
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 3, 30, 17, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_OUT,
                source="test",
            ),
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 3, 31, 9, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_IN,
                source="test",
            ),
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 3, 31, 12, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_OUT,
                source="test",
            ),
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 3, 31, 13, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_IN,
                source="test",
            ),
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 3, 31, 18, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_OUT,
                source="test",
            ),
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_IN,
                source="test",
            ),
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 4, 2, 9, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_OUT,
                source="test",
            ),
            TimeStampEvent(
                tenant_id=tenant.id,
                employee_id=employee.id,
                timestamp=datetime(2026, 4, 2, 10, 0, tzinfo=timezone.utc),
                type=TimeStampEventType.CLOCK_OUT,
                source="test",
            ),
        ]
        session.add_all(events)
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


def test_week_overview_valid(client: TestClient) -> None:
    absence_response = client.post(
        "/api/v1/absences/my",
        json={
            "absence_type": "vacation",
            "start_date": "2026-03-31",
            "end_date": "2026-03-31",
            "duration_type": "half_day_am",
            "note": "Planned leave",
        },
        headers=_auth_headers(),
    )
    assert absence_response.status_code == 201

    response = client.get("/api/v1/reports/my/week?year=2026&week=14", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["range_start"] == "2026-03-30"
    assert payload["range_end"] == "2026-04-05"
    assert len(payload["days"]) == 7
    assert payload["totals"]["target_minutes"] == 2390
    assert payload["totals"]["actual_minutes"] == 960
    assert payload["totals"]["break_minutes"] == 60
    assert payload["totals"]["days_complete"] == 2
    assert payload["totals"]["days_incomplete"] == 1
    assert payload["totals"]["days_invalid"] == 1
    assert payload["totals"]["days_empty"] == 3
    tuesday = next(day for day in payload["days"] if day["date"] == "2026-03-31")
    assert tuesday["absence"] == {"type": "vacation", "label": "Vacation", "duration_type": "half_day_am"}


def test_month_overview_valid(client: TestClient) -> None:
    response = client.get("/api/v1/reports/my/month?year=2026&month=3", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["range_start"] == "2026-03-01"
    assert payload["range_end"] == "2026-03-31"
    assert len(payload["days"]) == 31
    assert payload["totals"]["target_minutes"] == 10516
    assert payload["totals"]["actual_minutes"] == 960
    assert payload["totals"]["break_minutes"] == 60
    assert payload["totals"]["balance_minutes"] == -9556
    assert payload["totals"]["days_complete"] == 2
    assert payload["totals"]["days_empty"] == 29


def test_year_overview_valid(client: TestClient) -> None:
    response = client.get("/api/v1/reports/my/year?year=2026", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["months"]) == 12
    assert payload["months"][2]["actual_minutes"] == 960
    assert payload["months"][3]["days_incomplete"] == 1
    assert payload["months"][3]["days_invalid"] == 1
    assert payload["totals"]["target_minutes"] == 124800
    assert payload["totals"]["actual_minutes"] == 960
    assert payload["totals"]["break_minutes"] == 60


def test_week_overview_invalid_week_for_year(client: TestClient) -> None:
    response = client.get("/api/v1/reports/my/week?year=2025&week=53", headers=_auth_headers())

    assert response.status_code == 422
    assert response.json()["detail"] == "week must be in 1..52 for year 2025"


def test_month_overview_invalid_month_input(client: TestClient) -> None:
    response = client.get("/api/v1/reports/my/month?year=2026&month=13", headers=_auth_headers())

    assert response.status_code == 422


def test_week_overview_totals_aggregation_sanity(client: TestClient) -> None:
    response = client.get("/api/v1/reports/my/week?year=2026&week=14", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.json()
    daily_actual_sum = sum(day["actual_minutes"] for day in payload["days"])
    daily_balance_sum = sum(day["balance_minutes"] for day in payload["days"])

    assert payload["totals"]["actual_minutes"] == daily_actual_sum
    assert payload["totals"]["balance_minutes"] == daily_balance_sum


def test_day_csv_export(client: TestClient) -> None:
    response = client.get("/api/v1/exports/my/day?date=2026-03-30", headers=_auth_headers())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "zytlog_day_2026-03-30.csv" in response.headers["content-disposition"]
    decoded = response.content.decode("utf-8-sig")
    assert "Date,Status,Target Minutes" in decoded
    assert "2026-03-30,complete,478,07:58,480,08:00,0,00:00,2,00:02,2" in decoded
    assert "TOTAL,,478,07:58,480,08:00,0,00:00,2,00:02,2" in decoded


def test_week_pdf_export(client: TestClient) -> None:
    response = client.get("/api/v1/exports/my/week/pdf?year=2026&week=14", headers=_auth_headers())

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "zytlog_week_2026_w14.pdf" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_exports_require_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/exports/my/year?year=2026")

    assert response.status_code == 401


def test_calendar_month_valid_response(client: TestClient) -> None:
    response = client.get("/api/v1/calendar/my/month?year=2026&month=3", headers=_auth_headers())

    assert response.status_code == 200
    payload = response.json()
    assert payload["year"] == 2026
    assert payload["month"] == 3
    assert len(payload["days"]) == 31


def test_calendar_month_mixed_statuses(client: TestClient) -> None:
    absence_response = client.post(
        "/api/v1/absences/my",
        json={
            "absence_type": "sickness",
            "start_date": "2026-04-03",
            "end_date": "2026-04-03",
            "duration_type": "full_day",
            "note": "Sick leave",
        },
        headers=_auth_headers(),
    )
    assert absence_response.status_code == 201

    response = client.get("/api/v1/calendar/my/month?year=2026&month=4", headers=_auth_headers())

    assert response.status_code == 200
    statuses = {day["status"] for day in response.json()["days"]}
    assert "incomplete" in statuses
    assert "invalid" in statuses
    assert "no_data" in statuses
    sick_day = next(day for day in response.json()["days"] if day["date"] == "2026-04-03")
    assert sick_day["absence"] == {"type": "sickness", "label": "Sickness", "duration_type": "full_day"}


def test_calendar_month_invalid_month(client: TestClient) -> None:
    response = client.get("/api/v1/calendar/my/month?year=2026&month=13", headers=_auth_headers())

    assert response.status_code == 422


def test_calendar_month_auth_required(client: TestClient) -> None:
    response = client.get("/api/v1/calendar/my/month?year=2026&month=3")

    assert response.status_code == 401
