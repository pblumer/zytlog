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
from backend.models.enums import TenantType, UserRole
from backend.models.tenant import Tenant
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
        demo_tenant = Tenant(name="Demo Company", slug="demo-co", active=True, timezone="UTC")
        second_tenant = Tenant(name="Second Company", slug="second-co", active=True, timezone="Europe/Zurich")
        session.add_all([demo_tenant, second_tenant])
        session.flush()
        session.add_all(
            [
                User(
                    tenant_id=demo_tenant.id,
                    email="system.admin@zytlog.local",
                    full_name="System Admin",
                    keycloak_user_id="kc-system-admin",
                    role=UserRole.SYSTEM_ADMIN,
                ),
                User(
                    tenant_id=demo_tenant.id,
                    email="admin@zytlog.local",
                    full_name="Tenant Admin",
                    keycloak_user_id="kc-admin",
                    role=UserRole.ADMIN,
                ),
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

    with TestClient(app) as test_client:
        yield test_client


def test_list_tenants_requires_system_admin(client: TestClient) -> None:
    response = client.get("/api/v1/system/tenants", headers={"Authorization": "Bearer admin-token"})
    assert response.status_code == 403


def test_system_admin_can_list_tenants(client: TestClient) -> None:
    response = client.get("/api/v1/system/tenants", headers={"Authorization": "Bearer system-admin-token"})
    assert response.status_code == 200
    payload = response.json()
    assert [item["slug"] for item in payload] == ["demo-co", "second-co"]


def test_system_admin_can_create_tenant(client: TestClient) -> None:
    response = client.post(
        "/api/v1/system/tenants",
        headers={"Authorization": "Bearer system-admin-token"},
        json={
            "name": "Third Company",
            "slug": "third-co",
            "active": True,
            "type": "company",
            "timezone": "Europe/Zurich",
            "default_holiday_set_id": None,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["slug"] == "third-co"
    assert payload["type"] == TenantType.COMPANY.value


def test_create_tenant_rejects_duplicate_slug(client: TestClient) -> None:
    response = client.post(
        "/api/v1/system/tenants",
        headers={"Authorization": "Bearer system-admin-token"},
        json={
            "name": "Duplicate Demo",
            "slug": "demo-co",
            "active": True,
            "type": "company",
            "timezone": "UTC",
            "default_holiday_set_id": None,
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Tenant slug already exists"


def test_system_admin_can_update_tenant(client: TestClient) -> None:
    response = client.patch(
        "/api/v1/system/tenants/1",
        headers={"Authorization": "Bearer system-admin-token"},
        json={
            "name": "Demo Company Updated",
            "timezone": "Europe/Zurich",
            "active": False,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Demo Company Updated"
    assert payload["timezone"] == "Europe/Zurich"
    assert payload["active"] is False
