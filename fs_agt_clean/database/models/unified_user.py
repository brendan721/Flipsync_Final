"""
Unified UnifiedUser Models for FlipSync Database
=========================================

This module consolidates all user-related database models into a single,
standardized hierarchy, eliminating duplication across:
- fs_agt_clean/database/models/user.py (Pydantic models)
- fs_agt_clean/database/models/users.py (SQLAlchemy models)
- fs_agt_clean/core/models/database/auth_user.py (SQLAlchemy models)

AGENT_CONTEXT: Complete user management system with authentication, authorization, and account management
AGENT_PRIORITY: Database models for user management, roles, permissions, and marketplace accounts
AGENT_PATTERN: SQLAlchemy async models with proper relationships and Pydantic API models
"""

import secrets
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import bcrypt
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .unified_base import Base


# Enums for user management
class UnifiedUserRole(str, Enum):
    """UnifiedUser role enum."""

    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    SELLER = "seller"
    VIEWER = "viewer"


class UnifiedUserStatus(str, Enum):
    """UnifiedUser status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"
    LOCKED = "locked"


class AccountType(str, Enum):
    """Account type enum."""

    PERSONAL = "personal"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"
    MARKETPLACE = "marketplace"


class AccountStatus(str, Enum):
    """Account status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class MfaType(str, Enum):
    """MFA type enum."""

    NONE = "none"
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"


# Association table for user-role many-to-many relationship
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(255), ForeignKey("unified_users.id"), primary_key=True),
    Column("role_id", String(255), ForeignKey("roles.id"), primary_key=True),
    extend_existing=True,
)


class UnifiedUser(Base):
    """
    Unified UnifiedUser Model - Consolidates all user functionality

    This model combines features from:
    - UnifiedUnifiedUser (authentication and security)
    - UnifiedUser (basic user information)
    - MarketUnifiedUserAccount (marketplace-specific features)
    """

    __tablename__ = "unified_users"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # Basic user information
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Authentication fields
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Status and role fields
    status: Mapped[UnifiedUserStatus] = mapped_column(
        String(50), default=UnifiedUserStatus.ACTIVE
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Security and MFA
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_type: Mapped[MfaType] = mapped_column(String(20), default=MfaType.NONE)
    mfa_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # API and quota management
    api_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True
    )
    quota_multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # UnifiedUser preferences and metadata
    preferences: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, default="en"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=user_roles, back_populates="users"
    )
    accounts: Mapped[List["UnifiedUserAccount"]] = relationship(
        "UnifiedUserAccount", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["UnifiedUserSession"]] = relationship(
        "UnifiedUserSession", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user", cascade="all, delete-orphan"
    )
    dashboards: Mapped[List["DashboardModel"]] = relationship(
        "DashboardModel", back_populates="user", cascade="all, delete-orphan"
    )

    def __init__(self, email: str, username: str, password: str, **kwargs):
        """Initialize user with hashed password"""
        super().__init__()
        self.email = email
        self.username = username
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.status = kwargs.get("status", UnifiedUserStatus.ACTIVE)
        self.is_active = kwargs.get("is_active", True)
        self.is_verified = kwargs.get("is_verified", False)
        self.is_admin = kwargs.get("is_admin", False)
        self.timezone = kwargs.get("timezone", "UTC")
        self.language = kwargs.get("language", "en")

        # Hash the password
        self.hashed_password = self._hash_password(password)

        # Generate API key
        self.api_key = self._generate_api_key()

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt with cost factor 12"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return bcrypt.checkpw(
            password.encode("utf-8"), self.hashed_password.encode("utf-8")
        )

    def _generate_api_key(self) -> str:
        """Generate secure API key"""
        return f"fs_{secrets.token_urlsafe(32)}"

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)
        self.failed_login_attempts = 0

    def increment_failed_login(self):
        """Increment failed login attempts"""
        self.failed_login_attempts += 1

    def is_locked(self) -> bool:
        """Check if account is locked due to failed login attempts"""
        return self.failed_login_attempts >= 5

    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role"""
        return any(role.name == role_name for role in self.roles)

    def get_permissions(self) -> List[str]:
        """Get all permissions from user roles"""
        permissions = set()
        for role in self.roles:
            permissions.update(role.permissions)
        return list(permissions)

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    def __repr__(self):
        return f"<UnifiedUnifiedUser(id={self.id}, email={self.email}, username={self.username})>"


class Role(Base):
    """Role model for role-based access control"""

    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    permissions: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # JSON string

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    users: Mapped[List["UnifiedUser"]] = relationship(
        "UnifiedUser", secondary=user_roles, back_populates="roles"
    )

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class UnifiedUserAccount(Base):
    """UnifiedUser account association for marketplace accounts"""

    __tablename__ = "user_accounts"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("unified_users.id"))
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[AccountType] = mapped_column(String(50), nullable=False)
    account_status: Mapped[AccountStatus] = mapped_column(
        String(50), default=AccountStatus.ACTIVE
    )

    # Account-specific data
    marketplace_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    external_account_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    credentials: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Encrypted JSON

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    user: Mapped["UnifiedUser"] = relationship("UnifiedUser", back_populates="accounts")

    def __repr__(self):
        return f"<UnifiedUserAccount(id={self.id}, user_id={self.user_id}, account_name={self.account_name})>"


class UnifiedUserSession(Base):
    """UnifiedUser session tracking"""

    __tablename__ = "user_sessions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(255), ForeignKey("unified_users.id"))
    session_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["UnifiedUser"] = relationship("UnifiedUser", back_populates="sessions")

    def is_expired(self) -> bool:
        """Check if session is expired"""
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self):
        return f"<UnifiedUserSession(id={self.id}, user_id={self.user_id}, is_active={self.is_active})>"


# Pydantic models for API responses
class UnifiedUserResponse(BaseModel):
    """API response model for user data"""

    id: str
    email: str
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    status: UnifiedUserStatus
    is_active: bool
    is_verified: bool
    is_admin: bool
    mfa_enabled: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UnifiedUserCreate(BaseModel):
    """Model for creating a new user"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field("UTC", max_length=50)
    language: Optional[str] = Field("en", max_length=10)


class UnifiedUserUpdate(BaseModel):
    """Model for updating a user"""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    preferences: Optional[Dict[str, Any]] = None


class LoginRequest(BaseModel):
    """API request model for user login"""

    email: EmailStr
    password: str
    remember_me: bool = False


class LoginResponse(BaseModel):
    """API response model for user login"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None
    user: UnifiedUserResponse


class RegistrationRequest(BaseModel):
    """API request model for user registration"""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class RegistrationResponse(BaseModel):
    """API response model for user registration"""

    message: str
    user: UnifiedUserResponse
    access_token: Optional[str] = None


class VerificationRequest(BaseModel):
    """API request model for user verification"""

    token: str
    email: Optional[EmailStr] = None


class VerificationResponse(BaseModel):
    """API response model for user verification"""

    message: str
    success: bool


# Backward compatibility aliases
UserRole = UnifiedUserRole
UserStatus = UnifiedUserStatus
User = UnifiedUser
UserAccount = UnifiedUserAccount
UserSession = UnifiedUserSession
UserResponse = UnifiedUserResponse
UserCreate = UnifiedUserCreate
UserUpdate = UnifiedUserUpdate

# Export all models
__all__ = [
    # Enums
    "UnifiedUserRole",
    "UnifiedUserStatus",
    "UserRole",
    "UserStatus",
    "AccountType",
    "AccountStatus",
    "MfaType",
    # SQLAlchemy Models
    "UnifiedUser",
    "UnifiedUserAccount",
    "UnifiedUserSession",
    "User",  # Alias
    "Role",
    "UserAccount",
    "UserSession",
    # Pydantic Models
    "UnifiedUserResponse",
    "UnifiedUserCreate",
    "UnifiedUserUpdate",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "LoginRequest",
    "LoginResponse",
    "RegistrationRequest",
    "RegistrationResponse",
    "VerificationRequest",
    "VerificationResponse",
]
