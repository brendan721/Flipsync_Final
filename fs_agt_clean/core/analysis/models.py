"""
Data models for market analysis.

This module defines the data structures used for market analysis, including
trend data, competitor information, and demand forecasts.
"""

from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class TrendDirection(str, Enum):
    """Direction of a market trend."""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class CompetitorRank(str, Enum):
    """Ranking of a competitor's market position."""

    LEADER = "leader"
    CHALLENGER = "challenger"
    FOLLOWER = "follower"
    NICHE = "niche"


class MarketSegment(str, Enum):
    """Market segment categories."""

    BUDGET = "budget"
    MID_RANGE = "mid_range"
    PREMIUM = "premium"
    LUXURY = "luxury"


class PricePoint(BaseModel):
    """Price point data with timestamp."""

    price: float
    timestamp: datetime
    source: str
    currency: str = "USD"

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class MarketTrend(BaseModel):
    """Market trend data for a specific metric."""

    metric: str
    direction: TrendDirection
    magnitude: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    timeframe_days: int
    data_points: List[float]
    timestamps: List[datetime]
    description: Optional[str] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class CompetitorData(BaseModel):
    """Data about a competitor in the market."""

    competitor_id: str
    name: str
    market_share: float = Field(ge=0.0, le=1.0)
    rank: CompetitorRank
    price_history: List[PricePoint]
    average_price: float
    min_price: float
    max_price: float
    product_count: int
    rating: Optional[float] = None
    review_count: Optional[int] = None
    segments: List[MarketSegment]
    last_updated: datetime

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class DemandForecast(BaseModel):
    """Demand forecast for a product or category."""

    product_id: Optional[str] = None
    category_id: Optional[str] = None
    timeframe_days: int
    forecast_values: List[float]
    forecast_dates: List[datetime]
    confidence_intervals: Optional[List[Dict[str, float]]] = None
    seasonality_factors: Optional[Dict[str, float]] = None
    total_forecast: float
    growth_rate: float
    forecast_accuracy: float = Field(ge=0.0, le=1.0)
    factors: Dict[str, float] = Field(default_factory=dict)
    last_updated: datetime

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }


class MarketMetrics(BaseModel):
    """Comprehensive market metrics for a category."""

    category_id: str
    total_listings: int
    active_listings: int
    average_price: float
    price_range: Dict[str, float]
    sales_velocity: float
    market_size: float
    growth_rate: float
    top_competitors: List[CompetitorData]
    trends: List[MarketTrend]
    demand_forecast: Optional[DemandForecast] = None
    market_segments: Dict[MarketSegment, float]
    opportunity_score: float = Field(ge=0.0, le=1.0)
    competition_level: float = Field(ge=0.0, le=1.0)
    price_elasticity: Optional[float] = None
    seasonality_index: Optional[float] = None
    last_updated: datetime

    class Config:
        """Pydantic configuration."""

        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
        }
