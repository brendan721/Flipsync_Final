from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ASINSource(str, Enum):
    """Source of ASIN data."""

    AMAZON = "amazon"
    EBAY = "ebay"
    MANUAL = "manual"
    EXTERNAL = "external"


class ASINStatus(str, Enum):
    """Status of ASIN synchronization."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ASINPriority(int, Enum):
    """Priority levels for ASIN synchronization."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


class ASINSyncRequest(BaseModel):
    """Request model for ASIN synchronization."""

    asins: List[str] = Field(..., min_items=1, max_items=100)
    force: bool = False
    priority: ASINPriority = ASINPriority.NORMAL
    source: ASINSource = ASINSource.AMAZON


class ASINRejection(BaseModel):
    """Model for rejected ASINs."""

    asin: str
    reason: str


class ASINSyncResponse(BaseModel):
    """Response model for ASIN synchronization request."""

    request_id: str
    accepted_asins: List[str]
    rejected_asins: List[ASINRejection]
    estimated_completion: datetime


class ASINSyncStatus(BaseModel):
    """Status model for ASIN synchronization."""

    asin: str
    status: ASINStatus
    progress: float = Field(0.0, ge=0.0, le=1.0)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    source: ASINSource


class ASINPricing(BaseModel):
    """Pricing information for an ASIN."""

    current_price: float
    list_price: Optional[float] = None
    currency: str = "USD"
    last_updated: datetime


class ASINInventory(BaseModel):
    """Inventory information for an ASIN."""

    quantity: int
    condition: str = "New"
    fulfillment_type: str
    last_updated: datetime


class ASINCompetition(BaseModel):
    """Competition information for an ASIN."""

    total_sellers: int
    lowest_price: float
    highest_price: float
    average_price: float
    buy_box_price: Optional[float] = None
    currency: str = "USD"
    last_updated: datetime


class ASINMetrics(BaseModel):
    """Performance metrics for an ASIN."""

    sales_rank: Optional[int] = None
    category: Optional[str] = None
    reviews_count: int = 0
    average_rating: Optional[float] = None
    last_updated: datetime


class ASINData(BaseModel):
    """Complete data model for an ASIN."""

    asin: str
    title: str
    brand: Optional[str] = None
    category: str
    description: Optional[str] = None
    features: List[str] = []
    images: List[str] = []
    pricing: ASINPricing
    inventory: ASINInventory
    competition: ASINCompetition
    metrics: ASINMetrics
    source: ASINSource
    last_synced: datetime
    metadata: Dict[str, str] = {}
