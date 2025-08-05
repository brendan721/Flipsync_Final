"""
Core authentication functions for security-related operations.

This module provides utility functions for token verification and permission checking.
Most authentication functionality has been migrated to the unified AuthService system.

MIGRATION STATUS:
- ✅ JWT secret handling standardized (Phase 1 complete)
- ✅ AuthService enhanced with unified entry points (Phase 2 complete)
- ✅ Critical endpoints migrated to use AuthService dependencies (Phase 3 complete)
- ✅ Legacy authentication functions removed (Phase 4 complete)

CURRENT FUNCTIONS:
- verify_token(): Token verification utility (still used by permission system)
- require_permissions(): Permission-based dependency factory
- create_access_token(): JWT token creation utility
- create_test_token(): Test token creation for development

NEW CODE SHOULD USE:
- fs_agt_clean.api.dependencies.dependencies.get_current_user
- fs_agt_clean.api.dependencies.dependencies.get_current_user_optional
- fs_agt_clean.api.dependencies.dependencies.require_admin_permission
- fs_agt_clean.api.dependencies.dependencies.require_marketplace_permission
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from fs_agt_clean.core.auth.auth_factory import AuthenticationFactory
from fs_agt_clean.database.models.unified_user import UnifiedUserResponse

logger = logging.getLogger(__name__)

# OAuth2 password bearer scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

# Constants for token creation and validation
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# Use the same secret as the auth services for consistency
# In development mode, use the same development secret
ENVIRONMENT = os.getenv("ENVIRONMENT", "").lower()
if ENVIRONMENT in ("development", "dev", "test"):
    SECRET_KEY = "development-jwt-secret-not-for-production-use"
    logger.info("Using development JWT secret for token validation")
else:
    SECRET_KEY = os.getenv("JWT_SECRET")
    # Validate that JWT_SECRET is set in production
    if not SECRET_KEY:
        logger.error(
            "JWT_SECRET environment variable is not set! This is a critical security issue."
        )
        raise ValueError("JWT_SECRET environment variable must be set for security")


async def get_auth_service():
    """Get the unified authentication system.

    Returns:
        UnifiedAuthSystem: The unified authentication system
    """
    try:
        return await AuthenticationFactory.get_auth_system()
    except Exception as e:
        logger.error(f"Failed to get unified authentication system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable",
        )


async def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token and return the payload.

    Args:
        token: The JWT token to verify

    Returns:
        The decoded token payload or None if verification fails
    """
    try:
        # Use the same secret loading logic as AuthService for consistency
        if ENVIRONMENT in ("development", "dev", "test"):
            secret = "development-jwt-secret-not-for-production-use"
        else:
            # In production, always use the environment variable
            # This ensures consistency with token creation
            secret = os.getenv("JWT_SECRET")
            if not secret:
                logger.error("JWT_SECRET environment variable not set in production")
                return None

        # Decode the token using the secret key
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


# REMOVED: Deprecated get_current_user function
# This function has been replaced by fs_agt_clean.api.dependencies.dependencies.get_current_user
# All endpoints should now use the unified AuthService system


# REMOVED: Deprecated get_current_user_optional function
# This function has been replaced by unified dependencies get_current_user_optional
# All endpoints should now use the unified AuthService system


# DEPRECATED: get_admin_user function
# This function should be replaced by unified dependencies require_admin_permission
# Use require_admin_permission dependency for admin-only endpoints


def require_permissions(required_permissions: List[str]):
    """Create a dependency that requires specific permissions.

    DEPRECATED: This function is deprecated in favor of permission-based dependencies.
    Use fs_agt_clean.api.dependencies.dependencies.require_admin_permission or
    require_marketplace_permission for new code.

    Args:
        required_permissions: List of required permission strings

    Returns:
        A dependency function for use with FastAPI
    """
    import warnings

    warnings.warn(
        "require_permissions is deprecated. Use permission-based dependencies instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    async def permission_dependency(
        user: UnifiedUserResponse = Depends(lambda: None),  # Placeholder
    ) -> UnifiedUserResponse:
        # Simple permission check based on admin status
        if user and hasattr(user, "is_admin") and user.is_admin:
            return user

        # For non-admin users, allow basic permissions
        if user and any(perm in ["read", "write"] for perm in required_permissions):
            return user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {required_permissions}",
        )

    return permission_dependency


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a new JWT access token.

    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time delta

    Returns:
        str: Encoded JWT token
    """
    # Use the same secret loading logic for consistency
    if ENVIRONMENT in ("development", "dev", "test"):
        secret = "development-jwt-secret-not-for-production-use"
    else:
        secret = os.getenv("JWT_SECRET")
        if not secret:
            raise ValueError("JWT_SECRET environment variable not set in production")

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=ALGORITHM)
    return encoded_jwt


def create_test_token(subject: str, role: str = "admin") -> str:
    """Create a test JWT token for testing purposes.

    Args:
        subject: The subject (user ID) for the token
        role: The role to include in the token

    Returns:
        str: Encoded JWT token for testing
    """
    data = {"sub": subject, "role": role, "email": f"{subject}@example.com"}
    return create_access_token(data, timedelta(minutes=60))
