"""
Revenue Model for FlipSync Database Operations
=============================================

This module provides database models for revenue-related operations including
shipping arbitrage calculations, revenue tracking, and user rewards balance.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base


class ShippingArbitrageCalculation(Base):
    """Model for storing shipping arbitrage calculations."""

    __tablename__ = "shipping_arbitrage_calculations"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Primary identification
    calculation_id = Column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    product_id = Column(String(100), nullable=True, index=True)

    # Shipping cost details
    original_shipping_cost = Column(Numeric(10, 2), nullable=False)
    optimized_shipping_cost = Column(Numeric(10, 2), nullable=False)
    savings_amount = Column(Numeric(10, 2), nullable=False)
    savings_percentage = Column(Numeric(5, 2), nullable=False)

    # Optimization details
    optimization_method = Column(String(100), nullable=False)
    carrier_original = Column(String(50), nullable=True)
    carrier_optimized = Column(String(50), nullable=True)
    service_type_original = Column(String(50), nullable=True)
    service_type_optimized = Column(String(50), nullable=True)

    # Shipping details
    origin_address = Column(JSON, default=dict)
    destination_address = Column(JSON, default=dict)
    package_details = Column(JSON, default=dict)

    # Metadata
    calculation_metadata = Column(JSON, default=dict)
    status = Column(String(20), default="completed", nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "calculation_id": self.calculation_id,
            "user_id": str(self.user_id),
            "product_id": self.product_id,
            "original_shipping_cost": float(self.original_shipping_cost),
            "optimized_shipping_cost": float(self.optimized_shipping_cost),
            "savings_amount": float(self.savings_amount),
            "savings_percentage": float(self.savings_percentage),
            "optimization_method": self.optimization_method,
            "carrier_original": self.carrier_original,
            "carrier_optimized": self.carrier_optimized,
            "service_type_original": self.service_type_original,
            "service_type_optimized": self.service_type_optimized,
            "origin_address": self.origin_address,
            "destination_address": self.destination_address,
            "package_details": self.package_details,
            "calculation_metadata": self.calculation_metadata,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RevenueTracking(Base):
    """Model for tracking various revenue streams."""

    __tablename__ = "revenue_tracking"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Primary identification
    revenue_id = Column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Revenue details
    revenue_type = Column(
        String(50), nullable=False, index=True
    )  # shipping_savings, listing_optimization, etc.
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    source = Column(String(100), nullable=False)

    # Transaction details
    transaction_id = Column(String(100), nullable=True, index=True)
    marketplace = Column(String(50), nullable=True, index=True)
    product_id = Column(String(100), nullable=True, index=True)

    # Revenue metadata
    revenue_metadata = Column(JSON, default=dict)
    calculation_details = Column(JSON, default=dict)

    # Status and tracking
    status = Column(String(20), default="recorded", nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "revenue_id": self.revenue_id,
            "user_id": str(self.user_id),
            "revenue_type": self.revenue_type,
            "amount": float(self.amount),
            "currency": self.currency,
            "source": self.source,
            "transaction_id": self.transaction_id,
            "marketplace": self.marketplace,
            "product_id": self.product_id,
            "revenue_metadata": self.revenue_metadata,
            "calculation_details": self.calculation_details,
            "status": self.status,
            "processed_at": (
                self.processed_at.isoformat() if self.processed_at else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UnifiedUserRewardsBalance(Base):
    """Model for tracking user rewards balance and history."""

    __tablename__ = "user_rewards_balance"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Primary identification
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Balance details
    current_balance = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    lifetime_earned = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)
    lifetime_redeemed = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    # Rewards metadata
    redemption_history = Column(JSON, default=list)
    earning_history = Column(JSON, default=list)
    tier_status = Column(String(20), default="bronze", nullable=False)
    tier_benefits = Column(JSON, default=dict)

    # Tracking
    last_earning_date = Column(DateTime(timezone=True), nullable=True)
    last_redemption_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "user_id": str(self.user_id),
            "current_balance": float(self.current_balance),
            "lifetime_earned": float(self.lifetime_earned),
            "lifetime_redeemed": float(self.lifetime_redeemed),
            "redemption_history": self.redemption_history,
            "earning_history": self.earning_history,
            "tier_status": self.tier_status,
            "tier_benefits": self.tier_benefits,
            "last_earning_date": (
                self.last_earning_date.isoformat() if self.last_earning_date else None
            ),
            "last_redemption_date": (
                self.last_redemption_date.isoformat()
                if self.last_redemption_date
                else None
            ),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class RevenueOptimizationLog(Base):
    """Model for logging revenue optimization activities."""

    __tablename__ = "revenue_optimization_logs"
    __table_args__ = {"extend_existing": True}

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Primary identification
    log_id = Column(
        String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )

    # Optimization details
    optimization_type = Column(String(50), nullable=False, index=True)
    optimization_target = Column(String(100), nullable=False)

    # Results
    before_value = Column(Numeric(10, 2), nullable=True)
    after_value = Column(Numeric(10, 2), nullable=True)
    improvement_amount = Column(Numeric(10, 2), nullable=True)
    improvement_percentage = Column(Numeric(5, 2), nullable=True)

    # Optimization metadata
    optimization_data = Column(JSON, default=dict)
    algorithm_used = Column(String(100), nullable=True)
    confidence_score = Column(Numeric(3, 2), nullable=True)

    # Status
    status = Column(String(20), default="completed", nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "log_id": self.log_id,
            "user_id": str(self.user_id),
            "optimization_type": self.optimization_type,
            "optimization_target": self.optimization_target,
            "before_value": float(self.before_value) if self.before_value else None,
            "after_value": float(self.after_value) if self.after_value else None,
            "improvement_amount": (
                float(self.improvement_amount) if self.improvement_amount else None
            ),
            "improvement_percentage": (
                float(self.improvement_percentage)
                if self.improvement_percentage
                else None
            ),
            "optimization_data": self.optimization_data,
            "algorithm_used": self.algorithm_used,
            "confidence_score": (
                float(self.confidence_score) if self.confidence_score else None
            ),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Export all models
__all__ = [
    "ShippingArbitrageCalculation",
    "RevenueTracking",
    "UnifiedUserRewardsBalance",
    "RevenueOptimizationLog",
]
