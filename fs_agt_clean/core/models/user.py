"""
UnifiedUser models for FlipSync authentication system.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, EmailStr


class UnifiedUserStatus(str, Enum):
    """User status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class UnifiedUserRole(str, Enum):
    """User role enumeration."""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UnifiedUserResponse"


class RegistrationRequest(BaseModel):
    """Registration request model."""

    email: EmailStr
    password: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class RegistrationResponse(BaseModel):
    """Registration response model."""

    success: bool
    message: str
    user_id: Optional[str] = None
    verification_required: bool = True


class VerificationRequest(BaseModel):
    """Email verification request model."""

    user_id: str
    verification_code: str


class VerificationResponse(BaseModel):
    """Email verification response model."""

    success: bool
    message: str
    user_id: str
    email: str
    status: UnifiedUserStatus


class UnifiedUserResponse(BaseModel):
    """Unified user response model."""

    id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: UnifiedUserStatus
    role: UnifiedUserRole = UnifiedUserRole.USER
    is_active: bool = True
    is_verified: bool = False
    is_admin: bool = False
    mfa_enabled: bool = False
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_admin:
            return True
        # Add more permission logic as needed
        return permission in ["user", "basic"]
