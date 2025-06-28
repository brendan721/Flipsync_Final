"""API models for marketplace operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MarketplaceBase(BaseModel):
    """Base model for marketplace operations."""

    name: str = Field(description="Name of the marketplace")
    description: Optional[str] = Field(
        None, description="Description of the marketplace"
    )
    type: str = Field(description="Type of the marketplace")
    status: Optional[str] = Field("active", description="Status of the marketplace")
    config: Optional[Dict[str, Any]] = Field(
        {}, description="Configuration of the marketplace"
    )


class MarketplaceCreate(MarketplaceBase):
    """Model for creating a marketplace."""

    pass


class MarketplaceUpdate(BaseModel):
    """Model for updating a marketplace."""

    name: Optional[str] = Field(None, description="Name of the marketplace")
    description: Optional[str] = Field(
        None, description="Description of the marketplace"
    )
    type: Optional[str] = Field(None, description="Type of the marketplace")
    status: Optional[str] = Field(None, description="Status of the marketplace")
    config: Optional[Dict[str, Any]] = Field(
        None, description="Configuration of the marketplace"
    )


class MarketplaceResponse(MarketplaceBase):
    """Model for marketplace response."""

    id: str = Field(description="Marketplace ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        orm_mode = True
