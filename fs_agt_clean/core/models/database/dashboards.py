"""Database model for dashboards."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from fs_agt_clean.database.models.unified_base import Base


class DashboardModel(Base):
    """Database model for dashboards."""

    __tablename__ = "dashboards"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False, default="standard")
    user_id = Column(
        String(255), ForeignKey("unified_users.id"), nullable=True
    )  # Fixed: String to match UnifiedUser.id type
    config = Column(JSON, nullable=False, default={})
    is_public = Column(Boolean, default=False)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationship back to UnifiedUser model
    user = relationship("UnifiedUser", back_populates="dashboards")

    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "",
        description: Optional[str] = None,
        type: str = "standard",
        user_id: Optional[str] = None,  # Fixed: Changed to str to match UnifiedUser.id
        config: Optional[Dict[str, Any]] = None,
        is_public: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize a dashboard model.

        Args:
            id: Dashboard ID (defaults to a new UUID)
            name: Dashboard name
            description: Dashboard description
            type: Dashboard type
            user_id: UnifiedUser ID (integer) who owns the dashboard
            config: Dashboard configuration
            is_public: Whether the dashboard is public
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.type = type
        self.user_id = user_id
        self.config = config or {}
        self.is_public = is_public
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "user_id": self.user_id,
            "config": self.config,
            "is_public": self.is_public,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardModel":
        """Create dashboard model from dictionary.

        Args:
            data: Dictionary data

        Returns:
            DashboardModel: Dashboard model instance
        """
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            description=data.get("description"),
            type=data.get("type", "standard"),
            user_id=data.get("user_id"),
            config=data.get("config", {}),
            is_public=data.get("is_public", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def update_from_dict(self, data: Dict[str, Any]) -> None:
        """Update dashboard model from dictionary.

        Args:
            data: Dictionary data to update from
        """
        if "name" in data:
            self.name = data["name"]
        if "description" in data:
            self.description = data["description"]
        if "type" in data:
            self.type = data["type"]
        if "user_id" in data:
            self.user_id = data["user_id"]
        if "config" in data:
            self.config = data["config"]
        if "is_public" in data:
            self.is_public = data["is_public"]

        # Always update the timestamp
        self.updated_at = datetime.now(timezone.utc)
