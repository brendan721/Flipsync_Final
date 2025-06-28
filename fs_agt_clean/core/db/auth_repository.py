"""Repository for authentication users."""

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Optional imports with graceful fallbacks
try:
    from fs_agt_clean.database.models.unified_user import (
        UnifiedUnifiedUser,
        Permission,
        Role,
        RolePermission,
        UnifiedUserPermission,
        UnifiedUserRole,
    )

    # Mark that we have real models
    _USING_REAL_MODELS = True
except ImportError:
    # Create mock classes for graceful fallback
    # IMPORTANT: These do NOT inherit from Base to avoid SQLAlchemy registry conflicts
    class MockUnifiedUnifiedUser:
        """Mock UnifiedUnifiedUser class for fallback when real models unavailable."""

        def __init__(self, *args, **kwargs):
            self.id = "mock-user-id"
            self.email = kwargs.get("email", "mock@example.com")
            self.username = kwargs.get("username", "mockuser")
            self.first_name = kwargs.get("first_name", "Mock")
            self.last_name = kwargs.get("last_name", "UnifiedUser")
            self.is_active = kwargs.get("is_active", True)
            self.is_verified = kwargs.get("is_verified", True)
            self.is_admin = kwargs.get("is_admin", False)
            self.last_login = None
            self.updated_at = None

        def verify_password(self, password):
            return True  # Mock always succeeds

    # Alias for compatibility
    UnifiedUnifiedUser = MockUnifiedUnifiedUser

    class Permission:
        def __init__(self, *args, **kwargs):
            self.id = "mock-permission-id"
            self.name = "mock-permission"

    class Role:
        def __init__(self, *args, **kwargs):
            self.id = "mock-role-id"
            self.name = "mock-role"

    class RolePermission:
        def __init__(self, *args, **kwargs):
            self.role_id = "mock-role-id"
            self.permission_id = "mock-permission-id"

    class UnifiedUserPermission:
        def __init__(self, *args, **kwargs):
            self.user_id = "mock-user-id"
            self.permission_id = "mock-permission-id"

    class UnifiedUserRole:
        def __init__(self, *args, **kwargs):
            self.user_id = "mock-user-id"
            self.role_id = "mock-role-id"


logger = logging.getLogger(__name__)


class AuthRepository:
    """Repository for authentication users."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository with a database session."""
        self.session = session

    async def get_user_by_id(self, user_id: str) -> Optional[UnifiedUnifiedUser]:
        """Get a user by ID."""
        result = await self.session.execute(
            select(UnifiedUnifiedUser).filter(UnifiedUnifiedUser.id == user_id)
        )
        return result.scalars().first()

    async def get_user_by_email(self, email: str) -> Optional[UnifiedUnifiedUser]:
        """Get a user by email."""
        result = await self.session.execute(
            select(UnifiedUnifiedUser).filter(UnifiedUnifiedUser.email == email)
        )
        return result.scalars().first()

    async def get_user_by_username(self, username: str) -> Optional[UnifiedUnifiedUser]:
        """Get a user by username."""
        result = await self.session.execute(
            select(UnifiedUnifiedUser).filter(UnifiedUnifiedUser.username == username)
        )
        return result.scalars().first()

    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: bool = True,
        is_verified: bool = False,
        is_admin: bool = False,
    ) -> UnifiedUnifiedUser:
        """Create a new user."""
        user = UnifiedUnifiedUser(
            email=email,
            username=username,
            password=password,  # This will be hashed in the model's __init__
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            is_verified=is_verified,
            is_admin=is_admin,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_user(self, user: UnifiedUnifiedUser) -> UnifiedUnifiedUser:
        """Update a user."""
        user.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user: UnifiedUnifiedUser) -> bool:
        """Delete a user.

        Args:
            user: The user to delete

        Returns:
            bool: True if the user was deleted successfully
        """
        try:
            await self.session.delete(user)
            await self.session.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            await self.session.rollback()
            return False

    async def update_last_login(self, user: UnifiedUnifiedUser) -> UnifiedUnifiedUser:
        """Update the user's last login timestamp."""
        user.last_login = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_permissions(self, user: UnifiedUnifiedUser) -> List[str]:
        """Get a list of permission names for a user."""
        # Get direct user permissions
        user_perms_query = (
            select(Permission)
            .join(UnifiedUserPermission, UnifiedUserPermission.permission_id == Permission.id)
            .filter(UnifiedUserPermission.user_id == user.id)
        )
        user_perms_result = await self.session.execute(user_perms_query)
        user_permissions = [perm.name for perm in user_perms_result.scalars().all()]

        # Get permissions from roles
        role_perms_query = (
            select(Permission)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(UnifiedUserRole, UnifiedUserRole.role_id == Role.id)
            .filter(UnifiedUserRole.user_id == user.id)
        )
        role_perms_result = await self.session.execute(role_perms_query)
        role_permissions = [perm.name for perm in role_perms_result.scalars().all()]

        # Combine and deduplicate
        all_permissions = list(set(user_permissions + role_permissions))

        # Add admin permission if user is admin
        if user.is_admin and "admin" not in all_permissions:
            all_permissions.append("admin")

        return all_permissions

    async def authenticate_user(
        self, username_or_email: str, password: str
    ) -> Tuple[bool, Optional[UnifiedUnifiedUser]]:
        """Authenticate a user by username/email and password."""
        # Try to find user by email
        user = await self.get_user_by_email(username_or_email)

        # If not found, try by username
        if not user:
            user = await self.get_user_by_username(username_or_email)

        # If still not found, authentication fails
        if not user:
            logger.warning(
                f"Authentication failed: UnifiedUser not found: {username_or_email}"
            )
            return False, None

        # Check if user is active
        if not user.is_active:
            logger.warning(
                f"Authentication failed: UnifiedUser is not active: {username_or_email}"
            )
            return False, None

        # Check if user is verified (unless in development mode)
        # In development mode, we'll allow unverified users to authenticate
        if not user.is_verified and not os.environ.get("ENVIRONMENT", "").lower() in (
            "development",
            "dev",
            "test",
        ):
            logger.warning(
                f"Authentication failed: UnifiedUser is not verified: {username_or_email}"
            )
            return False, None

        # Verify password
        if not user.verify_password(password):
            logger.warning(
                f"Authentication failed: Invalid password for user: {username_or_email}"
            )
            return False, None

        # Authentication successful
        logger.info(f"Authentication successful for user: {username_or_email}")
        return True, user
