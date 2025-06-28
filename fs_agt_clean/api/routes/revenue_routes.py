"""
Revenue Model API routes for FlipSync.

This module provides API endpoints for revenue tracking and optimization:
- Shipping arbitrage calculations
- Revenue tracking and reporting
- Rewards balance management
- Cost optimization insights
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.database.models.unified_user import UnifiedUser
from fs_agt_clean.database.repositories.ai_analysis_repository import (
    RevenueCalculationRepository,
    RewardsBalanceRepository,
)
from fs_agt_clean.services.shipping_arbitrage import shipping_arbitrage_service

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/revenue", tags=["revenue-model"])

# Initialize repositories
revenue_repository = RevenueCalculationRepository()
rewards_repository = RewardsBalanceRepository()


class ShippingCalculationRequest(BaseModel):
    """Request model for shipping cost calculation."""

    origin_zip: str = Field(..., description="Origin ZIP code")
    destination_zip: str = Field(..., description="Destination ZIP code")
    weight: float = Field(..., gt=0, description="Package weight in pounds")
    package_type: str = Field(
        default="standard", description="Package type: standard, express, overnight"
    )
    current_carrier: Optional[str] = Field(
        default=None, description="Current shipping carrier"
    )
    current_rate: Optional[float] = Field(
        default=None, description="Current shipping rate"
    )


class BulkShippingRequest(BaseModel):
    """Request model for bulk shipping optimization."""

    shipments: List[Dict[str, Any]] = Field(..., description="List of shipment data")
    optimization_criteria: str = Field(
        default="cost", description="Optimization criteria: cost, speed, balance"
    )


class RewardsEarningRequest(BaseModel):
    """Request model for adding rewards earnings."""

    amount: float = Field(..., gt=0, description="Earnings amount")
    source: str = Field(..., description="Source of earnings")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )


@router.post("/shipping/calculate")
async def calculate_shipping_arbitrage(
    request: ShippingCalculationRequest,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Calculate shipping arbitrage opportunities for cost optimization.

    This endpoint:
    - Compares rates across multiple carriers
    - Identifies cost savings opportunities
    - Provides optimization recommendations
    - Tracks savings for revenue calculation
    """
    try:
        # Calculate arbitrage
        arbitrage_result = await shipping_arbitrage_service.calculate_arbitrage(
            origin_zip=request.origin_zip,
            destination_zip=request.destination_zip,
            weight=request.weight,
            package_type=request.package_type,
            current_carrier=request.current_carrier,
            current_rate=request.current_rate,
        )

        # Track savings if applicable
        if (
            request.current_rate
            and "savings" in arbitrage_result
            and arbitrage_result["savings"]
        ):
            savings_data = arbitrage_result["savings"]
            if savings_data["savings_amount"] > 0:
                # Track the savings
                tracking_result = await shipping_arbitrage_service.track_savings(
                    user_id=UUID(str(current_user.id)),
                    original_cost=savings_data["original_rate"],
                    optimized_cost=savings_data["optimized_rate"],
                    optimization_method="carrier_comparison",
                    carrier_recommendations=arbitrage_result.get("carrier_rates", {}),
                    product_id=None,
                )
                arbitrage_result["savings_tracked"] = tracking_result

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "arbitrage_result": arbitrage_result,
                "calculated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error calculating shipping arbitrage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation failed: {str(e)}",
        )


@router.post("/shipping/optimize-bulk")
async def optimize_bulk_shipping(
    request: BulkShippingRequest,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Optimize shipping costs for multiple shipments.

    This endpoint:
    - Processes multiple shipments at once
    - Applies bulk optimization strategies
    - Calculates total cost savings
    - Provides consolidated recommendations
    """
    try:
        # Optimize shipping for all shipments
        optimization_result = await shipping_arbitrage_service.optimize_shipping(
            shipments=request.shipments,
            optimization_criteria=request.optimization_criteria,
        )

        # Track bulk savings if applicable
        summary = optimization_result.get("optimization_summary", {})
        if summary.get("total_savings", 0) > 0:
            tracking_result = await shipping_arbitrage_service.track_savings(
                user_id=UUID(str(current_user.id)),
                original_cost=summary["total_original_cost"],
                optimized_cost=summary["total_optimized_cost"],
                optimization_method=f"bulk_optimization_{request.optimization_criteria}",
                carrier_recommendations={
                    "bulk_optimization": True,
                    "shipment_count": len(request.shipments),
                },
                product_id=None,
            )
            optimization_result["savings_tracked"] = tracking_result

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "optimization_result": optimization_result,
                "optimized_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error optimizing bulk shipping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}",
        )


@router.get("/arbitrage/history")
async def get_arbitrage_history(
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get user's shipping arbitrage history and savings.

    This endpoint returns:
    - Historical arbitrage calculations
    - Total savings achieved
    - Optimization trends
    - Performance metrics
    """
    try:
        # Get user's savings history
        savings_history = await revenue_repository.get_user_savings_history(
            user_id=UUID(str(current_user.id)), limit=limit
        )

        # Calculate total savings
        total_savings = await revenue_repository.get_total_user_savings(
            user_id=UUID(str(current_user.id))
        )

        # Format history data
        history_data = []
        for calculation in savings_history:
            history_data.append(
                {
                    "id": str(calculation.id),
                    "original_cost": float(calculation.original_shipping_cost),
                    "optimized_cost": float(calculation.optimized_shipping_cost),
                    "savings_amount": float(calculation.savings_amount),
                    "savings_percentage": float(calculation.savings_percentage),
                    "optimization_method": calculation.optimization_method,
                    "created_at": calculation.created_at.isoformat(),
                }
            )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "arbitrage_history": {
                    "calculations": history_data,
                    "total_calculations": len(history_data),
                    "total_savings": total_savings,
                    "average_savings": (
                        sum(float(calc.savings_amount) for calc in savings_history)
                        / len(savings_history)
                        if savings_history
                        else 0
                    ),
                },
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving arbitrage history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve history: {str(e)}",
        )


@router.post("/optimization/track")
async def track_optimization_savings(
    original_cost: float = Query(..., gt=0, description="Original cost"),
    optimized_cost: float = Query(..., gt=0, description="Optimized cost"),
    optimization_method: str = Query(..., description="Method used for optimization"),
    product_id: Optional[str] = Query(None, description="Product ID if applicable"),
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Track cost optimization savings for revenue calculation.

    This endpoint:
    - Records optimization savings
    - Updates user's total savings
    - Provides savings analytics
    - Contributes to revenue tracking
    """
    try:
        # Track the savings
        tracking_result = await shipping_arbitrage_service.track_savings(
            user_id=UUID(str(current_user.id)),
            original_cost=original_cost,
            optimized_cost=optimized_cost,
            optimization_method=optimization_method,
            carrier_recommendations={"manual_tracking": True},
            product_id=UUID(product_id) if product_id else None,
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "tracking_result": tracking_result,
                "tracked_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error tracking optimization savings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tracking failed: {str(e)}",
        )


@router.get("/rewards/balance/{user_id}")
async def get_rewards_balance(
    user_id: str, current_user: UnifiedUser = Depends(AuthService.get_current_user)
):
    """
    Get user's rewards balance and earning history.

    This endpoint returns:
    - Current rewards balance
    - Lifetime earnings and redemptions
    - Earning sources breakdown
    - Redemption history
    """
    try:
        # Verify user access (users can only access their own balance or admins can access any)
        if str(current_user.id) != user_id and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Can only view your own rewards balance",
            )

        # Get rewards balance
        balance = await rewards_repository.get_user_balance(UUID(user_id))

        if not balance:
            # Create initial balance record
            balance = await rewards_repository.create_or_update_balance(
                user_id=UUID(user_id),
                current_balance=0.0,
                lifetime_earned=0.0,
                lifetime_redeemed=0.0,
                redemption_history={},
                earning_sources={},
            )

        # Format balance data
        balance_data = {
            "user_id": user_id,
            "current_balance": float(balance.current_balance),
            "lifetime_earned": float(balance.lifetime_earned),
            "lifetime_redeemed": float(balance.lifetime_redeemed),
            "redemption_history": balance.redemption_history or {},
            "earning_sources": balance.earning_sources or {},
            "last_updated": balance.last_updated.isoformat(),
            "created_at": balance.created_at.isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "rewards_balance": balance_data,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving rewards balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve balance: {str(e)}",
        )


@router.post("/rewards/earn")
async def add_rewards_earnings(
    request: RewardsEarningRequest,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Add earnings to user's rewards balance.

    This endpoint:
    - Adds earnings from various sources
    - Updates lifetime earnings
    - Tracks earning sources
    - Provides earning confirmation
    """
    try:
        # Add earnings to user's balance
        updated_balance = await rewards_repository.add_earnings(
            user_id=UUID(str(current_user.id)),
            amount=request.amount,
            source=request.source,
            metadata=request.metadata or {},
        )

        # Format response
        earning_result = {
            "earning_id": str(updated_balance.id),
            "amount_earned": request.amount,
            "source": request.source,
            "new_balance": float(updated_balance.current_balance),
            "lifetime_earned": float(updated_balance.lifetime_earned),
            "earned_at": updated_balance.last_updated.isoformat(),
        }

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "earning_result": earning_result,
                "processed_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error adding rewards earnings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add earnings: {str(e)}",
        )
