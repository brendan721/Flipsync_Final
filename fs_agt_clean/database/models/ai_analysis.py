"""
Database models for AI analysis results and related data.

This module contains SQLAlchemy models for:
- AI analysis results
- UnifiedAgent coordination logs
- Revenue calculations
- Category optimization results
- UnifiedUser rewards balance
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from fs_agt_clean.database.models.unified_base import Base


class AIAnalysisResult(Base):
    """Model for storing AI analysis results."""

    __tablename__ = "ai_analysis_results"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    image_hash = Column(String(64), unique=True, nullable=True)  # For caching

    # Analysis results
    product_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=False, default=0.0)

    # Structured data
    analysis_data = Column(JSON, nullable=True)
    pricing_suggestions = Column(JSON, nullable=True)
    marketplace_recommendations = Column(JSON, nullable=True)

    # Processing metadata
    processing_time_ms = Column(Integer, nullable=False)
    ai_service_used = Column(String(50), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self):
        return f"<AIAnalysisResult(id={self.id}, product='{self.product_name}', confidence={self.confidence_score})>"


class UnifiedAgentCoordinationLog(Base):
    """Model for logging agent coordination activities."""

    __tablename__ = "agent_coordination_logs"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), nullable=True)

    # Coordination details
    participating_agents = Column(JSON, nullable=False)  # List of agent IDs
    coordination_type = Column(
        String(50), nullable=False
    )  # 'decision', 'task', 'consensus'
    status = Column(String(20), nullable=False)  # 'pending', 'completed', 'failed'

    # Results
    result_data = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UnifiedAgentCoordinationLog(id={self.id}, type='{self.coordination_type}', status='{self.status}')>"


class ShippingArbitrageCalculation(Base):
    """Model for storing shipping arbitrage calculations."""

    __tablename__ = "shipping_arbitrage_calculations"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)

    # Cost calculations
    original_shipping_cost = Column(Numeric(10, 2), nullable=False)
    optimized_shipping_cost = Column(Numeric(10, 2), nullable=False)
    savings_amount = Column(Numeric(10, 2), nullable=False)
    savings_percentage = Column(Numeric(5, 2), nullable=False)

    # Optimization details
    optimization_method = Column(String(100), nullable=True)
    carrier_recommendations = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ShippingArbitrageCalculation(id={self.id}, savings=${self.savings_amount})>"


class CategoryOptimizationResult(Base):
    """Model for storing category optimization results."""

    __tablename__ = "category_optimization_results"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=True)

    # Category data
    original_category = Column(String(200), nullable=False)
    optimized_category = Column(String(200), nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False)
    performance_improvement = Column(Numeric(5, 2), nullable=True)  # Percentage

    # Marketplace specific
    marketplace = Column(String(50), nullable=False)
    category_path = Column(JSON, nullable=True)  # Full category hierarchy

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<CategoryOptimizationResult(id={self.id}, {self.original_category} -> {self.optimized_category})>"


class UnifiedUserRewardsBalance(Base):
    """Model for tracking user rewards and earnings."""

    __tablename__ = "user_rewards_balance"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)

    # Balance tracking
    current_balance = Column(Numeric(10, 2), nullable=False, default=0.00)
    lifetime_earned = Column(Numeric(10, 2), nullable=False, default=0.00)
    lifetime_redeemed = Column(Numeric(10, 2), nullable=False, default=0.00)

    # Redemption history
    redemption_history = Column(JSON, nullable=True)
    earning_sources = Column(JSON, nullable=True)  # Track how rewards were earned

    # Timestamps
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<UnifiedUserRewardsBalance(user_id={self.user_id}, balance=${self.current_balance})>"


class MarketplaceCompetitiveAnalysis(Base):
    """Model for storing marketplace competitive analysis data."""

    __tablename__ = "marketplace_competitive_analysis"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Analysis scope
    product_category = Column(String(100), nullable=False)
    marketplace = Column(String(50), nullable=False)
    analysis_date = Column(DateTime(timezone=True), server_default=func.now())

    # Analysis results
    competitor_data = Column(JSON, nullable=True)
    pricing_insights = Column(JSON, nullable=True)
    market_trends = Column(JSON, nullable=True)
    opportunity_score = Column(Float, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<MarketplaceCompetitiveAnalysis(category='{self.product_category}', marketplace='{self.marketplace}')>"


class ListingPerformancePrediction(Base):
    """Model for storing listing performance predictions."""

    __tablename__ = "listing_performance_predictions"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    # Listing data
    listing_data = Column(JSON, nullable=False)
    marketplace = Column(String(50), nullable=False)

    # Predictions
    predicted_views = Column(Integer, nullable=True)
    predicted_sales = Column(Integer, nullable=True)
    predicted_revenue = Column(Numeric(10, 2), nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=False)

    # Model metadata
    prediction_model = Column(String(50), nullable=False)
    model_version = Column(String(20), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ListingPerformancePrediction(id={self.id}, predicted_revenue=${self.predicted_revenue})>"


class FeatureUsageTracking(Base):
    """Model for tracking feature usage by users."""

    __tablename__ = "feature_usage_tracking"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)

    # Usage details
    feature_name = Column(String(100), nullable=False)
    usage_count = Column(Integer, nullable=False, default=1)
    subscription_tier = Column(String(50), nullable=True)

    # Usage metadata
    usage_date = Column(DateTime(timezone=True), server_default=func.now())
    usage_metadata = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<FeatureUsageTracking(user_id={self.user_id}, feature='{self.feature_name}', count={self.usage_count})>"


class ProductEmbedding(Base):
    """Model for storing product vector embeddings."""

    __tablename__ = "product_embeddings"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False)

    # Embedding data
    embedding_vector = Column(JSON, nullable=False)  # Store as JSON array for now
    embedding_model = Column(String(50), nullable=False)
    vector_dimension = Column(Integer, nullable=False)

    # Metadata
    source_data = Column(JSON, nullable=True)  # What data was used to create embedding

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ProductEmbedding(product_id={self.product_id}, model='{self.embedding_model}')>"


# Export all models
__all__ = [
    "AIAnalysisResult",
    "UnifiedAgentCoordinationLog",
    "ShippingArbitrageCalculation",
    "CategoryOptimizationResult",
    "UnifiedUserRewardsBalance",
    "MarketplaceCompetitiveAnalysis",
    "ListingPerformancePrediction",
    "FeatureUsageTracking",
    "ProductEmbedding",
]
