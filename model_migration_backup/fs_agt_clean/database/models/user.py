# AGENT_CONTEXT: user - Core FlipSync component with established patterns
"""User models for FlipSync."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRole(str, Enum):
    """User role enum."""

    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"


class UserStatus(str, Enum):
    """User status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class MfaType(str, Enum):
    """MFA type enum."""

    NONE = "none"
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"


class User(BaseModel):
    """User model for FlipSync."""

    id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)
    mfa_enabled: bool = False
    mfa_type: MfaType = MfaType.NONE

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class UserResponse(BaseModel):
    """API response model for user data."""

    id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    mfa_enabled: bool = False

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
    )


class UserCreate(BaseModel):
    """Model for creating a new user."""

    email: str
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating a user."""

    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None


class UserLogin(BaseModel):
    """Model for user login."""

    email: str
    password: str


class LoginRequest(BaseModel):
    """API request model for user login."""

    email: str
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """API response model for user login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: User


class UserRegistration(BaseModel):
    """Model for user registration."""

    email: str
    username: str
    password: str
    password_confirm: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class RegistrationRequest(BaseModel):
    """API request model for user registration."""

    email: str
    username: str
    password: str
    password_confirm: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    phone_number: Optional[str] = None
    role: Optional[str] = None


class RegistrationResponse(BaseModel):
    """API response model for user registration."""

    user_id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "user"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    verification_required: bool = True


class PasswordResetRequest(BaseModel):
    """API request model for password reset."""

    email: str


class PasswordResetResponse(BaseModel):
    """API response model for password reset."""

    email: str
    reset_sent: bool


class PasswordChangeRequest(BaseModel):
    """API request model for password change."""

    current_password: str
    new_password: str
    new_password_confirm: str


class PasswordChangeResponse(BaseModel):
    """API response model for password change."""

    success: bool
    message: str


class MfaSetupRequest(BaseModel):
    """API request model for MFA setup."""

    mfa_type: MfaType
    phone_number: Optional[str] = None  # For SMS verification


class MfaSetupResponse(BaseModel):
    """API response model for MFA setup."""

    secret_key: Optional[str] = None  # For TOTP
    qr_code_url: Optional[str] = None  # For TOTP
    verification_sent: bool = False  # For SMS/Email
    next_step: str


class MfaVerifyRequest(BaseModel):
    """API request model for MFA verification."""

    code: str


class MfaVerifyResponse(BaseModel):
    """API response model for MFA verification."""

    success: bool
    message: str
    backup_codes: Optional[List[str]] = None


class VerificationRequest(BaseModel):
    """API request model for email verification."""

    user_id: str
    verification_code: str


class VerificationResponse(BaseModel):
    """API response model for email verification."""

    success: bool
    message: str
    user_id: str
    email: str
    status: UserStatus = UserStatus.ACTIVE
