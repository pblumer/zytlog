from fastapi import APIRouter, Depends

from backend.api.deps import AuthContext, get_auth_context
from backend.schemas.user import UserRead

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=UserRead)
def get_me(context: AuthContext = Depends(get_auth_context)) -> UserRead:
    # TODO: Replace with user lookup from Keycloak subject + tenant claim mapping.
    return UserRead(
        id=context.user_id,
        tenant_id=context.tenant_id,
        email="stub.user@zytlog.local",
        full_name="Stub User",
        role=context.role,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:00:00Z",
    )
