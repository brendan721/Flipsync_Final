"""
Subscription Models for FlipSync Payment Processing.

This module provides subscription-related models and enums for payment
processing and subscription management.
"""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Import BillingCycle from billing_cycle_manager
from .billing_cycle_manager import BillingCycle


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    TRIAL = "trial"


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""
    
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class SubscriptionPlan(BaseModel):
    """Subscription plan model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    description: str
    tier: SubscriptionTier
    billing_cycle: BillingCycle
    price: Decimal
    currency: str = "USD"
    trial_days: Optional[int] = None
    features: List[str] = Field(default_factory=list)
    limits: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UnifiedUserSubscription(BaseModel):
    """UnifiedUser subscription model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    billing_cycle: BillingCycle
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    payment_method_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubscriptionUsage(BaseModel):
    """Subscription usage tracking model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    subscription_id: str
    feature: str
    usage_count: int
    limit: Optional[int] = None
    period_start: datetime
    period_end: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PaymentRecord(BaseModel):
    """Payment record model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    subscription_id: str
    amount: Decimal
    currency: str = "USD"
    status: PaymentStatus
    payment_method: str
    provider_payment_id: Optional[str] = None
    provider_response: Dict[str, Any] = Field(default_factory=dict)
    billing_period_start: datetime
    billing_period_end: datetime
    processed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubscriptionEvent(BaseModel):
    """Subscription event model for tracking changes."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    subscription_id: str
    event_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SubscriptionMetrics(BaseModel):
    """Subscription metrics model."""
    
    model_config = ConfigDict(from_attributes=True)
    
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    trial_subscriptions: int = 0
    cancelled_subscriptions: int = 0
    monthly_recurring_revenue: Decimal = Decimal('0.00')
    annual_recurring_revenue: Decimal = Decimal('0.00')
    churn_rate: float = 0.0
    growth_rate: float = 0.0
    average_revenue_per_user: Decimal = Decimal('0.00')
    period_start: datetime
    period_end: datetime
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
