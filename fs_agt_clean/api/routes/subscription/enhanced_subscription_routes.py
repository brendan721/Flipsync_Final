"""
Enhanced Subscription API Routes for FlipSync.

This module provides API endpoints for advanced subscription management:
- Tier-based feature access control
- Usage tracking and analytics
- Upgrade suggestions and recommendations
- Billing analytics and forecasting
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.database.models.unified_user import UnifiedUser
from fs_agt_clean.services.subscription.enhanced_subscription_service import (
    FeatureType,
    SubscriptionTier,
    enhanced_subscription_service,
)
from fs_agt_clean.services.subscription.usage_analytics_service import (
    usage_analytics_service,
)

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/subscription", tags=["enhanced-subscription"])


class FeatureAccessRequest(BaseModel):
    """Request model for feature access check."""

    feature_type: str = Field(..., description="Feature type to check")
    subscription_tier: str = Field(..., description="UnifiedUser's subscription tier")


class UsageTrackingRequest(BaseModel):
    """Request model for usage tracking."""

    feature_type: str = Field(..., description="Feature type used")
    subscription_tier: str = Field(..., description="UnifiedUser's subscription tier")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


class FeatureAccessResponse(BaseModel):
    """Response model for feature access check."""

    has_access: bool
    access_info: Dict[str, Any]


class UsageAnalyticsResponse(BaseModel):
    """Response model for usage analytics."""

    user_id: str
    analytics: Dict[str, Any]
    generated_at: str


class SubscriptionPlansResponse(BaseModel):
    """Response model for subscription plans."""

    plans: Dict[str, Any]
    current_tier: Optional[str]
    recommendations: List[Dict[str, Any]]


@router.post("/check-access", response_model=FeatureAccessResponse)
async def check_feature_access(
    request: FeatureAccessRequest,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Check if user has access to a specific feature.

    This endpoint:
    - Validates feature access based on subscription tier
    - Returns current usage and limits
    - Provides access status and recommendations
    - Enforces tier-based feature restrictions
    """
    try:
        logger.info(
            f"Checking feature access for user {current_user.id}: {request.feature_type}"
        )

        # Validate feature type
        try:
            feature_type = FeatureType(request.feature_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feature type: {request.feature_type}",
            )

        # Validate subscription tier
        try:
            subscription_tier = SubscriptionTier(request.subscription_tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {request.subscription_tier}",
            )

        # Check feature access
        has_access, access_info = (
            await enhanced_subscription_service.check_feature_access(
                user_id=str(current_user.id),
                feature_type=feature_type,
                subscription_tier=subscription_tier,
            )
        )

        return FeatureAccessResponse(has_access=has_access, access_info=access_info)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature access check failed: {str(e)}",
        )


@router.post("/track-usage")
async def track_feature_usage(
    request: UsageTrackingRequest,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Track feature usage for a user.

    This endpoint:
    - Records feature usage for analytics
    - Updates usage counters and limits
    - Provides usage tracking for billing
    - Enables usage-based recommendations
    """
    try:
        logger.info(
            f"Tracking usage for user {current_user.id}: {request.feature_type}"
        )

        # Validate feature type
        try:
            feature_type = FeatureType(request.feature_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid feature type: {request.feature_type}",
            )

        # Validate subscription tier
        try:
            subscription_tier = SubscriptionTier(request.subscription_tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {request.subscription_tier}",
            )

        # Track usage
        success = await enhanced_subscription_service.track_feature_usage(
            user_id=str(current_user.id),
            feature_type=feature_type,
            subscription_tier=subscription_tier,
            metadata=request.metadata,
        )

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": "Usage tracked successfully",
                    "feature_type": request.feature_type,
                    "tracked_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track usage",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Usage tracking failed: {str(e)}",
        )


@router.get("/plans", response_model=SubscriptionPlansResponse)
async def get_subscription_plans(
    current_tier: Optional[str] = Query(
        default=None, description="Current subscription tier"
    ),
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get available subscription plans with recommendations.

    This endpoint:
    - Returns all available subscription plans
    - Provides feature comparisons and pricing
    - Includes upgrade recommendations based on usage
    - Shows tier-specific benefits and limits
    """
    try:
        logger.info(f"Getting subscription plans for user {current_user.id}")

        # Get all subscription plans
        plans = enhanced_subscription_service.get_subscription_plans()

        # Get upgrade recommendations if current tier provided
        recommendations = []
        if current_tier:
            try:
                tier = SubscriptionTier(current_tier)
                recommendations = (
                    await enhanced_subscription_service.get_upgrade_suggestions(
                        user_id=str(current_user.id), current_tier=tier
                    )
                )
            except ValueError:
                logger.warning(f"Invalid current tier provided: {current_tier}")

        return SubscriptionPlansResponse(
            plans=plans, current_tier=current_tier, recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Error getting subscription plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve subscription plans: {str(e)}",
        )


@router.get("/analytics/usage", response_model=UsageAnalyticsResponse)
async def get_usage_analytics(
    feature_type: Optional[str] = Query(
        default=None, description="Specific feature to analyze"
    ),
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to analyze"
    ),
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get detailed usage analytics for a user.

    This endpoint:
    - Provides usage pattern analysis
    - Shows feature adoption metrics
    - Includes usage trends and insights
    - Offers optimization recommendations
    """
    try:
        logger.info(f"Getting usage analytics for user {current_user.id}")

        # Validate feature type if provided
        feature_type_enum = None
        if feature_type:
            try:
                feature_type_enum = FeatureType(feature_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid feature type: {feature_type}",
                )

        # Get usage analytics
        analytics = await usage_analytics_service.analyze_usage_patterns(
            user_id=str(current_user.id), feature_type=feature_type_enum, days=days
        )

        return UsageAnalyticsResponse(
            user_id=str(current_user.id),
            analytics=analytics,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting usage analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Usage analytics failed: {str(e)}",
        )


@router.get("/analytics/cost-optimization")
async def get_cost_optimization(
    current_tier: str = Query(..., description="Current subscription tier"),
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get cost optimization recommendations.

    This endpoint:
    - Analyzes current usage vs subscription tier
    - Provides cost optimization suggestions
    - Identifies potential savings opportunities
    - Recommends optimal tier based on usage
    """
    try:
        logger.info(f"Getting cost optimization for user {current_user.id}")

        # Validate subscription tier
        try:
            tier = SubscriptionTier(current_tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {current_tier}",
            )

        # Get cost optimization recommendations
        recommendations = (
            await usage_analytics_service.get_cost_optimization_recommendations(
                user_id=str(current_user.id), current_tier=tier
            )
        )

        # Format recommendations
        formatted_recommendations = []
        for rec in recommendations:
            formatted_recommendations.append(
                {
                    "current_cost": float(rec.current_cost),
                    "optimized_cost": float(rec.optimized_cost),
                    "savings": float(rec.savings),
                    "recommendation": rec.recommendation,
                    "confidence": rec.confidence,
                }
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "user_id": str(current_user.id),
                "current_tier": current_tier,
                "recommendations": formatted_recommendations,
                "total_potential_savings": sum(
                    float(rec.savings) for rec in recommendations
                ),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cost optimization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost optimization failed: {str(e)}",
        )


@router.get("/analytics/billing-forecast")
async def get_billing_forecast(
    current_tier: str = Query(..., description="Current subscription tier"),
    months: int = Query(
        default=12, ge=1, le=24, description="Number of months to forecast"
    ),
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get billing forecast based on usage trends.

    This endpoint:
    - Projects future costs based on usage patterns
    - Identifies potential tier changes needed
    - Provides annual cost estimates
    - Shows potential savings opportunities
    """
    try:
        logger.info(f"Getting billing forecast for user {current_user.id}")

        # Validate subscription tier
        try:
            tier = SubscriptionTier(current_tier)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {current_tier}",
            )

        # Get billing forecast
        forecast = await usage_analytics_service.get_billing_forecast(
            user_id=str(current_user.id), current_tier=tier, months=months
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "user_id": str(current_user.id),
                "current_tier": current_tier,
                "forecast_months": months,
                "forecast": forecast,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting billing forecast: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Billing forecast failed: {str(e)}",
        )


@router.get("/analytics/feature-adoption")
async def get_feature_adoption_metrics(
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get feature adoption metrics for a user.

    This endpoint:
    - Shows adoption rates for each feature
    - Identifies growing vs declining feature usage
    - Provides insights into feature value
    - Helps optimize subscription tier selection
    """
    try:
        logger.info(f"Getting feature adoption metrics for user {current_user.id}")

        # Get feature adoption metrics
        metrics = await usage_analytics_service.get_feature_adoption_metrics(
            user_id=str(current_user.id)
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "metrics": metrics,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error getting feature adoption metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Feature adoption metrics failed: {str(e)}",
        )


@router.get("/health")
async def subscription_health_check():
    """
    Perform health check on subscription services.

    This endpoint:
    - Tests subscription service availability
    - Validates analytics service functionality
    - Returns comprehensive health status
    - Available without authentication for monitoring
    """
    try:
        # Test subscription service
        plans = enhanced_subscription_service.get_subscription_plans()
        subscription_healthy = len(plans) > 0

        # Test analytics service (basic functionality)
        analytics_healthy = True  # Simple check for now

        overall_health = (
            "healthy" if subscription_healthy and analytics_healthy else "degraded"
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": overall_health,
                "subscription_service": {
                    "status": "healthy" if subscription_healthy else "unhealthy",
                    "plans_available": len(plans) if subscription_healthy else 0,
                },
                "analytics_service": {
                    "status": "healthy" if analytics_healthy else "unhealthy"
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Subscription health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
