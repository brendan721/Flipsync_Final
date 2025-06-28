"""UnifiedUser service for managing user data."""

import logging
from datetime import datetime
from typing import Dict, List, Optional

# Optional imports with graceful fallbacks
try:
    from fs_agt_clean.core.models.user import UnifiedUser, UnifiedUserRole, UnifiedUserStatus
except ImportError:
    # Create mock classes for graceful fallback
    from datetime import datetime
    from enum import Enum

    class UnifiedUserRole(Enum):
        USER = "user"
        ADMIN = "admin"
        MODERATOR = "moderator"

    class UnifiedUserStatus(Enum):
        ACTIVE = "active"
        INACTIVE = "inactive"
        SUSPENDED = "suspended"

    class UnifiedUser:
        def __init__(self, **kwargs):
            self.id = kwargs.get("id", "mock-user-id")
            self.email = kwargs.get("email", "mock@example.com")
            self.username = kwargs.get("username", "mockuser")
            self.first_name = kwargs.get("first_name", "Mock")
            self.last_name = kwargs.get("last_name", "UnifiedUser")
            self.role = kwargs.get("role", UnifiedUserRole.USER)
            self.status = kwargs.get("status", UnifiedUserStatus.ACTIVE)
            self.created_at = kwargs.get("created_at", datetime.now())
            self.updated_at = kwargs.get("updated_at", datetime.now())
            self.last_login = kwargs.get("last_login")
            self.mfa_enabled = kwargs.get("mfa_enabled", False)


logger = logging.getLogger(__name__)


class UnifiedUserService:
    """Service for managing user data."""

    def __init__(self):
        """Initialize the user service."""
        self._users = {}  # In-memory user storage for testing

    async def create_user(self, user_data: Dict) -> UnifiedUser:
        """Create a new user."""
        user_id = f"user_{len(self._users) + 1}"

        user = UnifiedUser(
            id=user_id,
            email=user_data.get("email", ""),
            username=user_data.get("username", ""),
            first_name=user_data.get("first_name"),
            last_name=user_data.get("last_name"),
            role=UnifiedUserRole(user_data.get("role", UnifiedUserRole.USER)),
            status=UnifiedUserStatus(user_data.get("status", UnifiedUserStatus.ACTIVE)),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_login=None,
            mfa_enabled=False,
        )

        self._users[user_id] = user
        return user

    async def get_user_by_id(self, user_id: str) -> Optional[UnifiedUser]:
        """Get a user by ID."""
        return self._users.get(user_id)

    async def get_user_by_email(self, email: str) -> Optional[UnifiedUser]:
        """Get a user by email."""
        for user in self._users.values():
            if user.email == email:
                return user
        return None

    async def get_user_by_username(self, username: str) -> Optional[UnifiedUser]:
        """Get a user by username."""
        for user in self._users.values():
            if user.username == username:
                return user
        return None

    async def get_all_users(self) -> List[UnifiedUser]:
        """Get all users."""
        return list(self._users.values())

    async def update_user(self, user_id: str, user_data: Dict) -> Optional[UnifiedUser]:
        """Update a user."""
        user = self._users.get(user_id)
        if not user:
            return None

        # Update user fields
        for key, value in user_data.items():
            if hasattr(user, key):
                setattr(user, key, value)

        user.updated_at = datetime.now()
        self._users[user_id] = user
        return user

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    async def authenticate_user(self, email: str, password: str) -> Optional[UnifiedUser]:
        """Authenticate a user with email and password."""
        # This is a mock implementation for testing
        # In a real implementation, you would verify the password
        user = await self.get_user_by_email(email)
        if user:
            # Mock successful authentication
            return user
        return None
