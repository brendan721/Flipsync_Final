"""UnifiedUser roles management endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from fs_agt_clean.core.models.user import UnifiedUser, UnifiedUserRole
from fs_agt_clean.core.security.auth import get_current_user, require_permissions

router = APIRouter(tags=["user-roles"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_roles(
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Get all available user roles."""
    if not require_permissions(current_user, ["users:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view roles",
        )

    # Return available roles
    return [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "seller", "description": "Seller with marketplace access"},
        {"name": "viewer", "description": "Read-only access"},
    ]


@router.post("/{user_id}/assign", response_model=Dict[str, Any])
async def assign_role(
    user_id: str,
    role_data: Dict[str, Any],
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Assign a role to a user."""
    if not require_permissions(current_user, ["users:update"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to assign roles",
        )

    # Mock implementation
    return {
        "status": "success",
        "message": f"Role assigned to user {user_id}",
        "user_id": user_id,
        "role": role_data.get("role"),
    }
