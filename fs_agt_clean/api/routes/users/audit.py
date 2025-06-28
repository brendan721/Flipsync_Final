"""UnifiedUser audit endpoints."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.security.auth import get_current_user, require_permissions

router = APIRouter(tags=["user-audit"])


@router.get("/{user_id}/activity", response_model=List[Dict[str, Any]])
async def get_user_activity(
    user_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
    limit: int = Query(100, description="Maximum number of activities to return"),
    offset: int = Query(0, description="Number of activities to skip"),
):
    """Get user activity log."""
    if not require_permissions(current_user, ["users:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view user activity",
        )

    # Mock implementation
    return [
        {
            "id": "activity_1",
            "user_id": user_id,
            "action": "login",
            "timestamp": datetime.now().isoformat(),
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
        },
        {
            "id": "activity_2",
            "user_id": user_id,
            "action": "profile_update",
            "timestamp": datetime.now().isoformat(),
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
        },
    ]


@router.get("/{user_id}/sessions", response_model=List[Dict[str, Any]])
async def get_user_sessions(
    user_id: str,
    current_user: UnifiedUser = Depends(get_current_user),
):
    """Get active user sessions."""
    if not require_permissions(current_user, ["users:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view user sessions",
        )

    # Mock implementation
    return [
        {
            "session_id": "session_1",
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "ip_address": "192.168.1.1",
            "user_agent": "Mozilla/5.0...",
            "is_active": True,
        }
    ]
