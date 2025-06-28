"""
Authentication User Models for FlipSync Database
AGENT_CONTEXT: Complete user authentication system with SQLAlchemy models
AGENT_PRIORITY: Database models for user management, roles, and permissions
AGENT_PATTERN: SQLAlchemy async models with proper relationships
"""

import secrets
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import bcrypt
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .base import Base

# AGENT_INSTRUCTION: Association tables for many-to-many relationships
user_roles_table = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(255), ForeignKey("auth_users.id"), primary_key=True),
    Column("role_id", String(255), ForeignKey("roles.id"), primary_key=True),
    extend_existing=True,
)

user_permissions_table = Table(
    "user_permissions",
    Base.metadata,
    Column("user_id", String(255), ForeignKey("auth_users.id"), primary_key=True),
    Column(
        "permission_id", String(255), ForeignKey("permissions.id"), primary_key=True
    ),
    extend_existing=True,
)

role_permissions_table = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", String(255), ForeignKey("roles.id"), primary_key=True),
    Column(
        "permission_id", String(255), ForeignKey("permissions.id"), primary_key=True
    ),
    extend_existing=True,
)


class AuthUser(Base):
    """
    AGENT_CONTEXT: Main user model for authentication and authorization
    AGENT_CAPABILITY: Password hashing, verification, role management
    AGENT_SECURITY: Bcrypt password hashing, secure token generation
    """

    __tablename__ = "auth_users"
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

    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Security tracking
    failed_login_attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Email verification
    email_verification_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    email_verification_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Password reset
    password_reset_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    password_reset_expires: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=user_roles_table, back_populates="users", lazy="selectin"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=user_permissions_table,
        back_populates="users",
        lazy="selectin",
    )

    def __init__(self, email: str, username: str, password: str, **kwargs):
        """
        Initialize user with hashed password
        AGENT_SECURITY: Automatically hash password on creation
        """
        super().__init__()
        self.email = email
        self.username = username
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.is_active = kwargs.get("is_active", True)
        self.is_verified = kwargs.get("is_verified", False)
        self.is_admin = kwargs.get("is_admin", False)

        # Hash the password
        self.hashed_password = self._hash_password(password)

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt with cost factor 12"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), self.hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    def set_password(self, password: str) -> None:
        """Set new password (hashed)"""
        self.hashed_password = self._hash_password(password)
        self.updated_at = datetime.now(timezone.utc)

    def generate_verification_token(self) -> str:
        """Generate email verification token"""
        token = secrets.token_urlsafe(32)
        self.email_verification_token = token
        self.email_verification_expires = datetime.now(timezone.utc).replace(
            hour=23, minute=59, second=59, microsecond=999999
        )  # Expires at end of day
        return token

    def generate_password_reset_token(self) -> str:
        """Generate password reset token"""
        token = secrets.token_urlsafe(32)
        self.password_reset_token = token
        # Token expires in 1 hour
        self.password_reset_expires = datetime.now(timezone.utc).replace(
            minute=datetime.now(timezone.utc).minute + 60
        )
        return token

    def is_verification_token_valid(self, token: str) -> bool:
        """Check if verification token is valid"""
        if not self.email_verification_token or not self.email_verification_expires:
            return False

        return (
            self.email_verification_token == token
            and datetime.now(timezone.utc) < self.email_verification_expires
        )

    def is_password_reset_token_valid(self, token: str) -> bool:
        """Check if password reset token is valid"""
        if not self.password_reset_token or not self.password_reset_expires:
            return False

        return (
            self.password_reset_token == token
            and datetime.now(timezone.utc) < self.password_reset_expires
        )

    def verify_email(self) -> None:
        """Mark email as verified"""
        self.is_verified = True
        self.email_verification_token = None
        self.email_verification_expires = None
        self.updated_at = datetime.now(timezone.utc)

    def update_login_success(self) -> None:
        """Update fields after successful login"""
        self.last_login = datetime.now(timezone.utc)
        self.failed_login_attempts = 0
        self.updated_at = datetime.now(timezone.utc)

    def update_login_failure(self) -> None:
        """Update fields after failed login"""
        self.failed_login_attempts += 1
        self.updated_at = datetime.now(timezone.utc)

    def is_locked(self) -> bool:
        """Check if account is locked due to failed attempts"""
        return self.failed_login_attempts >= 5

    def __repr__(self) -> str:
        return f"<AuthUser(id='{self.id}', email='{self.email}', username='{self.username}')>"


class Role(Base):
    """
    AGENT_CONTEXT: Role model for role-based access control
    AGENT_CAPABILITY: Hierarchical role management with permissions
    """

    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    users: Mapped[List["AuthUser"]] = relationship(
        "AuthUser", secondary=user_roles_table, back_populates="roles"
    )
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary=role_permissions_table, back_populates="roles"
    )

    def __repr__(self) -> str:
        return f"<Role(id='{self.id}', name='{self.name}')>"


class Permission(Base):
    """
    AGENT_CONTEXT: Permission model for granular access control
    AGENT_CAPABILITY: Fine-grained permission management
    """

    __tablename__ = "permissions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )  # e.g., 'products', 'users'
    action: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )  # e.g., 'read', 'write', 'delete'

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
    users: Mapped[List["AuthUser"]] = relationship(
        "AuthUser", secondary=user_permissions_table, back_populates="permissions"
    )
    roles: Mapped[List["Role"]] = relationship(
        "Role", secondary=role_permissions_table, back_populates="permissions"
    )

    def __repr__(self) -> str:
        return f"<Permission(id='{self.id}', name='{self.name}')>"


# AGENT_INSTRUCTION: Compatibility classes for the repository
class UserRole:
    """Compatibility class for user-role relationships"""

    def __init__(self, user_id: str, role_id: str):
        self.user_id = user_id
        self.role_id = role_id


class UserPermission:
    """Compatibility class for user-permission relationships"""

    def __init__(self, user_id: str, permission_id: str):
        self.user_id = user_id
        self.permission_id = permission_id


class RolePermission:
    """Compatibility class for role-permission relationships"""

    def __init__(self, role_id: str, permission_id: str):
        self.role_id = role_id
        self.permission_id = permission_id
