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
from backend.models.holiday import Holiday
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

        session.add_all(
            [
                Holiday(tenant_id=demo_tenant.id, date=date(2026, 1, 1), name="Neujahr", active=True),
                Holiday(tenant_id=other_tenant.id, date=date(2026, 1, 1), name="Other Neujahr", active=True),
            ]
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


def test_list_holidays_admin_only(client: TestClient) -> None:
    response = client.get('/api/v1/holidays', headers={'Authorization': 'Bearer valid-employee-token'})
    assert response.status_code == 403


def test_list_holidays_scoped_by_tenant(client: TestClient) -> None:
    response = client.get('/api/v1/holidays?year=2026', headers={'Authorization': 'Bearer valid-admin-token'})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]['name'] == 'Neujahr'


def test_create_update_delete_holiday(client: TestClient) -> None:
    create_response = client.post(
        '/api/v1/holidays',
        headers={'Authorization': 'Bearer valid-admin-token'},
        json={'date': '2026-12-25', 'name': 'Weihnachten', 'active': True},
    )
    assert create_response.status_code == 200
    holiday_id = create_response.json()['id']

    update_response = client.patch(
        f'/api/v1/holidays/{holiday_id}',
        headers={'Authorization': 'Bearer valid-admin-token'},
        json={'name': 'Weihnachtstag', 'active': False},
    )
    assert update_response.status_code == 200
    assert update_response.json()['name'] == 'Weihnachtstag'
    assert update_response.json()['active'] is False

    delete_response = client.delete(
        f'/api/v1/holidays/{holiday_id}',
        headers={'Authorization': 'Bearer valid-admin-token'},
    )
    assert delete_response.status_code == 204


def test_holiday_date_unique_per_tenant(client: TestClient) -> None:
    response = client.post(
        '/api/v1/holidays',
        headers={'Authorization': 'Bearer valid-admin-token'},
        json={'date': '2026-01-01', 'name': 'Neujahr 2', 'active': True},
    )
    assert response.status_code == 409


def test_same_date_allowed_for_another_tenant(client: TestClient) -> None:
    response = client.post(
        '/api/v1/holidays',
        headers={'Authorization': 'Bearer valid-admin-other-tenant-token'},
        json={'date': '2026-05-01', 'name': 'Tag der Arbeit', 'active': True},
    )
    assert response.status_code == 200
