"""UnifiedUser access control endpoints."""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.security.auth import get_current_user, require_permissions

router = APIRouter(tags=["user-access-control"])


@router.post("/{user_id}/enable", response_model=Dict[str, Any])
async def enable_user(
    user_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Enable a user account."""
    if not require_permissions(current_user, ["users:update"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to enable users",
        )

    return {
        "status": "success",
        "message": f"UnifiedUser {user_id} enabled",
        "user_id": user_id,
    }


@router.post("/{user_id}/disable", response_model=Dict[str, Any])
async def disable_user(
    user_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Disable a user account."""
    if not require_permissions(current_user, ["users:update"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to disable users",
        )

    return {
        "status": "success",
        "message": f"UnifiedUser {user_id} disabled",
        "user_id": user_id,
    }
