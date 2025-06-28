"""
Usage Analytics Service for FlipSync Subscription Management.

This service provides detailed analytics and insights for subscription usage:
- Usage pattern analysis
- Cost optimization recommendations
- Feature adoption tracking
- Billing analytics and forecasting
"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fs_agt_clean.services.subscription.enhanced_subscription_service import (
    FeatureType,
    SubscriptionTier,
    enhanced_subscription_service,
)

logger = logging.getLogger(__name__)


class UsagePattern:
    """Usage pattern analysis result."""

    def __init__(
        self,
        feature_type: FeatureType,
        daily_average: float,
        weekly_trend: str,
        peak_usage_day: str,
        peak_usage_hour: int,
        growth_rate: float,
    ):
        self.feature_type = feature_type
        self.daily_average = daily_average
        self.weekly_trend = weekly_trend
        self.peak_usage_day = peak_usage_day
        self.peak_usage_hour = peak_usage_hour
        self.growth_rate = growth_rate


class CostOptimization:
    """Cost optimization recommendation."""

    def __init__(
        self,
        current_cost: Decimal,
        optimized_cost: Decimal,
        savings: Decimal,
        recommendation: str,
        confidence: float,
    ):
        self.current_cost = current_cost
        self.optimized_cost = optimized_cost
        self.savings = savings
        self.recommendation = recommendation
        self.confidence = confidence


class UsageAnalyticsService:
    """
    Usage analytics service for subscription management.

    This service provides:
    - Usage pattern analysis and insights
    - Cost optimization recommendations
    - Feature adoption tracking
    - Billing analytics and forecasting
    """

    def __init__(self):
        """Initialize the usage analytics service."""
        self.subscription_service = enhanced_subscription_service

        # Mock usage data for demonstration
        self.mock_usage_data = self._generate_mock_usage_data()

        logger.info("Usage Analytics Service initialized")

    def _generate_mock_usage_data(self) -> Dict[str, Any]:
        """Generate mock usage data for demonstration."""
        return {
            "user_123": {
                FeatureType.AI_ANALYSIS: {
                    "daily_usage": [5, 8, 12, 6, 9, 15, 3],  # Last 7 days
                    "hourly_distribution": [
                        0,
                        0,
                        1,
                        2,
                        5,
                        8,
                        12,
                        15,
                        18,
                        20,
                        16,
                        12,
                        8,
                        5,
                        3,
                        2,
                        1,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                    ],
                    "monthly_total": 180,
                    "previous_month": 150,
                },
                FeatureType.VECTOR_SEARCH: {
                    "daily_usage": [25, 30, 45, 20, 35, 50, 15],
                    "hourly_distribution": [
                        2,
                        1,
                        3,
                        5,
                        8,
                        12,
                        18,
                        25,
                        30,
                        35,
                        28,
                        22,
                        18,
                        15,
                        12,
                        8,
                        5,
                        3,
                        2,
                        1,
                        1,
                        0,
                        0,
                        1,
                    ],
                    "monthly_total": 680,
                    "previous_month": 520,
                },
                FeatureType.MARKETPLACE_OPTIMIZATION: {
                    "daily_usage": [3, 5, 8, 2, 4, 10, 1],
                    "hourly_distribution": [
                        0,
                        0,
                        0,
                        1,
                        2,
                        3,
                        5,
                        8,
                        10,
                        12,
                        8,
                        6,
                        4,
                        3,
                        2,
                        1,
                        1,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                        0,
                    ],
                    "monthly_total": 95,
                    "previous_month": 75,
                },
            }
        }

    async def analyze_usage_patterns(
        self, user_id: str, feature_type: Optional[FeatureType] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze usage patterns for a user.

        Args:
            user_id: UnifiedUser ID
            feature_type: Specific feature to analyze (optional)
            days: Number of days to analyze

        Returns:
            Usage pattern analysis
        """
        try:
            # Get user usage data (mock for now)
            user_data = self.mock_usage_data.get(user_id, {})

            if feature_type:
                # Analyze specific feature
                feature_data = user_data.get(feature_type, {})
                pattern = self._analyze_feature_pattern(feature_type, feature_data)

                return {
                    "feature_type": feature_type.value,
                    "pattern": {
                        "daily_average": pattern.daily_average,
                        "weekly_trend": pattern.weekly_trend,
                        "peak_usage_day": pattern.peak_usage_day,
                        "peak_usage_hour": pattern.peak_usage_hour,
                        "growth_rate": pattern.growth_rate,
                    },
                    "insights": self._generate_pattern_insights(pattern),
                    "recommendations": self._generate_pattern_recommendations(pattern),
                }
            else:
                # Analyze all features
                patterns = {}
                for ft in FeatureType:
                    if ft in user_data:
                        feature_data = user_data[ft]
                        pattern = self._analyze_feature_pattern(ft, feature_data)
                        patterns[ft.value] = {
                            "daily_average": pattern.daily_average,
                            "weekly_trend": pattern.weekly_trend,
                            "peak_usage_day": pattern.peak_usage_day,
                            "peak_usage_hour": pattern.peak_usage_hour,
                            "growth_rate": pattern.growth_rate,
                        }

                return {
                    "patterns": patterns,
                    "overall_insights": self._generate_overall_insights(patterns),
                    "recommendations": self._generate_overall_recommendations(patterns),
                }

        except Exception as e:
            logger.error(f"Error analyzing usage patterns: {e}")
            return {"error": str(e)}

    def _analyze_feature_pattern(
        self, feature_type: FeatureType, feature_data: Dict[str, Any]
    ) -> UsagePattern:
        """Analyze usage pattern for a specific feature."""

        daily_usage = feature_data.get("daily_usage", [0] * 7)
        hourly_distribution = feature_data.get("hourly_distribution", [0] * 24)
        monthly_total = feature_data.get("monthly_total", 0)
        previous_month = feature_data.get("previous_month", 0)

        # Calculate daily average
        daily_average = sum(daily_usage) / len(daily_usage) if daily_usage else 0

        # Determine weekly trend
        first_half = sum(daily_usage[:3])
        second_half = sum(daily_usage[4:])
        if second_half > first_half * 1.1:
            weekly_trend = "increasing"
        elif second_half < first_half * 0.9:
            weekly_trend = "decreasing"
        else:
            weekly_trend = "stable"

        # Find peak usage day
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        peak_day_index = daily_usage.index(max(daily_usage)) if daily_usage else 0
        peak_usage_day = days[peak_day_index]

        # Find peak usage hour
        peak_usage_hour = (
            hourly_distribution.index(max(hourly_distribution))
            if hourly_distribution
            else 9
        )

        # Calculate growth rate
        growth_rate = (
            ((monthly_total - previous_month) / previous_month * 100)
            if previous_month > 0
            else 0
        )

        return UsagePattern(
            feature_type=feature_type,
            daily_average=daily_average,
            weekly_trend=weekly_trend,
            peak_usage_day=peak_usage_day,
            peak_usage_hour=peak_usage_hour,
            growth_rate=growth_rate,
        )

    def _generate_pattern_insights(self, pattern: UsagePattern) -> List[str]:
        """Generate insights from usage pattern."""
        insights = []

        if pattern.growth_rate > 20:
            insights.append(
                f"High growth rate of {pattern.growth_rate:.1f}% indicates increasing adoption"
            )
        elif pattern.growth_rate < -10:
            insights.append(
                f"Declining usage of {pattern.growth_rate:.1f}% may indicate issues or reduced need"
            )

        if pattern.daily_average > 50:
            insights.append(
                "High daily usage suggests this is a core feature for the user"
            )
        elif pattern.daily_average < 5:
            insights.append(
                "Low daily usage suggests limited adoption or occasional use"
            )

        if pattern.peak_usage_hour in range(9, 17):
            insights.append(
                "Peak usage during business hours indicates professional use"
            )
        elif pattern.peak_usage_hour in range(18, 23):
            insights.append("Peak usage in evening suggests personal/side business use")

        return insights

    def _generate_pattern_recommendations(self, pattern: UsagePattern) -> List[str]:
        """Generate recommendations from usage pattern."""
        recommendations = []

        if pattern.growth_rate > 30:
            recommendations.append(
                "Consider upgrading subscription tier to accommodate growing usage"
            )

        if pattern.weekly_trend == "increasing":
            recommendations.append("Monitor usage closely as it's trending upward")

        if (
            pattern.daily_average > 40
            and pattern.feature_type == FeatureType.AI_ANALYSIS
        ):
            recommendations.append(
                "High AI analysis usage - consider Premium tier for unlimited access"
            )

        return recommendations

    def _generate_overall_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate overall insights from all patterns."""
        insights = []

        # Count features with high growth
        high_growth_features = sum(
            1 for p in patterns.values() if p.get("growth_rate", 0) > 20
        )

        if high_growth_features >= 2:
            insights.append(
                "Multiple features showing high growth - strong platform adoption"
            )

        # Check for consistent peak hours
        peak_hours = [p.get("peak_usage_hour", 9) for p in patterns.values()]
        if len(set(peak_hours)) <= 2:
            insights.append(
                "Consistent usage patterns across features indicate focused work sessions"
            )

        return insights

    def _generate_overall_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations from all patterns."""
        recommendations = []

        # Check if multiple features are growing
        growing_features = [
            name for name, p in patterns.items() if p.get("growth_rate", 0) > 15
        ]

        if len(growing_features) >= 2:
            recommendations.append(
                "Multiple growing features suggest considering a higher tier subscription"
            )

        return recommendations

    async def get_cost_optimization_recommendations(
        self, user_id: str, current_tier: SubscriptionTier
    ) -> List[CostOptimization]:
        """Get cost optimization recommendations for a user."""
        try:
            recommendations = []

            # Get current plan
            plans = self.subscription_service.get_subscription_plans()
            current_plan = plans.get(current_tier.value)

            if not current_plan:
                return recommendations

            current_monthly_cost = Decimal(str(current_plan["monthly_price"]))

            # Analyze usage patterns
            usage_analysis = await self.analyze_usage_patterns(user_id)
            patterns = usage_analysis.get("patterns", {})

            # Check if user is underutilizing current tier
            underutilized_features = 0
            for feature_name, pattern in patterns.items():
                if pattern.get("daily_average", 0) < 5:  # Low usage threshold
                    underutilized_features += 1

            # Recommend downgrade if significantly underutilized
            if underutilized_features >= 2 and current_tier != SubscriptionTier.FREE:
                lower_tiers = [
                    SubscriptionTier.FREE,
                    SubscriptionTier.BASIC,
                    SubscriptionTier.PREMIUM,
                ]
                for tier in lower_tiers:
                    if tier.value < current_tier.value:
                        lower_plan = plans.get(tier.value)
                        if lower_plan:
                            savings = current_monthly_cost - Decimal(
                                str(lower_plan["monthly_price"])
                            )
                            if savings > 0:
                                recommendations.append(
                                    CostOptimization(
                                        current_cost=current_monthly_cost,
                                        optimized_cost=Decimal(
                                            str(lower_plan["monthly_price"])
                                        ),
                                        savings=savings,
                                        recommendation=f"Consider downgrading to {lower_plan['name']} tier due to low usage",
                                        confidence=0.7,
                                    )
                                )
                                break

            # Recommend annual billing for savings
            if current_plan["annual_price"] > 0:
                annual_monthly_equivalent = (
                    Decimal(str(current_plan["annual_price"])) / 12
                )
                monthly_savings = current_monthly_cost - annual_monthly_equivalent

                if monthly_savings > 0:
                    recommendations.append(
                        CostOptimization(
                            current_cost=current_monthly_cost,
                            optimized_cost=annual_monthly_equivalent,
                            savings=monthly_savings,
                            recommendation="Switch to annual billing for cost savings",
                            confidence=0.9,
                        )
                    )

            return recommendations

        except Exception as e:
            logger.error(f"Error getting cost optimization recommendations: {e}")
            return []

    async def get_billing_forecast(
        self, user_id: str, current_tier: SubscriptionTier, months: int = 12
    ) -> Dict[str, Any]:
        """Get billing forecast based on usage trends."""
        try:
            # Get usage patterns
            usage_analysis = await self.analyze_usage_patterns(user_id)
            patterns = usage_analysis.get("patterns", {})

            # Get current plan
            plans = self.subscription_service.get_subscription_plans()
            current_plan = plans.get(current_tier.value)

            if not current_plan:
                return {"error": "Invalid subscription tier"}

            monthly_cost = Decimal(str(current_plan["monthly_price"]))

            # Calculate projected costs
            projected_costs = []
            for month in range(1, months + 1):
                # Apply growth rate to estimate future usage
                growth_factor = 1.0
                for pattern in patterns.values():
                    growth_rate = pattern.get("growth_rate", 0)
                    if growth_rate > 0:
                        growth_factor = max(
                            growth_factor, 1 + (growth_rate / 100) * (month / 12)
                        )

                # Estimate if tier upgrade might be needed
                projected_cost = monthly_cost
                if growth_factor > 1.5 and current_tier != SubscriptionTier.ENTERPRISE:
                    # Might need upgrade
                    next_tier_cost = self._get_next_tier_cost(current_tier, plans)
                    if next_tier_cost:
                        projected_cost = next_tier_cost

                projected_costs.append(
                    {
                        "month": month,
                        "projected_cost": float(projected_cost),
                        "growth_factor": growth_factor,
                    }
                )

            total_projected = sum(cost["projected_cost"] for cost in projected_costs)

            return {
                "current_monthly_cost": float(monthly_cost),
                "projected_monthly_costs": projected_costs,
                "total_projected_annual": total_projected,
                "potential_savings_annual": (
                    float(monthly_cost * 12 - total_projected)
                    if total_projected < monthly_cost * 12
                    else 0
                ),
                "forecast_confidence": 0.75,
            }

        except Exception as e:
            logger.error(f"Error generating billing forecast: {e}")
            return {"error": str(e)}

    def _get_next_tier_cost(
        self, current_tier: SubscriptionTier, plans: Dict[str, Any]
    ) -> Optional[Decimal]:
        """Get the cost of the next tier up."""
        tier_order = [
            SubscriptionTier.FREE,
            SubscriptionTier.BASIC,
            SubscriptionTier.PREMIUM,
            SubscriptionTier.ENTERPRISE,
        ]

        try:
            current_index = tier_order.index(current_tier)
            if current_index < len(tier_order) - 1:
                next_tier = tier_order[current_index + 1]
                next_plan = plans.get(next_tier.value)
                if next_plan:
                    return Decimal(str(next_plan["monthly_price"]))
        except (ValueError, IndexError):
            pass

        return None

    async def get_feature_adoption_metrics(self, user_id: str) -> Dict[str, Any]:
        """Get feature adoption metrics for a user."""
        try:
            # Get usage data
            user_data = self.mock_usage_data.get(user_id, {})

            adoption_metrics = {}
            for feature_type in FeatureType:
                feature_data = user_data.get(feature_type, {})
                monthly_total = feature_data.get("monthly_total", 0)
                previous_month = feature_data.get("previous_month", 0)

                adoption_metrics[feature_type.value] = {
                    "current_usage": monthly_total,
                    "previous_usage": previous_month,
                    "adoption_rate": (
                        ((monthly_total - previous_month) / previous_month * 100)
                        if previous_month > 0
                        else 0
                    ),
                    "adoption_status": (
                        "growing"
                        if monthly_total > previous_month
                        else (
                            "stable" if monthly_total == previous_month else "declining"
                        )
                    ),
                }

            return {
                "user_id": user_id,
                "adoption_metrics": adoption_metrics,
                "overall_adoption_trend": self._calculate_overall_trend(
                    adoption_metrics
                ),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting feature adoption metrics: {e}")
            return {"error": str(e)}

    def _calculate_overall_trend(self, adoption_metrics: Dict[str, Any]) -> str:
        """Calculate overall adoption trend."""
        growing_features = sum(
            1
            for metrics in adoption_metrics.values()
            if metrics["adoption_status"] == "growing"
        )
        declining_features = sum(
            1
            for metrics in adoption_metrics.values()
            if metrics["adoption_status"] == "declining"
        )

        if growing_features > declining_features:
            return "growing"
        elif declining_features > growing_features:
            return "declining"
        else:
            return "stable"


# Global service instance
usage_analytics_service = UsageAnalyticsService()
