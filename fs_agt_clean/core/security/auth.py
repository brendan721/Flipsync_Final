"""
Core authentication functions for security-related operations.

This module provides functions for token verification, user authentication,
and permission checking, without containing API route definitions.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.core.models.user import UnifiedUserResponse

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


def get_auth_service(request: Request) -> AuthService:
    """Get the authentication service from the application state.

    Args:
        request: The FastAPI request object

    Returns:
        AuthService: The authentication service
    """
    # Get the auth service from the application state
    if hasattr(request.app.state, "auth"):
        return request.app.state.auth

    # Log error if auth service not found
    logger.error("Auth service not found in application state")
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
        # Decode the token using the secret key
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UnifiedUserResponse:
    """Get the current authenticated user from the token.

    Args:
        token: The JWT token from the Authorization header

    Returns:
        UnifiedUser: The authenticated user

    Raises:
        HTTPException: If authentication fails
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = await verify_token(token)
        if payload is None:
            raise credentials_exception

        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception

        # In a real implementation, you would fetch the user from a database
        # For testing purposes, create a mock user using the response model
        user = UnifiedUserResponse(
            id=username,
            email=payload.get("email", "user@example.com"),
            username=payload.get("username", username),
            first_name=payload.get("first_name", "Test"),
            last_name=payload.get("last_name", "User"),
            status="active",
            is_active=True,
            is_verified=True,
            is_admin=payload.get("permissions", []).count("admin") > 0,
            mfa_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
        )
        return user
    except JWTError:
        raise credentials_exception


async def get_current_user_optional(
    authorization: Optional[str] = Header(None),
) -> Optional[UnifiedUserResponse]:
    """Get the current authenticated user from the token, but return None if not authenticated.

    Args:
        authorization: The Authorization header (optional)

    Returns:
        Optional[UnifiedUserResponse]: The authenticated user or None if not authenticated
    """
    if not authorization:
        return None

    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]  # Remove "Bearer " prefix

    try:
        # Verify the token and get user info
        payload = await verify_token(token)
        if not payload:
            return None

        # Extract user information from token
        username = payload.get("sub")
        if not username:
            return None

        # Create a mock user using the response model
        user = UnifiedUserResponse(
            id=username,
            email=payload.get("email", "user@example.com"),
            username=payload.get("username", username),
            first_name=payload.get("first_name", "Test"),
            last_name=payload.get("last_name", "User"),
            status="active",
            is_active=True,
            is_verified=True,
            is_admin=payload.get("permissions", []).count("admin") > 0,
            mfa_enabled=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
        )

        return user

    except Exception as e:
        logger.warning(f"Optional authentication failed: {str(e)}")
        return None


async def get_admin_user(
    user: UnifiedUserResponse = Depends(get_current_user),
) -> UnifiedUserResponse:
    """Get the current user and verify they have admin role.

    Args:
        user: The authenticated user

    Returns:
        UnifiedUser: The authenticated admin user

    Raises:
        HTTPException: If the user is not an admin
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Admin role required.",
        )
    return user


def require_permissions(required_permissions: List[str]):
    """Create a dependency that requires specific permissions.

    Args:
        required_permissions: List of required permission strings

    Returns:
        A dependency function for use with FastAPI
    """

    async def permission_dependency(
        user: UnifiedUserResponse = Depends(get_current_user),
    ) -> UnifiedUserResponse:
        # In a real implementation, you would check against user permissions
        # For demonstration, assume the user has permissions based on their admin status
        user_permissions = []
        if user.is_admin:
            user_permissions = ["admin", "read", "write", "delete"]
        else:
            user_permissions = ["read", "write"]

        # Check if user has any of the required permissions
        if not any(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permissions}",
            )
        return user

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
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
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
