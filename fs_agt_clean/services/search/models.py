"""Search service data models."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class SearchFilter(BaseModel):
    """Search filter parameters."""

    field: str
    operator: str
    value: Union[str, int, float, bool, List[Any]]


class SearchSort(BaseModel):
    """Search sort parameters."""

    field: str
    order: str = "desc"


class SearchResult(BaseModel):
    """Search result model."""

    id: str
    score: float
    document: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


class SearchResponse(BaseModel):
    """Search response model."""

    results: List[SearchResult]
    total: int
    page: int
    page_size: int
    took_ms: float
    facets: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
