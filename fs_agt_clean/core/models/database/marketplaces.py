"""Database model for marketplaces."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from .base import Base


class MarketplaceModel(Base):
    """Database model for marketplaces."""

    __tablename__ = "marketplaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="active")
    config = Column(JSONB, nullable=False, default={})
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "",
        description: Optional[str] = None,
        type: str = "",
        status: str = "active",
        config: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize a marketplace model.

        Args:
            id: Marketplace ID (defaults to a new UUID)
            name: Marketplace name
            description: Marketplace description
            type: Marketplace type
            status: Marketplace status
            config: Marketplace configuration
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.type = type
        self.status = status
        self.config = config or {}
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
            "status": self.status,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class MarketplaceConnectionModel(Base):
    """Database model for marketplace connections (OAuth tokens and connection status)."""

    __tablename__ = "marketplace_connections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    marketplace_type = Column(String(50), nullable=False)  # 'ebay', 'amazon', etc.
    marketplace_id = Column(String(36), ForeignKey("marketplaces.id"), nullable=True)

    # OAuth token fields
    access_token = Column(Text, nullable=True)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime, nullable=True)

    # Connection status
    is_connected = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_sync_at = Column(DateTime, nullable=True)

    # eBay specific fields
    ebay_user_id = Column(String(255), nullable=True)
    ebay_username = Column(String(255), nullable=True)

    # Metadata
    connection_metadata = Column(JSONB, nullable=False, default={})
    error_message = Column(Text, nullable=True)

    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationship to marketplace
    marketplace = relationship("MarketplaceModel", backref="connections")

    def __init__(
        self,
        id: Optional[str] = None,
        user_id: str = "",
        marketplace_type: str = "",
        marketplace_id: Optional[str] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        token_expires_at: Optional[datetime] = None,
        is_connected: bool = False,
        is_active: bool = True,
        last_sync_at: Optional[datetime] = None,
        ebay_user_id: Optional[str] = None,
        ebay_username: Optional[str] = None,
        connection_metadata: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize a marketplace connection model.

        Args:
            id: Connection ID (defaults to a new UUID)
            user_id: User ID who owns this connection
            marketplace_type: Type of marketplace ('ebay', 'amazon', etc.)
            marketplace_id: Reference to marketplace record
            access_token: OAuth access token (encrypted)
            refresh_token: OAuth refresh token (encrypted)
            token_expires_at: When the access token expires
            is_connected: Whether the connection is active
            is_active: Whether the connection is enabled
            last_sync_at: Last successful sync timestamp
            ebay_user_id: eBay user ID
            ebay_username: eBay username
            connection_metadata: Additional connection metadata
            error_message: Last error message if any
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.marketplace_type = marketplace_type
        self.marketplace_id = marketplace_id
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expires_at = token_expires_at
        self.is_connected = is_connected
        self.is_active = is_active
        self.last_sync_at = last_sync_at
        self.ebay_user_id = ebay_user_id
        self.ebay_username = ebay_username
        self.connection_metadata = connection_metadata or {}
        self.error_message = error_message
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "marketplace_type": self.marketplace_type,
            "marketplace_id": self.marketplace_id,
            "is_connected": self.is_connected,
            "is_active": self.is_active,
            "last_sync_at": (
                self.last_sync_at.isoformat() if self.last_sync_at else None
            ),
            "ebay_user_id": self.ebay_user_id,
            "ebay_username": self.ebay_username,
            "connection_metadata": self.connection_metadata,
            "error_message": self.error_message,
            "token_expires_at": (
                self.token_expires_at.isoformat() if self.token_expires_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def has_valid_tokens(self) -> bool:
        """Check if the connection has valid OAuth tokens.

        Returns:
            bool: True if tokens are valid and not expired
        """
        if not self.access_token:
            return False

        if self.token_expires_at and self.token_expires_at <= datetime.now(
            timezone.utc
        ):
            return False

        return True
