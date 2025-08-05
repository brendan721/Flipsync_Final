"""
Database Model Enums

This module provides enums used by database models.
"""

from enum import Enum


class AccountStatus(Enum):
    """Account status enumeration."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class AccountType(Enum):
    """Account type enumeration."""

    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    TRIAL = "trial"


class SyncStatus(Enum):
    """Sync status enumeration."""

    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"
    IN_PROGRESS = "in_progress"


class UnifiedUserRole(Enum):
    """UnifiedUser role enumeration."""

    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPER_ADMIN = "super_admin"


class NotificationStatus(Enum):
    """Notification status enumeration."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    READ = "read"


class NotificationType(Enum):
    """Notification type enumeration."""

    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"
    IN_APP = "in_app"


class Priority(Enum):
    """Priority enumeration."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
