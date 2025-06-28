"""Notification models for monitoring.

This module provides model classes for the notification system.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

from fs_agt_clean.core.monitoring.notifications.config import AlertSeverity


class Alert(BaseModel):
    """Alert model for notifications."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Alert ID")
    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    severity: AlertSeverity = Field(..., description="Alert severity")
    component: str = Field(..., description="Component that triggered the alert")
    source: str = Field("system", description="Source of the alert")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Alert timestamp",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("title", "message", "component")
    def validate_non_empty(cls, v):
        """Validate string fields are not empty."""
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v


class Notification(BaseModel):
    """Notification model."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Notification ID"
    )
    alert: Alert = Field(..., description="Alert that triggered the notification")
    recipients: List[str] = Field(
        default_factory=list, description="Notification recipients"
    )
    sent_at: Optional[datetime] = Field(
        None, description="When the notification was sent"
    )
    status: str = Field("pending", description="Notification status")
    delivery_attempts: int = Field(0, description="Number of delivery attempts")
    max_attempts: int = Field(3, description="Maximum number of delivery attempts")

    def mark_as_sent(self):
        """Mark the notification as sent."""
        self.sent_at = datetime.now(timezone.utc)
        self.status = "sent"

    def mark_as_failed(self):
        """Mark the notification as failed."""
        self.delivery_attempts += 1
        if self.delivery_attempts >= self.max_attempts:
            self.status = "failed"
        else:
            self.status = "retry"
