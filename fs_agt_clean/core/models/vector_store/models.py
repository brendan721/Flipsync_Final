"""Vector store models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class ProductMetadata:
    """Product metadata model."""

    def __init__(
        self,
        product_id: str,
        title: str,
        description: str,
        price: float,
        category: str,
        source: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize product metadata."""
        self.product_id = product_id
        self.title = title
        self.description = description
        self.price = price
        self.category = category
        self.source = source
        self.timestamp = timestamp
        self.additional_data = kwargs

    def to_dict(self) -> Dict[str, Union[str, float, datetime]]:
        """Convert to dictionary."""
        return {
            "product_id": self.product_id,
            "title": self.title,
            "description": self.description,
            "price": self.price,
            "category": self.category,
            "source": self.source,
            "timestamp": self.timestamp,
            **self.additional_data,
        }


class SearchQuery:
    """Search query model."""

    def __init__(
        self,
        vector: List[float],
        filters: Optional[Dict[str, str]] = None,
        limit: int = 10,
    ):
        """Initialize search query."""
        self.vector = vector
        self.filters = filters or {}
        self.limit = limit


class SearchResult:
    """Search result model."""

    def __init__(
        self, id: str, score: float, metadata: Dict[str, Union[str, float, datetime]]
    ):
        """Initialize search result."""
        self.id = id
        self.score = score
        self.metadata = metadata
