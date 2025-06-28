"""
Database Models for Market Data
===============================

This module defines SQLAlchemy models for market-related data including
products, pricing, inventory, competitors, and market decisions.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from fs_agt_clean.core.models.database.base import Base


class ProductModel(Base):
    """Product model for marketplace products."""

    __tablename__ = "products"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Product identifiers
    asin = Column(String(20), nullable=True, index=True)  # Amazon ASIN
    sku = Column(String(100), nullable=True, index=True)  # Stock Keeping Unit
    upc = Column(String(20), nullable=True, index=True)  # Universal Product Code
    ean = Column(String(20), nullable=True, index=True)  # European Article Number
    isbn = Column(String(20), nullable=True, index=True)  # ISBN for books
    mpn = Column(String(100), nullable=True, index=True)  # Manufacturer Part Number
    ebay_item_id = Column(String(50), nullable=True, index=True)  # eBay Item ID
    internal_id = Column(String(100), nullable=True, index=True)  # Internal product ID

    # Product information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    marketplace = Column(String(50), nullable=False, index=True)
    category = Column(String(200), nullable=True)
    brand = Column(String(200), nullable=True)

    # Status and metadata
    status = Column(String(50), default="active", index=True)
    product_metadata = Column(
        JSON, default=dict
    )  # Renamed from 'metadata' to avoid SQLAlchemy conflict

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    price_history = relationship(
        "PriceHistoryModel", back_populates="product", cascade="all, delete-orphan"
    )
    inventory_records = relationship(
        "InventoryModel", back_populates="product", cascade="all, delete-orphan"
    )
    competitor_data = relationship(
        "CompetitorModel", back_populates="product", cascade="all, delete-orphan"
    )
    pricing_recommendations = relationship(
        "PricingRecommendationModel",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    market_decisions = relationship(
        "MarketDecisionModel", back_populates="product", cascade="all, delete-orphan"
    )

    # Indexes for common queries
    __table_args__ = (
        Index("idx_product_asin_marketplace", "asin", "marketplace"),
        Index("idx_product_sku_marketplace", "sku", "marketplace"),
        Index("idx_product_identifiers", "asin", "sku", "upc", "ean"),
        {"extend_existing": True},
    )


class PriceHistoryModel(Base):
    """Price history model for tracking price changes."""

    __tablename__ = "price_history"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    marketplace = Column(String(50), nullable=False, index=True)

    # Price details
    includes_shipping = Column(Boolean, default=False)
    includes_tax = Column(Boolean, default=False)
    source = Column(String(50), default="api")  # api, manual, scraping

    # Timestamps
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product = relationship("ProductModel", back_populates="price_history")

    # Indexes
    __table_args__ = (
        Index("idx_price_history_product_date", "product_id", "recorded_at"),
        Index("idx_price_history_marketplace_date", "marketplace", "recorded_at"),
        {"extend_existing": True},
    )


class CompetitorModel(Base):
    """Competitor data model for tracking competitor information."""

    __tablename__ = "competitors"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    competitor_asin = Column(String(20), nullable=True, index=True)
    competitor_sku = Column(String(100), nullable=True)
    competitor_seller_id = Column(String(100), nullable=True)

    # Competitor pricing
    competitor_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    marketplace = Column(String(50), nullable=False, index=True)

    # Competitor details
    competitor_title = Column(String(500), nullable=True)
    competitor_rating = Column(Numeric(3, 2), nullable=True)
    competitor_review_count = Column(Integer, nullable=True)
    competitor_data = Column(JSON, default=dict)  # Additional competitor info

    # Timestamps
    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product = relationship("ProductModel", back_populates="competitor_data")

    # Indexes
    __table_args__ = (
        Index("idx_competitor_product_date", "product_id", "recorded_at"),
        Index("idx_competitor_asin_marketplace", "competitor_asin", "marketplace"),
        {"extend_existing": True},
    )


class InventoryModel(Base):
    """Inventory status model for tracking stock levels."""

    __tablename__ = "inventory"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    marketplace = Column(String(50), nullable=False, index=True)

    # Inventory quantities
    quantity_available = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    quantity_inbound = Column(Integer, nullable=False, default=0)

    # Inventory management
    reorder_point = Column(Integer, nullable=True)
    max_stock_level = Column(Integer, nullable=True)
    warehouse_locations = Column(JSON, default=list)
    fulfillment_method = Column(String(50), nullable=True)  # FBA, FBM, etc.

    # Timestamps
    last_updated = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product = relationship("ProductModel", back_populates="inventory_records")

    # Indexes
    __table_args__ = (
        Index("idx_inventory_product_marketplace", "product_id", "marketplace"),
        Index("idx_inventory_updated", "last_updated"),
        UniqueConstraint(
            "product_id", "marketplace", name="uq_inventory_product_marketplace"
        ),
        {"extend_existing": True},
    )


class PricingRecommendationModel(Base):
    """Pricing recommendation model for storing AI pricing suggestions."""

    __tablename__ = "pricing_recommendations"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    recommendation_id = Column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Pricing information
    current_price = Column(Numeric(10, 2), nullable=False)
    recommended_price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    marketplace = Column(String(50), nullable=False, index=True)

    # Recommendation details
    price_change_direction = Column(
        String(20), nullable=False
    )  # increase, decrease, maintain
    confidence_score = Column(Numeric(3, 2), nullable=False)
    reasoning = Column(Text, nullable=False)

    # Analysis data
    expected_impact = Column(JSON, default=dict)
    market_conditions = Column(JSON, default=dict)
    competitor_analysis = Column(JSON, default=dict)

    # Status and timestamps
    status = Column(
        String(20), default="pending", index=True
    )  # pending, approved, rejected, executed
    expires_at = Column(DateTime, nullable=True, index=True)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product = relationship("ProductModel", back_populates="pricing_recommendations")

    # Indexes
    __table_args__ = (
        Index("idx_pricing_rec_product_status", "product_id", "status"),
        Index("idx_pricing_rec_expires", "expires_at"),
        {"extend_existing": True},
    )


class MarketDecisionModel(Base):
    """Market decision model for tracking AI agent decisions."""

    __tablename__ = "market_decisions"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    decision_id = Column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )
    decision_type = Column(
        String(50), nullable=False, index=True
    )  # pricing, inventory, optimization
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)

    # Decision details
    current_state = Column(JSON, default=dict)
    recommended_action = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False)

    # Impact and risk assessment
    expected_outcome = Column(JSON, default=dict)
    risk_assessment = Column(JSON, default=dict)

    # Approval and execution
    requires_approval = Column(Boolean, default=True, index=True)
    auto_execute = Column(Boolean, default=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    executed_at = Column(DateTime, nullable=True)

    # Status tracking
    status = Column(
        String(20), default="pending", index=True
    )  # pending, approved, rejected, executed, failed
    execution_result = Column(JSON, default=dict)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product = relationship("ProductModel", back_populates="market_decisions")

    # Indexes
    __table_args__ = (
        Index("idx_market_decision_type_status", "decision_type", "status"),
        Index("idx_market_decision_product_type", "product_id", "decision_type"),
        Index("idx_market_decision_approval", "requires_approval", "status"),
        {"extend_existing": True},
    )


class MarketMetricsModel(Base):
    """Market metrics model for tracking performance data."""

    __tablename__ = "market_metrics"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    marketplace = Column(String(50), nullable=False, index=True)

    # Performance metrics
    sales_rank = Column(Integer, nullable=True)
    category_rank = Column(Integer, nullable=True)
    buy_box_percentage = Column(Numeric(5, 2), nullable=True)
    conversion_rate = Column(Numeric(5, 2), nullable=True)
    click_through_rate = Column(Numeric(5, 2), nullable=True)

    # Sales data
    impression_count = Column(Integer, nullable=True)
    session_count = Column(Integer, nullable=True)
    units_sold = Column(Integer, nullable=True)
    revenue = Column(Numeric(12, 2), nullable=True)
    profit_margin = Column(Numeric(5, 4), nullable=True)

    # Quality metrics
    return_rate = Column(Numeric(5, 2), nullable=True)
    customer_satisfaction = Column(Numeric(3, 2), nullable=True)

    # Time period
    date_range_start = Column(DateTime, nullable=False, index=True)
    date_range_end = Column(DateTime, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product = relationship("ProductModel")

    # Indexes
    __table_args__ = (
        Index("idx_market_metrics_product_date", "product_id", "date_range_start"),
        Index("idx_market_metrics_marketplace_date", "marketplace", "date_range_start"),
        {"extend_existing": True},
    )


class MarketAlertModel(Base):
    """Market alert model for tracking important market events."""

    __tablename__ = "market_alerts"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    alert_id = Column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True)

    # Alert details
    alert_type = Column(
        String(50), nullable=False, index=True
    )  # price_change, stock_out, new_competitor
    severity = Column(
        String(20), default="medium", index=True
    )  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)

    # Alert data
    data = Column(JSON, default=dict)
    action_required = Column(Boolean, default=False, index=True)
    suggested_actions = Column(JSON, default=list)

    # Status tracking
    status = Column(
        String(20), default="active", index=True
    )  # active, acknowledged, resolved, dismissed
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    product = relationship("ProductModel")

    # Indexes
    __table_args__ = (
        Index("idx_market_alert_type_severity", "alert_type", "severity"),
        Index("idx_market_alert_status_created", "status", "created_at"),
        Index("idx_market_alert_action_required", "action_required", "status"),
        {"extend_existing": True},
    )
