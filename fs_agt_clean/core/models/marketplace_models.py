"""
Marketplace Models for FlipSync Market UnifiedAgent
===========================================

This module defines data models for marketplace operations including
product data, pricing information, inventory status, and competitor analysis.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class MarketplaceType(str, Enum):
    """Supported marketplace types."""

    AMAZON = "amazon"
    EBAY = "ebay"
    WALMART = "walmart"
    ETSY = "etsy"
    SHOPIFY = "shopify"


class ProductCondition(str, Enum):
    """Product condition types."""

    NEW = "new"
    USED_LIKE_NEW = "used_like_new"
    USED_EXCELLENT = "used_excellent"
    USED_VERY_GOOD = "used_very_good"
    USED_GOOD = "used_good"
    USED_ACCEPTABLE = "used_acceptable"
    USED_FAIR = "used_fair"
    COLLECTIBLE = "collectible"
    REFURBISHED = "refurbished"
    FOR_PARTS = "for_parts"


class ListingStatus(str, Enum):
    """Listing status types."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"
    OUT_OF_STOCK = "out_of_stock"
    ENDED = "ended"


class PriceChangeDirection(str, Enum):
    """Price change direction."""

    INCREASE = "increase"
    DECREASE = "decrease"
    MAINTAIN = "maintain"


@dataclass
class ProductIdentifier:
    """Product identification across marketplaces."""

    asin: Optional[str] = None  # Amazon Standard Identification Number
    sku: Optional[str] = None  # Stock Keeping Unit
    upc: Optional[str] = None  # Universal Product Code
    ean: Optional[str] = None  # European Article Number
    isbn: Optional[str] = None  # International Standard Book Number
    mpn: Optional[str] = None  # Manufacturer Part Number
    ebay_item_id: Optional[str] = None
    internal_id: Optional[str] = None


@dataclass
class Price:
    """Price information with currency and marketplace context."""

    amount: Decimal
    currency: str = "USD"
    marketplace: MarketplaceType = MarketplaceType.AMAZON
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    includes_shipping: bool = False
    includes_tax: bool = False

    def __post_init__(self):
        """Ensure amount is a Decimal."""
        if not isinstance(self.amount, Decimal):
            self.amount = Decimal(str(self.amount))


@dataclass
class ProductListing:
    """Complete product listing information."""

    identifier: ProductIdentifier
    title: str
    description: str
    marketplace: MarketplaceType
    seller_id: str
    condition: ProductCondition
    status: ListingStatus
    current_price: Price
    original_price: Optional[Price] = None
    quantity_available: Optional[int] = None
    images: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    shipping_info: Dict[str, Any] = field(default_factory=dict)
    seller_rating: Optional[float] = None
    review_count: Optional[int] = None
    average_rating: Optional[float] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    listing_url: Optional[str] = None


@dataclass
class CompetitorListing:
    """Competitor listing information for analysis."""

    listing: ProductListing
    market_share: Optional[float] = None
    sales_velocity: Optional[int] = None  # estimated sales per day
    listing_age: Optional[int] = None  # days since listing created
    price_history: List[Price] = field(default_factory=list)
    competitive_advantages: List[str] = field(default_factory=list)
    competitive_disadvantages: List[str] = field(default_factory=list)


@dataclass
class InventoryStatus:
    """Inventory status across marketplaces."""

    product_id: ProductIdentifier
    marketplace: MarketplaceType
    quantity_available: int
    quantity_reserved: int = 0
    quantity_inbound: int = 0
    reorder_point: Optional[int] = None
    max_stock_level: Optional[int] = None
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    warehouse_locations: List[str] = field(default_factory=list)
    fulfillment_method: Optional[str] = None  # FBA, FBM, etc.


@dataclass
class PricingRecommendation:
    """Pricing recommendation from analysis."""

    product_id: ProductIdentifier
    current_price: Price
    recommended_price: Price
    price_change_direction: PriceChangeDirection
    confidence_score: float  # 0.0 to 1.0
    reasoning: str
    expected_impact: Dict[str, Any]  # sales, profit, ranking changes
    competitor_analysis: List[CompetitorListing] = field(default_factory=list)
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    recommendation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


@dataclass
class CompetitorAnalysis:
    """Comprehensive competitor analysis."""

    product_id: ProductIdentifier
    analysis_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    total_competitors: int = 0
    price_range: Dict[str, Decimal] = field(default_factory=dict)  # min, max, avg
    market_position: str = ""  # "leader", "follower", "niche"
    competitive_listings: List[CompetitorListing] = field(default_factory=list)
    market_insights: Dict[str, Any] = field(default_factory=dict)
    opportunities: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class ListingOptimization:
    """Listing optimization recommendations."""

    product_id: ProductIdentifier
    current_listing: ProductListing
    optimization_score: float  # 0.0 to 1.0
    title_suggestions: List[str] = field(default_factory=list)
    description_improvements: List[str] = field(default_factory=list)
    keyword_opportunities: List[str] = field(default_factory=list)
    image_recommendations: List[str] = field(default_factory=list)
    category_suggestions: List[str] = field(default_factory=list)
    pricing_recommendations: Optional[PricingRecommendation] = None
    estimated_impact: Dict[str, Any] = field(default_factory=dict)
    priority_actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DemandForecast:
    """Demand forecasting data."""

    product_id: ProductIdentifier
    forecast_period_days: int
    predicted_demand: int
    confidence_interval: Dict[str, int]  # low, high estimates
    seasonal_factors: Dict[str, float] = field(default_factory=dict)
    trend_direction: str = "stable"  # "increasing", "decreasing", "stable"
    historical_data_points: int = 0
    forecast_accuracy: Optional[float] = None  # if historical validation available
    factors_considered: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MarketMetrics:
    """Market performance metrics."""

    marketplace: MarketplaceType
    product_id: ProductIdentifier
    sales_rank: Optional[int] = None
    category_rank: Optional[int] = None
    buy_box_percentage: Optional[float] = None
    conversion_rate: Optional[float] = None
    click_through_rate: Optional[float] = None
    impression_count: Optional[int] = None
    session_count: Optional[int] = None
    units_sold: Optional[int] = None
    revenue: Optional[Decimal] = None
    profit_margin: Optional[float] = None
    return_rate: Optional[float] = None
    customer_satisfaction: Optional[float] = None
    date_range_start: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    date_range_end: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class MarketAlert:
    """Market condition alerts."""

    product_id: ProductIdentifier
    alert_type: str = ""  # "price_change", "stock_out", "new_competitor", etc.
    severity: str = "medium"  # "low", "medium", "high", "critical"
    title: str = ""
    message: str = ""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: Dict[str, Any] = field(default_factory=dict)
    action_required: bool = False
    suggested_actions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


@dataclass
class MarketDecision:
    """Market agent decision record."""

    product_id: ProductIdentifier
    decision_type: str = ""  # "pricing", "inventory", "listing_optimization"
    recommended_action: str = ""
    reasoning: str = ""
    confidence_score: float = 0.0
    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    current_state: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: Dict[str, Any] = field(default_factory=dict)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = True
    auto_execute: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    approved_by: Optional[str] = None


# Utility functions for model operations


def create_product_identifier(**kwargs) -> ProductIdentifier:
    """Create a product identifier with provided values."""
    return ProductIdentifier(**kwargs)


def create_price(amount: Union[str, float, Decimal], **kwargs) -> Price:
    """Create a price object with proper decimal conversion."""
    return Price(amount=Decimal(str(amount)), **kwargs)


def calculate_price_change_percentage(old_price: Price, new_price: Price) -> float:
    """Calculate percentage change between two prices."""
    if old_price.amount == 0:
        return 0.0
    return float((new_price.amount - old_price.amount) / old_price.amount * 100)


def is_competitive_price(
    target_price: Price, competitor_prices: List[Price], margin: float = 0.05
) -> bool:
    """Check if a price is competitive within a margin."""
    if not competitor_prices:
        return True

    min_competitor_price = min(p.amount for p in competitor_prices)
    max_acceptable_price = min_competitor_price * (1 + margin)

    return target_price.amount <= max_acceptable_price


def get_price_position(target_price: Price, competitor_prices: List[Price]) -> str:
    """Get price position relative to competitors."""
    if not competitor_prices:
        return "unknown"

    competitor_amounts = [p.amount for p in competitor_prices]
    min_price = min(competitor_amounts)
    max_price = max(competitor_amounts)
    avg_price = sum(competitor_amounts) / len(competitor_amounts)

    if target_price.amount <= min_price:
        return "lowest"
    elif target_price.amount >= max_price:
        return "highest"
    elif target_price.amount <= avg_price:
        return "below_average"
    else:
        return "above_average"
