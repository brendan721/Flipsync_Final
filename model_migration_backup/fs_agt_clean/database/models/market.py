"""Market models for FlipSync."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# Re-export Account and UserAccount from account module
from fs_agt_clean.core.models.account import Account, UserAccount, UserRole


class MarketplaceType(str, Enum):
    """Marketplace type enum."""

    AMAZON = "amazon"
    EBAY = "ebay"
    ETSY = "etsy"
    WALMART = "walmart"
    SHOPIFY = "shopify"


class AccountStatus(str, Enum):
    """Account status enum."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    CLOSED = "closed"


class ListingStatus(str, Enum):
    """Listing status enum."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ENDED = "ended"
    DRAFT = "draft"


class PricingStrategy(str, Enum):
    """Pricing strategy enum."""

    FIXED = "fixed"
    COMPETITIVE = "competitive"
    COST_PLUS = "cost_plus"
    DYNAMIC = "dynamic"
    TIERED = "tiered"


class MarketplaceAccount(BaseModel):
    """Marketplace account model."""

    id: str
    user_id: str
    marketplace: str
    credentials: Dict[str, Any] = Field(default_factory=dict)
    status: AccountStatus = AccountStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class MarketplaceProduct(BaseModel):
    """Marketplace product model."""

    id: str
    marketplace_account_id: str
    external_id: str
    title: str
    description: str
    price: float
    currency: str = "USD"
    inventory: int = 0
    category: str
    images: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class PricingStrategyRequest(BaseModel):
    """Pricing strategy request model."""

    id: str
    user_id: str
    marketplace_account_id: str
    product_id: str
    strategy_type: PricingStrategy
    parameters: Dict[str, Any] = Field(default_factory=dict)
    target_margin: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    competitor_tracking: bool = False
    requested_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class PricingStrategyResponse(BaseModel):
    """Pricing strategy response model."""

    request_id: str
    recommended_price: float
    currency: str = "USD"
    margin: Optional[float] = None
    competitor_prices: Optional[List[float]] = None
    price_history: Optional[List[Dict[str, Any]]] = None
    reasoning: Optional[str] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class ListingRequest(BaseModel):
    """Listing request model."""

    id: str
    user_id: str
    marketplace_account_id: str
    product_data: Dict[str, Any]
    listing_options: Dict[str, Any] = Field(default_factory=dict)
    requested_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class ListingResponse(BaseModel):
    """Listing response model."""

    request_id: str
    listing_id: Optional[str] = None
    external_id: Optional[str] = None
    status: ListingStatus = ListingStatus.PENDING
    url: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class InventorySyncRequest(BaseModel):
    """Inventory sync request model."""

    id: str
    user_id: str
    marketplace_account_id: str
    product_ids: List[str] = Field(default_factory=list)
    sync_all: bool = False
    requested_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class InventorySyncResponse(BaseModel):
    """Inventory sync response model."""

    request_id: str
    synced_products: List[str] = Field(default_factory=list)
    failed_products: Dict[str, str] = Field(
        default_factory=dict
    )  # product_id -> error message
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class CompetitorAnalysisRequest(BaseModel):
    """Competitor analysis request model."""

    id: str
    user_id: str
    marketplace: str
    product_id: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None
    requested_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class CompetitorProduct(BaseModel):
    """Competitor product model."""

    external_id: str
    title: str
    price: float
    currency: str = "USD"
    rating: Optional[float] = None
    review_count: Optional[int] = None
    url: Optional[str] = None
    image_url: Optional[str] = None
    seller: Optional[str] = None

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class PricePoint(BaseModel):
    """Price point model."""

    price: float
    currency: str = "USD"
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class PriceHistory(BaseModel):
    """Price history model."""

    product_id: str
    marketplace: str
    prices: List[PricePoint] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class CompetitorAnalysisResponse(BaseModel):
    """Competitor analysis response model."""

    request_id: str
    products: List[CompetitorProduct] = Field(default_factory=list)
    average_price: Optional[float] = None
    price_range: Optional[Dict[str, float]] = None
    top_keywords: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class MarketTrend(BaseModel):
    """Market trend model."""

    category: str
    marketplace: str
    trend_type: str  # e.g., "price", "demand", "competition"
    direction: str  # e.g., "up", "down", "stable"
    magnitude: float  # 0-1 scale
    confidence: float  # 0-1 scale
    time_period: str  # e.g., "daily", "weekly", "monthly"
    data_points: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class MarketInsight(BaseModel):
    """Market insight model."""

    id: str
    category: str
    marketplace: str
    insight_type: str  # e.g., "opportunity", "risk", "trend"
    title: str
    description: str
    confidence: float  # 0-1 scale
    impact: float  # 0-1 scale
    supporting_data: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class MarketplaceMetrics(BaseModel):
    """Marketplace metrics model."""

    marketplace_account_id: str
    period: str  # e.g., "daily", "weekly", "monthly"
    start_date: datetime
    end_date: datetime
    sales: float = 0.0
    revenue: float = 0.0
    currency: str = "USD"
    order_count: int = 0
    average_order_value: Optional[float] = None
    return_rate: Optional[float] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class ProductTransformationRequest(BaseModel):
    """Product transformation request model."""

    id: str
    user_id: str
    source_marketplace: str
    source_product_id: str
    target_marketplace: str
    transformation_options: Dict[str, Any] = Field(default_factory=dict)
    requested_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True


class ProductTransformationResponse(BaseModel):
    """Product transformation response model."""

    request_id: str
    transformed_product: MarketplaceProduct
    recommendations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    completed_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
