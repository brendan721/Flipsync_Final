"""
V3 User Profile and Preferences API Routes

Implements the user profile system required for V3 adaptive content features.
Provides inventory source preferences and user customization for the Flutter frontend.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from fs_agt_clean.api.dependencies.dependencies import get_current_user
from fs_agt_clean.core.models.user import UnifiedUserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/users", tags=["V3 User Profile"])


class UserProfileV3(BaseModel):
    """V3 User Profile Model."""

    user_id: str
    inventory_source: str = Field(
        ..., description="liquidation, thrifting, or miscellaneous"
    )
    selling_style: str = Field(..., description="aggressive, balanced, or conservative")
    inventory_size: str = Field(..., description="small, medium, or large")
    ebay_location: Optional[str] = Field(
        None, description="ZIP code for shipping calculations"
    )
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserPreferencesV3(BaseModel):
    """V3 User Preferences Model."""

    inventory_source: str = Field(..., description="Primary inventory sourcing method")
    selling_style: str = Field(..., description="Selling approach preference")
    inventory_size: str = Field(..., description="Current inventory size")
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)
    optimization_settings: Dict[str, Any] = Field(default_factory=dict)
    collaboration_preferences: Dict[str, Any] = Field(default_factory=dict)


class UserProfileUpdateRequest(BaseModel):
    """Request model for updating user profile."""

    inventory_source: Optional[str] = None
    selling_style: Optional[str] = None
    inventory_size: Optional[str] = None
    ebay_location: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


# In-memory storage for development (replace with database in production)
_user_profiles: Dict[str, UserProfileV3] = {}


@router.get("/profile", response_model=UserProfileV3)
async def get_user_profile(
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> UserProfileV3:
    """
    Get the current user's V3 profile with inventory source preferences.

    Returns user profile including:
    - Inventory source preference (liquidation, thrifting, miscellaneous)
    - Selling style (aggressive, balanced, conservative)
    - eBay location for shipping calculations
    - Custom preferences and settings
    """
    try:
        user_id = current_user.id

        # Check if profile exists
        if user_id not in _user_profiles:
            # Create default profile
            default_profile = UserProfileV3(
                user_id=user_id,
                inventory_source="miscellaneous",
                selling_style="balanced",
                inventory_size="medium",
                ebay_location=None,
                preferences={
                    "notifications_enabled": True,
                    "auto_optimization": True,
                    "collaboration_level": "standard",
                },
            )
            _user_profiles[user_id] = default_profile
            logger.info(f"Created default V3 profile for user {user_id}")

        profile = _user_profiles[user_id]
        logger.info(
            f"Retrieved V3 profile for user {user_id}: {profile.inventory_source}"
        )

        return profile

    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user profile: {str(e)}",
        )


@router.put("/profile", response_model=UserProfileV3)
async def update_user_profile(
    update_request: UserProfileUpdateRequest,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> UserProfileV3:
    """
    Update the current user's V3 profile.

    Allows updating:
    - Inventory source preference
    - Selling style
    - Inventory size
    - eBay location
    - Custom preferences
    """
    try:
        user_id = current_user.id

        # Get existing profile or create default
        if user_id not in _user_profiles:
            _user_profiles[user_id] = UserProfileV3(
                user_id=user_id,
                inventory_source="miscellaneous",
                selling_style="balanced",
                inventory_size="medium",
            )

        profile = _user_profiles[user_id]

        # Update fields if provided
        if update_request.inventory_source is not None:
            if update_request.inventory_source not in [
                "liquidation",
                "thrifting",
                "miscellaneous",
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid inventory_source. Must be: liquidation, thrifting, or miscellaneous",
                )
            profile.inventory_source = update_request.inventory_source

        if update_request.selling_style is not None:
            if update_request.selling_style not in [
                "aggressive",
                "balanced",
                "conservative",
            ]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid selling_style. Must be: aggressive, balanced, or conservative",
                )
            profile.selling_style = update_request.selling_style

        if update_request.inventory_size is not None:
            if update_request.inventory_size not in ["small", "medium", "large"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid inventory_size. Must be: small, medium, or large",
                )
            profile.inventory_size = update_request.inventory_size

        if update_request.ebay_location is not None:
            profile.ebay_location = update_request.ebay_location

        if update_request.preferences is not None:
            profile.preferences.update(update_request.preferences)

        profile.updated_at = datetime.now(timezone.utc)
        _user_profiles[user_id] = profile

        logger.info(f"Updated V3 profile for user {user_id}")
        return profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user profile: {str(e)}",
        )


@router.get("/preferences", response_model=UserPreferencesV3)
async def get_user_preferences(
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> UserPreferencesV3:
    """
    Get the current user's V3 preferences.

    Returns simplified preferences for quick access by frontend components.
    """
    try:
        profile = await get_user_profile(current_user)

        preferences = UserPreferencesV3(
            inventory_source=profile.inventory_source,
            selling_style=profile.selling_style,
            inventory_size=profile.inventory_size,
            notification_preferences=profile.preferences.get("notifications", {}),
            optimization_settings=profile.preferences.get("optimization", {}),
            collaboration_preferences=profile.preferences.get("collaboration", {}),
        )

        return preferences

    except Exception as e:
        logger.error(f"Error retrieving user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user preferences: {str(e)}",
        )


@router.post("/preferences", response_model=UserPreferencesV3)
async def set_user_preferences(
    preferences: UserPreferencesV3,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> UserPreferencesV3:
    """
    Set the current user's V3 preferences.

    Updates the user profile with new preference settings.
    """
    try:
        # Update profile with new preferences
        update_request = UserProfileUpdateRequest(
            inventory_source=preferences.inventory_source,
            selling_style=preferences.selling_style,
            inventory_size=preferences.inventory_size,
            preferences={
                "notifications": preferences.notification_preferences,
                "optimization": preferences.optimization_settings,
                "collaboration": preferences.collaboration_preferences,
            },
        )

        await update_user_profile(update_request, current_user)

        logger.info(f"Updated preferences for user {current_user.id}")
        return preferences

    except Exception as e:
        logger.error(f"Error setting user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set user preferences: {str(e)}",
        )
