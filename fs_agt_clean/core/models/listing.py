"""
Listing models for marketplace integrations.

This module contains data models for marketplace listings.
"""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ListingStatus(str, Enum):
    """Enumeration of listing statuses."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SOLD = "sold"
    ENDED = "ended"
    DRAFT = "draft"


class Listing(BaseModel):
    """Base listing model."""

    id: Optional[str] = None
    title: str
    description: str
    price: float
    currency: str = "USD"
    status: ListingStatus = ListingStatus.DRAFT
    marketplace: str
    marketplace_id: Optional[str] = None
    sku: Optional[str] = None
    quantity: int = 1
    category: Optional[str] = None
    images: list[str] = []
    metadata: Dict[str, Any] = {}


__all__ = ["ListingStatus", "Listing"]
