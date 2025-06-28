"""UnifiedUser permissions management endpoints."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.security.auth import get_current_user, require_permissions

router = APIRouter(tags=["user-permissions"])


@router.get("/", response_model=List[Dict[str, Any]])
async def get_permissions(
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Get all available permissions."""
    if not require_permissions(current_user, ["users:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view permissions",
        )

    # Return available permissions
    return [
        {"name": "users:create", "description": "Create users"},
        {"name": "users:read", "description": "Read user data"},
        {"name": "users:update", "description": "Update users"},
        {"name": "users:delete", "description": "Delete users"},
        {"name": "marketplace:read", "description": "Read marketplace data"},
        {"name": "marketplace:write", "description": "Write marketplace data"},
    ]


@router.get("/{user_id}", response_model=List[str])
async def get_user_permissions(
    user_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Get permissions for a specific user."""
    if not require_permissions(current_user, ["users:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view user permissions",
        )

    # Mock implementation - return permissions based on role
    return ["users:read", "marketplace:read"]
