from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.api.deps import get_db
from backend.api.v1.endpoints import openholidays as openholidays_endpoint
from backend.core.auth.dependencies import get_jwt_validator
from backend.core.auth.jwt import TokenValidationError
from backend.core.config import settings
from backend.db.base import Base
from backend.main import create_app
from backend.models.enums import UserRole
from backend.models.holiday import Holiday
from backend.models.holiday_set import HolidaySet
from backend.models.tenant import Tenant
from backend.models.user import User
from backend.services.openholidays_service import OpenHolidayItem


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


class StubOpenHolidaysClient:
    def list_countries(self):
        return [{"iso_code": "CH", "name": "Schweiz"}]

    def list_languages(self):
        return [{"language_code": "DE", "name": "Deutsch"}]

    def list_subdivisions(self, _country_code: str):
        return [{"code": "CH-BE", "name": "Bern"}]

    def fetch_public_holidays(self, **_kwargs):
        return [
            OpenHolidayItem(
                date=date(2026, 1, 1),
                name="Neujahr",
                country_iso_code="CH",
                subdivision_code="CH-BE",
                language_code="DE",
                source_reference="a",
            ),
            OpenHolidayItem(
                date=date(2026, 8, 1),
                name="Bundesfeier",
                country_iso_code="CH",
                subdivision_code="CH-BE",
                language_code="DE",
                source_reference="b",
            ),
        ]


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

        demo_set = HolidaySet(tenant_id=demo_tenant.id, name="Standard", source="manual", active=True)
        other_set = HolidaySet(tenant_id=other_tenant.id, name="Other Standard", source="manual", active=True)
        session.add_all([demo_set, other_set])
        session.flush()

        session.add_all(
            [
                User(
                    tenant_id=demo_tenant.id,
                    email="admin@zytlog.local",
                    full_name="Admin User",
                    keycloak_user_id="kc-admin",
                    role=UserRole.ADMIN,
                ),
                User(
                    tenant_id=demo_tenant.id,
                    email="employee@zytlog.local",
                    full_name="Employee User",
                    keycloak_user_id="kc-employee",
                    role=UserRole.EMPLOYEE,
                ),
                User(
                    tenant_id=other_tenant.id,
                    email="admin.other@zytlog.local",
                    full_name="Other Admin",
                    keycloak_user_id="kc-admin-other",
                    role=UserRole.ADMIN,
                ),
            ]
        )
        session.flush()

        session.add(
            Holiday(
                tenant_id=demo_tenant.id,
                holiday_set_id=demo_set.id,
                date=date(2026, 1, 1),
                name="Bestehend",
                active=True,
            )
        )
        session.commit()

    return session_local


@pytest.fixture
def client(test_session_local: sessionmaker, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    app = create_app()

    def _get_test_db():
        db = test_session_local()
        try:
            yield db
        finally:
            db.close()

    monkeypatch.setattr(openholidays_endpoint, "_client", lambda: StubOpenHolidaysClient())
    app.dependency_overrides[get_db] = _get_test_db
    app.dependency_overrides[get_jwt_validator] = lambda: StubJWTValidator()

    previous_auth_enabled = settings.auth_enabled
    settings.auth_enabled = True

    with TestClient(app) as test_client:
        yield test_client

    settings.auth_enabled = previous_auth_enabled


def _payload(import_mode: str = "skip_existing") -> dict:
    return {
        "country_iso_code": "CH",
        "subdivision_code": "CH-BE",
        "language_code": "DE",
        "valid_from": "2026-01-01",
        "valid_to": "2026-12-31",
        "import_mode": import_mode,
    }


def test_openholidays_admin_only(client: TestClient) -> None:
    response = client.get("/api/v1/admin/openholidays/countries", headers={"Authorization": "Bearer valid-employee-token"})
    assert response.status_code == 403


def test_openholidays_preview_skip_existing(client: TestClient) -> None:
    set_response = client.get('/api/v1/holiday-sets', headers={'Authorization': 'Bearer valid-admin-token'})
    holiday_set_id = set_response.json()[0]['id']

    response = client.post(
        f"/api/v1/admin/holiday-sets/{holiday_set_id}/import/openholidays/preview",
        headers={"Authorization": "Bearer valid-admin-token"},
        json=_payload("skip_existing"),
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert rows[0]["exists_in_holiday_set"] is True
    assert rows[0]["action_hint"] == "skip"
    assert rows[1]["action_hint"] == "create"


def test_openholidays_commit_replace_existing(client: TestClient) -> None:
    set_response = client.get('/api/v1/holiday-sets', headers={'Authorization': 'Bearer valid-admin-token'})
    holiday_set_id = set_response.json()[0]['id']

    response = client.post(
        f"/api/v1/admin/holiday-sets/{holiday_set_id}/import/openholidays/commit",
        headers={"Authorization": "Bearer valid-admin-token"},
        json=_payload("replace_existing_in_range"),
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["created"] == 2
    assert summary["replaced"] == 1
    assert summary["skipped"] == 0

    list_response = client.get(
        f"/api/v1/holidays?year=2026&holiday_set_id={holiday_set_id}",
        headers={"Authorization": "Bearer valid-admin-token"},
    )
    assert list_response.status_code == 200
    names = [item["name"] for item in list_response.json()]
    assert names == ["Neujahr", "Bundesfeier"]


def test_openholidays_tenant_isolation(client: TestClient) -> None:
    set_response = client.get('/api/v1/holiday-sets', headers={'Authorization': 'Bearer valid-admin-other-tenant-token'})
    other_set_id = set_response.json()[0]['id']

    response = client.post(
        f"/api/v1/admin/holiday-sets/{other_set_id}/import/openholidays/preview",
        headers={"Authorization": "Bearer valid-admin-token"},
        json=_payload(),
    )
    assert response.status_code == 404
