"""
Enhanced Subscription Management Service for FlipSync.

This service provides advanced subscription management including:
- Tier-based feature enforcement
- Usage tracking and analytics
- Upgrade suggestions and recommendations
- Billing and payment integration
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from fs_agt_clean.database.repositories.ai_analysis_repository import (
    FeatureUsageRepository,
)

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""

    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class FeatureType(str, Enum):
    """Feature types for usage tracking."""

    AI_ANALYSIS = "ai_analysis"
    VECTOR_SEARCH = "vector_search"
    MARKETPLACE_OPTIMIZATION = "marketplace_optimization"
    PERFORMANCE_PREDICTION = "performance_prediction"
    BULK_OPERATIONS = "bulk_operations"
    API_CALLS = "api_calls"
    STORAGE = "storage"
    SUPPORT = "support"


class UsageStatus(str, Enum):
    """Usage status indicators."""

    WITHIN_LIMITS = "within_limits"
    APPROACHING_LIMIT = "approaching_limit"
    LIMIT_EXCEEDED = "limit_exceeded"
    UNLIMITED = "unlimited"


class SubscriptionFeature:
    """Subscription feature configuration."""

    def __init__(
        self,
        feature_type: FeatureType,
        limit: Optional[int] = None,
        unlimited: bool = False,
        cost_per_unit: Decimal = Decimal("0.00"),
        description: str = "",
    ):
        self.feature_type = feature_type
        self.limit = limit
        self.unlimited = unlimited
        self.cost_per_unit = cost_per_unit
        self.description = description


class SubscriptionPlan:
    """Subscription plan configuration."""

    def __init__(
        self,
        tier: SubscriptionTier,
        name: str,
        monthly_price: Decimal,
        annual_price: Decimal,
        features: Dict[FeatureType, SubscriptionFeature],
        description: str = "",
        popular: bool = False,
    ):
        self.tier = tier
        self.name = name
        self.monthly_price = monthly_price
        self.annual_price = annual_price
        self.features = features
        self.description = description
        self.popular = popular


class UsageMetrics:
    """Usage metrics for a specific feature."""

    def __init__(
        self,
        feature_type: FeatureType,
        current_usage: int,
        limit: Optional[int],
        unlimited: bool,
        reset_date: datetime,
        usage_history: List[Dict[str, Any]],
    ):
        self.feature_type = feature_type
        self.current_usage = current_usage
        self.limit = limit
        self.unlimited = unlimited
        self.reset_date = reset_date
        self.usage_history = usage_history

    def get_usage_percentage(self) -> float:
        """Get usage as percentage of limit."""
        if self.unlimited or self.limit is None:
            return 0.0
        return (self.current_usage / self.limit) * 100 if self.limit > 0 else 0.0

    def get_status(self) -> UsageStatus:
        """Get current usage status."""
        if self.unlimited:
            return UsageStatus.UNLIMITED

        if self.limit is None:
            return UsageStatus.WITHIN_LIMITS

        percentage = self.get_usage_percentage()

        if percentage >= 100:
            return UsageStatus.LIMIT_EXCEEDED
        elif percentage >= 80:
            return UsageStatus.APPROACHING_LIMIT
        else:
            return UsageStatus.WITHIN_LIMITS


class EnhancedSubscriptionService:
    """
    Enhanced subscription management service.

    This service provides:
    - Tier-based feature enforcement
    - Usage tracking and analytics
    - Upgrade suggestions and recommendations
    - Billing and payment integration
    """

    def __init__(self):
        """Initialize the enhanced subscription service."""
        self.usage_repository = FeatureUsageRepository()

        # Define subscription plans
        self.subscription_plans = self._initialize_subscription_plans()

        logger.info("Enhanced Subscription Service initialized")

    def _initialize_subscription_plans(
        self,
    ) -> Dict[SubscriptionTier, SubscriptionPlan]:
        """Initialize subscription plan configurations."""

        # Free tier features
        free_features = {
            FeatureType.AI_ANALYSIS: SubscriptionFeature(
                FeatureType.AI_ANALYSIS,
                limit=10,
                description="10 AI analyses per month",
            ),
            FeatureType.VECTOR_SEARCH: SubscriptionFeature(
                FeatureType.VECTOR_SEARCH,
                limit=50,
                description="50 semantic searches per month",
            ),
            FeatureType.MARKETPLACE_OPTIMIZATION: SubscriptionFeature(
                FeatureType.MARKETPLACE_OPTIMIZATION,
                limit=5,
                description="5 marketplace optimizations per month",
            ),
            FeatureType.API_CALLS: SubscriptionFeature(
                FeatureType.API_CALLS,
                limit=1000,
                description="1,000 API calls per month",
            ),
            FeatureType.STORAGE: SubscriptionFeature(
                FeatureType.STORAGE, limit=100, description="100 MB storage"
            ),
        }

        # Basic tier features
        basic_features = {
            FeatureType.AI_ANALYSIS: SubscriptionFeature(
                FeatureType.AI_ANALYSIS,
                limit=100,
                description="100 AI analyses per month",
            ),
            FeatureType.VECTOR_SEARCH: SubscriptionFeature(
                FeatureType.VECTOR_SEARCH,
                limit=500,
                description="500 semantic searches per month",
            ),
            FeatureType.MARKETPLACE_OPTIMIZATION: SubscriptionFeature(
                FeatureType.MARKETPLACE_OPTIMIZATION,
                limit=50,
                description="50 marketplace optimizations per month",
            ),
            FeatureType.PERFORMANCE_PREDICTION: SubscriptionFeature(
                FeatureType.PERFORMANCE_PREDICTION,
                limit=25,
                description="25 performance predictions per month",
            ),
            FeatureType.API_CALLS: SubscriptionFeature(
                FeatureType.API_CALLS,
                limit=10000,
                description="10,000 API calls per month",
            ),
            FeatureType.STORAGE: SubscriptionFeature(
                FeatureType.STORAGE, limit=1000, description="1 GB storage"
            ),
            FeatureType.SUPPORT: SubscriptionFeature(
                FeatureType.SUPPORT, unlimited=True, description="Email support"
            ),
        }

        # Premium tier features
        premium_features = {
            FeatureType.AI_ANALYSIS: SubscriptionFeature(
                FeatureType.AI_ANALYSIS,
                limit=1000,
                description="1,000 AI analyses per month",
            ),
            FeatureType.VECTOR_SEARCH: SubscriptionFeature(
                FeatureType.VECTOR_SEARCH,
                unlimited=True,
                description="Unlimited semantic searches",
            ),
            FeatureType.MARKETPLACE_OPTIMIZATION: SubscriptionFeature(
                FeatureType.MARKETPLACE_OPTIMIZATION,
                unlimited=True,
                description="Unlimited marketplace optimizations",
            ),
            FeatureType.PERFORMANCE_PREDICTION: SubscriptionFeature(
                FeatureType.PERFORMANCE_PREDICTION,
                unlimited=True,
                description="Unlimited performance predictions",
            ),
            FeatureType.BULK_OPERATIONS: SubscriptionFeature(
                FeatureType.BULK_OPERATIONS,
                unlimited=True,
                description="Bulk operations support",
            ),
            FeatureType.API_CALLS: SubscriptionFeature(
                FeatureType.API_CALLS,
                limit=100000,
                description="100,000 API calls per month",
            ),
            FeatureType.STORAGE: SubscriptionFeature(
                FeatureType.STORAGE, limit=10000, description="10 GB storage"
            ),
            FeatureType.SUPPORT: SubscriptionFeature(
                FeatureType.SUPPORT, unlimited=True, description="Priority support"
            ),
        }

        # Enterprise tier features
        enterprise_features = {
            feature_type: SubscriptionFeature(
                feature_type,
                unlimited=True,
                description=f"Unlimited {feature_type.value}",
            )
            for feature_type in FeatureType
        }

        return {
            SubscriptionTier.FREE: SubscriptionPlan(
                SubscriptionTier.FREE,
                "Free",
                Decimal("0.00"),
                Decimal("0.00"),
                free_features,
                "Perfect for getting started",
                False,
            ),
            SubscriptionTier.BASIC: SubscriptionPlan(
                SubscriptionTier.BASIC,
                "Basic",
                Decimal("29.99"),
                Decimal("299.99"),
                basic_features,
                "Great for small businesses",
                False,
            ),
            SubscriptionTier.PREMIUM: SubscriptionPlan(
                SubscriptionTier.PREMIUM,
                "Premium",
                Decimal("99.99"),
                Decimal("999.99"),
                premium_features,
                "Perfect for growing businesses",
                True,
            ),
            SubscriptionTier.ENTERPRISE: SubscriptionPlan(
                SubscriptionTier.ENTERPRISE,
                "Enterprise",
                Decimal("299.99"),
                Decimal("2999.99"),
                enterprise_features,
                "For large organizations",
                False,
            ),
        }

    async def check_feature_access(
        self,
        user_id: str,
        feature_type: FeatureType,
        subscription_tier: SubscriptionTier,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if user has access to a specific feature.

        Args:
            user_id: UnifiedUser ID
            feature_type: Feature to check
            subscription_tier: UnifiedUser's subscription tier

        Returns:
            Tuple of (has_access, access_info)
        """
        try:
            # Get subscription plan
            plan = self.subscription_plans.get(subscription_tier)
            if not plan:
                return False, {"error": "Invalid subscription tier"}

            # Get feature configuration
            feature = plan.features.get(feature_type)
            if not feature:
                return False, {"error": "Feature not available in this tier"}

            # Check if feature is unlimited
            if feature.unlimited:
                return True, {
                    "access": True,
                    "unlimited": True,
                    "message": "Unlimited access",
                }

            # Get current usage
            usage_metrics = await self.get_usage_metrics(user_id, feature_type)

            # Check if within limits
            if feature.limit is None:
                has_access = True
            else:
                has_access = usage_metrics.current_usage < feature.limit

            return has_access, {
                "access": has_access,
                "unlimited": False,
                "current_usage": usage_metrics.current_usage,
                "limit": feature.limit,
                "usage_percentage": usage_metrics.get_usage_percentage(),
                "status": usage_metrics.get_status().value,
                "reset_date": usage_metrics.reset_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error checking feature access: {e}")
            return False, {"error": str(e)}

    async def get_usage_metrics(
        self, user_id: str, feature_type: FeatureType
    ) -> UsageMetrics:
        """Get usage metrics for a specific feature."""
        try:
            # Calculate reset date (first day of next month)
            now = datetime.now(timezone.utc)
            if now.month == 12:
                reset_date = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                reset_date = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)

            # Get usage stats from repository
            # For now, return mock data since we don't have actual usage tracking
            current_usage = 0  # This would come from actual usage tracking

            return UsageMetrics(
                feature_type=feature_type,
                current_usage=current_usage,
                limit=None,  # Will be set based on subscription tier
                unlimited=False,
                reset_date=reset_date,
                usage_history=[],
            )

        except Exception as e:
            logger.error(f"Error getting usage metrics: {e}")
            return UsageMetrics(
                feature_type=feature_type,
                current_usage=0,
                limit=None,
                unlimited=False,
                reset_date=datetime.now(timezone.utc) + timedelta(days=30),
                usage_history=[],
            )

    async def track_feature_usage(
        self,
        user_id: str,
        feature_type: FeatureType,
        subscription_tier: SubscriptionTier,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Track feature usage for a user."""
        try:
            # Track usage in repository
            await self.usage_repository.track_usage(
                user_id=user_id,
                feature_name=feature_type.value,
                subscription_tier=subscription_tier.value,
                metadata=metadata,
            )

            logger.info(f"Tracked usage for user {user_id}: {feature_type.value}")
            return True

        except Exception as e:
            logger.error(f"Error tracking feature usage: {e}")
            return False

    def get_subscription_plans(self) -> Dict[str, Any]:
        """Get all available subscription plans."""
        plans = {}

        for tier, plan in self.subscription_plans.items():
            plans[tier.value] = {
                "name": plan.name,
                "tier": plan.tier.value,
                "monthly_price": float(plan.monthly_price),
                "annual_price": float(plan.annual_price),
                "description": plan.description,
                "popular": plan.popular,
                "features": {
                    feature_type.value: {
                        "limit": feature.limit,
                        "unlimited": feature.unlimited,
                        "description": feature.description,
                        "cost_per_unit": float(feature.cost_per_unit),
                    }
                    for feature_type, feature in plan.features.items()
                },
            }

        return plans

    async def get_upgrade_suggestions(
        self, user_id: str, current_tier: SubscriptionTier
    ) -> List[Dict[str, Any]]:
        """Get upgrade suggestions based on usage patterns."""
        try:
            suggestions = []

            # Get current plan
            current_plan = self.subscription_plans.get(current_tier)
            if not current_plan:
                return suggestions

            # Check usage for each feature
            for feature_type in FeatureType:
                usage_metrics = await self.get_usage_metrics(user_id, feature_type)

                if usage_metrics.get_status() in [
                    UsageStatus.APPROACHING_LIMIT,
                    UsageStatus.LIMIT_EXCEEDED,
                ]:
                    # Find next tier that provides more of this feature
                    for tier in [
                        SubscriptionTier.BASIC,
                        SubscriptionTier.PREMIUM,
                        SubscriptionTier.ENTERPRISE,
                    ]:
                        if tier.value <= current_tier.value:
                            continue

                        plan = self.subscription_plans[tier]
                        feature = plan.features.get(feature_type)

                        if feature and (
                            feature.unlimited
                            or (feature.limit and feature.limit > usage_metrics.limit)
                        ):
                            suggestions.append(
                                {
                                    "reason": f"Approaching limit for {feature_type.value}",
                                    "current_usage": usage_metrics.current_usage,
                                    "current_limit": usage_metrics.limit,
                                    "suggested_tier": tier.value,
                                    "suggested_plan": plan.name,
                                    "new_limit": (
                                        feature.limit
                                        if not feature.unlimited
                                        else "unlimited"
                                    ),
                                    "monthly_price": float(plan.monthly_price),
                                    "annual_price": float(plan.annual_price),
                                }
                            )
                            break

            return suggestions

        except Exception as e:
            logger.error(f"Error getting upgrade suggestions: {e}")
            return []


# Global service instance
enhanced_subscription_service = EnhancedSubscriptionService()
