"""
UnifiedUser management endpoints for FlipSync API.

This module implements endpoints for:
1. Creating, retrieving, updating, and deleting users
2. Managing user profiles and settings
3. Handling user-specific operations
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field

from fs_agt_clean.core.models.api_response import ApiResponse
from fs_agt_clean.core.models.user import (
    UnifiedUser,
    UnifiedUserCreate,
    UnifiedUserResponse,
    UnifiedUserRole,
    UnifiedUserStatus,
    UnifiedUserUpdate,
)
from fs_agt_clean.core.security.auth import get_current_user, require_permissions
from fs_agt_clean.services.user.user_service import UnifiedUserService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="",
    tags=["users"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Not authenticated"},
        status.HTTP_403_FORBIDDEN: {"description": "Not authorized"},
        status.HTTP_404_NOT_FOUND: {"description": "UnifiedUser not found"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Validation error"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


def get_user_service() -> UnifiedUserService:
    """Get the user service."""
    return UnifiedUserService()


@router.post(
    "",
    response_model=UnifiedUserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user with the provided information.",
)
async def create_user(
    user_create: UnifiedUserCreate,
    current_user: UnifiedUser = Depends(get_current_user),
    user_service: UnifiedUserService = Depends(get_user_service),
) -> UnifiedUserResponse:
    """Create a new user."""
    # Check if user has permission to create users
    if not require_permissions(current_user, ["users:create"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create users",
        )

    try:
        # Create user
        user = await user_service.create_user(user_create.dict())

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user",
            )

        return UnifiedUserResponse.from_user(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user",
        )


@router.get(
    "",
    response_model=List[UnifiedUserResponse],
    summary="Get all users",
    description="Get all users with optional filtering and pagination.",
)
async def get_users(
    current_user: UnifiedUser = Depends(get_current_user),
    user_service: UnifiedUserService = Depends(get_user_service),
    skip: int = Query(0, description="Number of users to skip"),
    limit: int = Query(100, description="Maximum number of users to return"),
    role: Optional[UnifiedUserRole] = Query(None, description="Filter by role"),
    status: Optional[UnifiedUserStatus] = Query(None, description="Filter by status"),
) -> List[UnifiedUserResponse]:
    """Get all users."""
    # Check if user has permission to view users
    if not require_permissions(current_user, ["users:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users",
        )

    try:
        # Get users
        users = await user_service.get_all_users(skip=skip, limit=limit)

        # Filter by role and status if provided
        if role:
            users = [user for user in users if user.role == role]
        if status:
            users = [user for user in users if user.status == status]

        return [UnifiedUserResponse.from_user(user) for user in users]
    except Exception as e:
        logger.error(f"Error getting users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users",
        )


@router.get(
    "/{user_id}",
    response_model=UnifiedUserResponse,
    summary="Get a user by ID",
    description="Get a user by their ID.",
)
async def get_user(
    user_id: str = Path(..., description="UnifiedUser ID"),
    current_user: UnifiedUser = Depends(get_current_user),
    user_service: UnifiedUserService = Depends(get_user_service),
) -> UnifiedUserResponse:
    """Get a user by ID."""
    # Check if user has permission to view users
    if not require_permissions(current_user, ["users:read"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view users",
        )

    try:
        # Get user
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UnifiedUser not found",
            )

        return UnifiedUserResponse.from_user(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user",
        )


@router.put(
    "/{user_id}",
    response_model=UnifiedUserResponse,
    summary="Update a user",
    description="Update a user with the provided information.",
)
async def update_user(
    user_update: UnifiedUserUpdate,
    user_id: str = Path(..., description="UnifiedUser ID"),
    current_user: UnifiedUser = Depends(get_current_user),
    user_service: UnifiedUserService = Depends(get_user_service),
) -> UnifiedUserResponse:
    """Update a user."""
    # Check if user has permission to update users
    if not require_permissions(current_user, ["users:update"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update users",
        )

    try:
        # Check if user exists
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UnifiedUser not found",
            )

        # Update user
        user_data = user_update.dict(exclude_unset=True)
        updated_user = await user_service.update_user(user_id, user_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to update user",
            )

        return UnifiedUserResponse.from_user(updated_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user",
        )


@router.delete(
    "/{user_id}",
    response_model=ApiResponse,
    summary="Delete a user",
    description="Delete a user by their ID.",
)
async def delete_user(
    user_id: str = Path(..., description="UnifiedUser ID"),
    current_user: UnifiedUser = Depends(get_current_user),
    user_service: UnifiedUserService = Depends(get_user_service),
) -> ApiResponse:
    """Delete a user."""
    # Check if user has permission to delete users
    if not require_permissions(current_user, ["users:delete"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete users",
        )

    try:
        # Check if user exists
        user = await user_service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="UnifiedUser not found",
            )

        # Delete user
        success = await user_service.delete_user(user_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete user",
            )

        return ApiResponse(
            success=True,
            message=f"UnifiedUser {user_id} deleted successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )


@router.get(
    "/me",
    response_model=UnifiedUserResponse,
    summary="Get current user",
    description="Get the current authenticated user's profile.",
)
async def get_current_user_profile(
    current_user: UnifiedUser = Depends(get_current_user),
) -> UnifiedUserResponse:
    """Get current user profile."""
    return UnifiedUserResponse.from_user(current_user)
