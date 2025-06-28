"""
UnifiedUser profile management for FlipSync.

This module provides user profile management capabilities
for maintaining user context and preferences.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class UnifiedUserProfileManager:
    """
    Legacy user profile manager for backward compatibility.

    This class provides basic user profile management capabilities
    that are used by the chat service for legacy support.
    """

    def __init__(self):
        """Initialize the user profile manager."""
        self.user_profiles: Dict[str, Dict[str, Any]] = {}
        self.initialized = True
        logger.info("UnifiedUserProfileManager initialized for legacy support")

    def get_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Get user profile.

        Args:
            user_id: UnifiedUser identifier

        Returns:
            UnifiedUser profile dictionary
        """
        try:
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now().isoformat(),
                    "preferences": {},
                    "context": {},
                    "metadata": {},
                }

            return self.user_profiles[user_id]

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {"user_id": user_id, "error": str(e)}

    def update_profile(self, user_id: str, updates: Dict[str, Any]) -> None:
        """
        Update user profile.

        Args:
            user_id: UnifiedUser identifier
            updates: Profile updates
        """
        try:
            profile = self.get_profile(user_id)
            profile.update(updates)
            profile["updated_at"] = datetime.now().isoformat()

            logger.debug(f"Updated profile for user {user_id}")

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")

    def set_preference(self, user_id: str, key: str, value: Any) -> None:
        """
        Set user preference.

        Args:
            user_id: UnifiedUser identifier
            key: Preference key
            value: Preference value
        """
        try:
            profile = self.get_profile(user_id)
            if "preferences" not in profile:
                profile["preferences"] = {}

            profile["preferences"][key] = value
            profile["updated_at"] = datetime.now().isoformat()

            logger.debug(f"Set preference {key} for user {user_id}")

        except Exception as e:
            logger.error(f"Error setting user preference: {e}")

    def get_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Get user preference.

        Args:
            user_id: UnifiedUser identifier
            key: Preference key
            default: Default value if not found

        Returns:
            Preference value or default
        """
        try:
            profile = self.get_profile(user_id)
            return profile.get("preferences", {}).get(key, default)

        except Exception as e:
            logger.error(f"Error getting user preference: {e}")
            return default
