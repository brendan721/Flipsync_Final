"""
eBay OAuth Token Storage Models for FlipSync.

This module provides database models for storing and managing eBay OAuth tokens
with proper encryption and security measures.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from fs_agt_clean.database.models.base import Base


class EbayOAuthToken(Base):
    """
    Database model for storing eBay OAuth tokens.
    
    This model stores encrypted OAuth tokens for eBay API access,
    including access tokens, refresh tokens, and metadata.
    """
    
    __tablename__ = "ebay_oauth_tokens"
    __table_args__ = {"extend_existing": True}
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    # User association
    user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    
    # OAuth tokens (encrypted)
    access_token: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    refresh_token: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Token metadata
    token_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="Bearer"
    )
    expires_in: Mapped[Optional[int]] = mapped_column(
        nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # OAuth flow metadata
    scope: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    
    # eBay-specific metadata
    ebay_user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    marketplace_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    
    # Status tracking
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
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
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) >= self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the token is valid and usable."""
        return (
            self.is_active 
            and not self.is_revoked 
            and not self.is_expired()
            and self.access_token
        )
    
    def mark_used(self) -> None:
        """Mark the token as recently used."""
        self.last_used_at = datetime.now(timezone.utc)
    
    def revoke(self) -> None:
        """Revoke the token."""
        self.is_revoked = True
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)


class EbayOAuthState(Base):
    """
    Database model for storing OAuth state parameters for CSRF protection.
    
    This model stores temporary state parameters used during the OAuth flow
    to prevent CSRF attacks.
    """
    
    __tablename__ = "ebay_oauth_states"
    __table_args__ = {"extend_existing": True}
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(255), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    
    # State parameter
    state: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    
    # User association (optional, for logged-in users)
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True
    )
    
    # Session metadata
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )
    
    # Status
    is_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    
    def is_expired(self) -> bool:
        """Check if the state is expired."""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the state is valid and usable."""
        return not self.is_used and not self.is_expired()
    
    def mark_used(self) -> None:
        """Mark the state as used."""
        self.is_used = True


# Export models
__all__ = [
    "EbayOAuthToken",
    "EbayOAuthState",
]
