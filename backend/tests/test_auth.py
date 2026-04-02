from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
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
        if token == "valid-new-user-token":
            return type(
                "Claims",
                (),
                {
                    "sub": "kc-new-user",
                    "preferred_username": "new.employee",
                    "email": "new.employee@zytlog.local",
                    "realm_roles": ["employee"],
                    "resource_roles": {"zytlog-api": ["employee"]},
                },
            )()
        if token == "valid-relinked-user-token":
            return type(
                "Claims",
                (),
                {
                    "sub": "kc-recreated-employee",
                    "preferred_username": "employee.recreated",
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
        other_tenant = Tenant(name="Test Tenant", slug="test", active=True, timezone="UTC")
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
    previous_provisioning_tenant_slug = settings.provisioning_tenant_slug
    previous_bootstrap_admin_enabled = settings.bootstrap_admin_enabled
    previous_bootstrap_admin_sub = settings.bootstrap_admin_sub
    previous_bootstrap_admin_email = settings.bootstrap_admin_email
    settings.auth_enabled = True
    settings.provisioning_tenant_slug = "demo-co"
    settings.bootstrap_admin_enabled = False
    settings.bootstrap_admin_sub = None
    settings.bootstrap_admin_email = None

    with TestClient(app) as test_client:
        yield test_client

    settings.auth_enabled = previous_auth_enabled
    settings.provisioning_tenant_slug = previous_provisioning_tenant_slug
    settings.bootstrap_admin_enabled = previous_bootstrap_admin_enabled
    settings.bootstrap_admin_sub = previous_bootstrap_admin_sub
    settings.bootstrap_admin_email = previous_bootstrap_admin_email


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


def test_me_returns_authenticated_user_context_for_existing_user(
    client: TestClient,
    test_session_local: sessionmaker,
) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-admin-token"})
    assert response.status_code == 200
    payload = response.json()

    with test_session_local() as session:
        user = session.scalar(select(User).where(User.keycloak_user_id == "kc-admin"))
        assert user is not None

        assert payload["email"] == "admin@zytlog.local"
        assert payload["role"] == "admin"
        assert payload["user_id"] == user.id
        assert payload["tenant_id"] == user.tenant_id


def test_me_auto_provisions_new_keycloak_user(
    client: TestClient,
    test_session_local: sessionmaker,
) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-new-user-token"})
    assert response.status_code == 200
    payload = response.json()

    with test_session_local() as session:
        user = session.scalar(select(User).where(User.keycloak_user_id == "kc-new-user"))
        assert user is not None

        demo_tenant = session.scalar(select(Tenant).where(Tenant.slug == "demo-co"))
        assert demo_tenant is not None

        assert payload["email"] == "new.employee@zytlog.local"
        assert payload["role"] == "employee"
        assert payload["user_id"] == user.id
        assert payload["tenant_id"] == demo_tenant.id

        assert user.tenant_id == demo_tenant.id
        assert user.role == UserRole.EMPLOYEE


def test_me_relinks_existing_user_by_email_when_sub_changes(
    client: TestClient,
    test_session_local: sessionmaker,
) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-relinked-user-token"})
    assert response.status_code == 200
    payload = response.json()

    with test_session_local() as session:
        user = session.scalar(select(User).where(User.email == "employee@zytlog.local"))
        assert user is not None
        assert user.keycloak_user_id == "kc-recreated-employee"
        assert user.full_name == "employee.recreated"

        assert payload["email"] == "employee@zytlog.local"
        assert payload["role"] == "employee"
        assert payload["user_id"] == user.id


def test_me_relinked_user_login_does_not_create_duplicate_email_user(
    client: TestClient,
    test_session_local: sessionmaker,
) -> None:
    response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-relinked-user-token"})
    assert response.status_code == 200

    with test_session_local() as session:
        users = session.scalars(select(User).where(User.email == "employee@zytlog.local")).all()
        assert len(users) == 1


def test_me_promotes_existing_matching_bootstrap_user_when_no_admin_exists(
    client: TestClient,
    test_session_local: sessionmaker,
) -> None:
    with test_session_local() as session:
        admin = session.scalar(select(User).where(User.keycloak_user_id == "kc-admin"))
        assert admin is not None
        session.delete(admin)
        session.commit()

    settings.bootstrap_admin_enabled = True
    settings.bootstrap_admin_sub = "kc-employee"
    settings.bootstrap_admin_email = "employee@zytlog.local"

    response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-employee-token"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"

    with test_session_local() as session:
        employee = session.scalar(select(User).where(User.keycloak_user_id == "kc-employee"))
        assert employee is not None
        assert employee.role == UserRole.ADMIN


def test_me_does_not_promote_matching_bootstrap_user_if_admin_exists(
    client: TestClient,
    test_session_local: sessionmaker,
) -> None:
    settings.bootstrap_admin_enabled = True
    settings.bootstrap_admin_sub = "kc-employee"
    settings.bootstrap_admin_email = "employee@zytlog.local"

    response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-employee-token"})
    assert response.status_code == 200
    assert response.json()["role"] == "employee"

    with test_session_local() as session:
        employee = session.scalar(select(User).where(User.keycloak_user_id == "kc-employee"))
        assert employee is not None
        assert employee.role == UserRole.EMPLOYEE


def test_me_does_not_promote_non_matching_bootstrap_user_when_no_admin_exists(
    client: TestClient,
    test_session_local: sessionmaker,
) -> None:
    with test_session_local() as session:
        admin = session.scalar(select(User).where(User.keycloak_user_id == "kc-admin"))
        assert admin is not None
        session.delete(admin)
        session.commit()

    settings.bootstrap_admin_enabled = True
    settings.bootstrap_admin_sub = "other-sub"
    settings.bootstrap_admin_email = "other@zytlog.local"

    response = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-employee-token"})
    assert response.status_code == 200
    assert response.json()["role"] == "employee"

    with test_session_local() as session:
        employee = session.scalar(select(User).where(User.keycloak_user_id == "kc-employee"))
        assert employee is not None
        assert employee.role == UserRole.EMPLOYEE


def test_me_bootstrap_promotion_is_idempotent_across_repeated_logins(
    client: TestClient,
    test_session_local: sessionmaker,
) -> None:
    with test_session_local() as session:
        admin = session.scalar(select(User).where(User.keycloak_user_id == "kc-admin"))
        assert admin is not None
        session.delete(admin)
        session.commit()

    settings.bootstrap_admin_enabled = True
    settings.bootstrap_admin_sub = "kc-employee"
    settings.bootstrap_admin_email = "employee@zytlog.local"

    first = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-employee-token"})
    second = client.get("/api/v1/me", headers={"Authorization": "Bearer valid-employee-token"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["role"] == "admin"
    assert second.json()["role"] == "admin"

    with test_session_local() as session:
        employee = session.scalar(select(User).where(User.keycloak_user_id == "kc-employee"))
        admins = session.scalars(select(User).where(User.role == UserRole.ADMIN)).all()
        assert employee is not None
        assert employee.role == UserRole.ADMIN
        assert len(admins) == 1
