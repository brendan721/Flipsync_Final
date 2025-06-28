"""
Notification models for the database.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import (
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from fs_agt_clean.database.models.unified_base import Base


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Status of a notification."""

    PENDING = "pending"
    DELIVERED = "delivered"
    READ = "read"
    ARCHIVED = "archived"
    FAILED = "failed"


class NotificationCategory(str, Enum):
    """Categories for notifications."""

    SYSTEM = "system"
    ORDER = "order"
    INVENTORY = "inventory"
    MARKETPLACE = "marketplace"
    SECURITY = "security"
    PAYMENT = "payment"
    SHIPPING = "shipping"
    ACCOUNT = "account"
    OTHER = "other"


class Notification(Base):
    """Notification model for tracking user notifications."""

    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("unified_users.id"), nullable=False)
    template_id = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(
        SQLAlchemyEnum(NotificationCategory), default=NotificationCategory.SYSTEM
    )
    priority = Column(
        SQLAlchemyEnum(NotificationPriority), default=NotificationPriority.MEDIUM
    )
    status = Column(
        SQLAlchemyEnum(NotificationStatus), default=NotificationStatus.PENDING
    )
    data = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=True)
    delivery_methods = Column(JSON, nullable=True)
    delivery_attempts = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("UnifiedUser", back_populates="notifications")

    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "title": self.title,
            "message": self.message,
            "category": self.category.value if self.category else None,
            "priority": self.priority.value if self.priority else None,
            "status": self.status.value if self.status else None,
            "data": self.data,
            "actions": self.actions,
            "delivery_methods": self.delivery_methods,
            "delivery_attempts": self.delivery_attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delivered_at": (
                self.delivered_at.isoformat() if self.delivered_at else None
            ),
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }

    def mark_delivered(self) -> None:
        """Mark the notification as delivered."""
        self.status = NotificationStatus.DELIVERED
        self.delivered_at = datetime.utcnow()

    def mark_read(self) -> None:
        """Mark the notification as read."""
        self.status = NotificationStatus.READ
        self.read_at = datetime.utcnow()

    def mark_archived(self) -> None:
        """Mark the notification as archived."""
        self.status = NotificationStatus.ARCHIVED

    def mark_failed(self) -> None:
        """Mark the notification as failed."""
        self.status = NotificationStatus.FAILED
