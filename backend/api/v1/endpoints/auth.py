from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.auth import AuthContext, require_authenticated_user
from backend.schemas.auth import MeRead

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=MeRead)
def get_me(context: AuthContext = Depends(require_authenticated_user)) -> MeRead:
    if context.internal_user_id is None or context.internal_role is None or context.tenant_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication context")

    return MeRead(
        user_id=context.internal_user_id,
        username=context.username,
        email=context.email or "",
        role=context.internal_role,
        tenant_id=context.tenant_id,
    )
