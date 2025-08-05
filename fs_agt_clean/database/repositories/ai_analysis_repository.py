"""
Repository for AI analysis data operations.

This module provides data access methods for:
- AI analysis results
- AutonomousAgent coordination logs
- Revenue calculations
- Category optimization results
- UnifiedUser rewards balance
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID


from fs_agt_clean.database.base_repository import BaseRepository
from fs_agt_clean.database.models.ai_analysis import (
    AIAnalysisResult,
    CategoryOptimizationResult,
    FeatureUsageTracking,
    ShippingArbitrageCalculation,
    AutonomousAgentCoordinationLog,
    UnifiedUserRewardsBalance,
)

logger = logging.getLogger(__name__)


class AIAnalysisRepository(BaseRepository[AIAnalysisResult]):
    """Repository for AI analysis results."""

    def __init__(self):
        super().__init__(AIAnalysisResult, "ai_analysis_results")

    async def create_analysis_result(
        self,
        user_id: UUID,
        product_name: str,
        category: str,
        description: str,
        confidence_score: float,
        analysis_data: Dict[str, Any],
        pricing_suggestions: Dict[str, Any],
        marketplace_recommendations: Dict[str, Any],
        processing_time_ms: int,
        ai_service_used: str,
        image_hash: Optional[str] = None,
    ) -> AIAnalysisResult:
        """Create a new AI analysis result."""
        data = {
            "user_id": user_id,
            "product_name": product_name,
            "category": category,
            "description": description,
            "confidence_score": confidence_score,
            "analysis_data": analysis_data,
            "pricing_suggestions": pricing_suggestions,
            "marketplace_recommendations": marketplace_recommendations,
            "processing_time_ms": processing_time_ms,
            "ai_service_used": ai_service_used,
            "image_hash": image_hash,
        }
        return await self.create(data)

    async def get_user_analysis_history(
        self, user_id: UUID, limit: int = 10, offset: int = 0
    ) -> List[AIAnalysisResult]:
        """Get analysis history for a user."""
        criteria = {"user_id": user_id}
        return await self.find_many(
            criteria, limit=limit, offset=offset, order_by="created_at DESC"
        )

    async def get_by_image_hash(self, image_hash: str) -> Optional[AIAnalysisResult]:
        """Get analysis result by image hash for caching."""
        criteria = {"image_hash": image_hash}
        results = await self.find_many(criteria, limit=1)
        return results[0] if results else None


class AutonomousAgentCoordinationRepository(BaseRepository[AutonomousAgentCoordinationLog]):
    """Repository for agent coordination logs."""

    def __init__(self):
        super().__init__(AutonomousAgentCoordinationLog, "agent_coordination_logs")

    async def log_coordination_activity(
        self,
        participating_agents: List[str],
        coordination_type: str,
        status: str,
        result_data: Dict[str, Any],
        processing_time_ms: int,
        workflow_id: Optional[UUID] = None,
    ) -> AutonomousAgentCoordinationLog:
        """Log an agent coordination activity."""
        data = {
            "workflow_id": workflow_id,
            "participating_agents": participating_agents,
            "coordination_type": coordination_type,
            "status": status,
            "result_data": result_data,
            "processing_time_ms": processing_time_ms,
        }
        return await self.create(data)

    async def get_coordination_history(
        self, coordination_type: Optional[str] = None, limit: int = 50
    ) -> List[AutonomousAgentCoordinationLog]:
        """Get coordination history, optionally filtered by type."""
        criteria = {}
        if coordination_type:
            criteria["coordination_type"] = coordination_type
        return await self.find_many(criteria, limit=limit, order_by="created_at DESC")


class RevenueCalculationRepository(BaseRepository[ShippingArbitrageCalculation]):
    """Repository for shipping arbitrage calculations."""

    def __init__(self):
        super().__init__(
            ShippingArbitrageCalculation, "shipping_arbitrage_calculations"
        )

    async def create_arbitrage_calculation(
        self,
        user_id: UUID,
        original_shipping_cost: float,
        optimized_shipping_cost: float,
        savings_amount: float,
        savings_percentage: float,
        optimization_method: str,
        carrier_recommendations: Dict[str, Any],
        product_id: Optional[UUID] = None,
    ) -> ShippingArbitrageCalculation:
        """Create a new shipping arbitrage calculation."""
        data = {
            "user_id": user_id,
            "product_id": product_id,
            "original_shipping_cost": original_shipping_cost,
            "optimized_shipping_cost": optimized_shipping_cost,
            "savings_amount": savings_amount,
            "savings_percentage": savings_percentage,
            "optimization_method": optimization_method,
            "carrier_recommendations": carrier_recommendations,
        }
        return await self.create(data)

    async def get_user_savings_history(
        self, user_id: UUID, limit: int = 20
    ) -> List[ShippingArbitrageCalculation]:
        """Get savings history for a user."""
        criteria = {"user_id": user_id}
        return await self.find_many(criteria, limit=limit, order_by="created_at DESC")

    async def get_total_user_savings(self, user_id: UUID) -> float:
        """Get total savings amount for a user from shipping arbitrage calculations."""
        try:
            from sqlalchemy import func, select
            from fs_agt_clean.database.models.ai_analysis import (
                ShippingArbitrageCalculation,
            )

            # Query to sum all savings from shipping arbitrage calculations
            query = select(
                func.coalesce(
                    func.sum(ShippingArbitrageCalculation.savings_amount), 0.0
                )
            ).where(ShippingArbitrageCalculation.user_id == user_id)

            result = await self.session.execute(query)
            total_savings = result.scalar()
            return float(total_savings) if total_savings else 0.0

        except Exception as e:
            logger.error(f"Error calculating total user savings for {user_id}: {e}")
            return 0.0


class CategoryOptimizationRepository(BaseRepository[CategoryOptimizationResult]):
    """Repository for category optimization results."""

    def __init__(self):
        super().__init__(CategoryOptimizationResult, "category_optimization_results")

    async def create_optimization_result(
        self,
        user_id: UUID,
        original_category: str,
        optimized_category: str,
        confidence_score: float,
        marketplace: str,
        category_path: Dict[str, Any],
        performance_improvement: Optional[float] = None,
        product_id: Optional[UUID] = None,
    ) -> CategoryOptimizationResult:
        """Create a new category optimization result."""
        data = {
            "user_id": user_id,
            "product_id": product_id,
            "original_category": original_category,
            "optimized_category": optimized_category,
            "confidence_score": confidence_score,
            "performance_improvement": performance_improvement,
            "marketplace": marketplace,
            "category_path": category_path,
        }
        return await self.create(data)


class RewardsBalanceRepository(BaseRepository[UnifiedUserRewardsBalance]):
    """Repository for user rewards balance."""

    def __init__(self):
        super().__init__(UnifiedUserRewardsBalance, "user_rewards_balance")

    async def get_user_balance(
        self, user_id: UUID
    ) -> Optional[UnifiedUserRewardsBalance]:
        """Get rewards balance for a user."""
        criteria = {"user_id": user_id}
        results = await self.find_many(criteria, limit=1)
        return results[0] if results else None

    async def create_or_update_balance(
        self,
        user_id: UUID,
        current_balance: float,
        lifetime_earned: float,
        lifetime_redeemed: float,
        redemption_history: Dict[str, Any],
        earning_sources: Dict[str, Any],
    ) -> UnifiedUserRewardsBalance:
        """Create or update user rewards balance."""
        existing = await self.get_user_balance(user_id)

        if existing:
            # Update existing record
            update_data = {
                "current_balance": current_balance,
                "lifetime_earned": lifetime_earned,
                "lifetime_redeemed": lifetime_redeemed,
                "redemption_history": redemption_history,
                "earning_sources": earning_sources,
            }
            return await self.update(existing.id, update_data)
        else:
            # Create new record
            data = {
                "user_id": user_id,
                "current_balance": current_balance,
                "lifetime_earned": lifetime_earned,
                "lifetime_redeemed": lifetime_redeemed,
                "redemption_history": redemption_history,
                "earning_sources": earning_sources,
            }
            return await self.create(data)

    async def add_earnings(
        self, user_id: UUID, amount: float, source: str, metadata: Dict[str, Any]
    ) -> UnifiedUserRewardsBalance:
        """Add earnings to user's rewards balance."""
        balance = await self.get_user_balance(user_id)

        if not balance:
            # Create new balance record
            earning_sources = {
                source: [
                    {
                        "amount": amount,
                        "metadata": metadata,
                        "date": datetime.now(timezone.utc).isoformat(),
                    }
                ]
            }
            return await self.create_or_update_balance(
                user_id=user_id,
                current_balance=amount,
                lifetime_earned=amount,
                lifetime_redeemed=0.0,
                redemption_history={},
                earning_sources=earning_sources,
            )
        else:
            # Update existing balance
            new_balance = float(balance.current_balance) + amount
            new_lifetime = float(balance.lifetime_earned) + amount

            # Update earning sources
            earning_sources = balance.earning_sources or {}
            if source not in earning_sources:
                earning_sources[source] = []
            earning_sources[source].append(
                {
                    "amount": amount,
                    "metadata": metadata,
                    "date": datetime.now(timezone.utc).isoformat(),
                }
            )

            return await self.create_or_update_balance(
                user_id=user_id,
                current_balance=new_balance,
                lifetime_earned=new_lifetime,
                lifetime_redeemed=float(balance.lifetime_redeemed),
                redemption_history=balance.redemption_history or {},
                earning_sources=earning_sources,
            )


class FeatureUsageRepository(BaseRepository[FeatureUsageTracking]):
    """Repository for feature usage tracking."""

    def __init__(self):
        super().__init__(FeatureUsageTracking, "feature_usage_tracking")

    async def track_usage(
        self,
        user_id: UUID,
        feature_name: str,
        subscription_tier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeatureUsageTracking:
        """Track feature usage for a user."""
        data = {
            "user_id": user_id,
            "feature_name": feature_name,
            "usage_count": 1,
            "subscription_tier": subscription_tier,
            "metadata": metadata,
            "usage_date": datetime.now(timezone.utc),
        }
        return await self.create(data)

    async def get_user_usage_stats(
        self,
        user_id: UUID,
        feature_name: Optional[str] = None,
        start_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get usage statistics for a user from feature usage tracking."""
        try:
            from sqlalchemy import func, select
            from fs_agt_clean.database.models.ai_analysis import FeatureUsageTracking

            # Base query for user's feature usage
            base_query = select(FeatureUsageTracking).where(
                FeatureUsageTracking.user_id == user_id
            )

            if start_date:
                base_query = base_query.where(
                    FeatureUsageTracking.created_at >= start_date
                )

            # Get total usage count
            total_query = select(func.count(FeatureUsageTracking.id)).where(
                FeatureUsageTracking.user_id == user_id
            )
            if start_date:
                total_query = total_query.where(
                    FeatureUsageTracking.created_at >= start_date
                )

            # Get usage by feature
            feature_query = (
                select(
                    FeatureUsageTracking.feature_name,
                    func.count(FeatureUsageTracking.id).label("usage_count"),
                )
                .where(FeatureUsageTracking.user_id == user_id)
                .group_by(FeatureUsageTracking.feature_name)
            )

            if start_date:
                feature_query = feature_query.where(
                    FeatureUsageTracking.created_at >= start_date
                )

            # Execute queries
            total_result = await self.session.execute(total_query)
            total_usage = total_result.scalar() or 0

            feature_result = await self.session.execute(feature_query)
            feature_data = feature_result.fetchall()

            # Build response
            features_used = [row[0] for row in feature_data]
            usage_by_feature = {row[0]: row[1] for row in feature_data}

            return {
                "total_usage": total_usage,
                "features_used": features_used,
                "usage_by_feature": usage_by_feature,
            }

        except Exception as e:
            logger.error(f"Error getting usage statistics for {user_id}: {e}")
            return {"total_usage": 0, "features_used": [], "usage_by_feature": {}}

    async def get_agent_performance_aggregates(
        self, agent_type: str, time_range_hours: int = 24
    ) -> Dict[str, Any]:
        """Get agent performance aggregation metrics for 4+1 architecture monitoring."""
        try:
            from sqlalchemy import func, select
            from fs_agt_clean.database.models.autonomous_agent import (
                AutonomousAgentDecision,
            )
            from datetime import datetime, timedelta, timezone

            # Calculate time range
            start_time = datetime.now(timezone.utc) - timedelta(hours=time_range_hours)

            # Query for agent performance metrics
            query = (
                select(
                    func.count(AutonomousAgentDecision.id).label("total_decisions"),
                    func.avg(AutonomousAgentDecision.execution_time_ms).label(
                        "avg_decision_time"
                    ),
                    func.max(AutonomousAgentDecision.execution_time_ms).label(
                        "max_decision_time"
                    ),
                    func.min(AutonomousAgentDecision.execution_time_ms).label(
                        "min_decision_time"
                    ),
                    func.avg(AutonomousAgentDecision.confidence).label(
                        "avg_confidence"
                    ),
                    func.count(
                        func.case((AutonomousAgentDecision.status == "completed", 1))
                    ).label("successful_decisions"),
                    func.count(
                        func.case((AutonomousAgentDecision.execution_time_ms < 1000, 1))
                    ).label("sub_1000ms_decisions"),
                )
                .where(AutonomousAgentDecision.agent_id.like(f"%{agent_type}%"))
                .where(AutonomousAgentDecision.started_at >= start_time)
            )

            result = await self.session.execute(query)
            row = result.fetchone()

            if row:
                total_decisions = row[0] or 0
                success_rate = (
                    (row[5] / total_decisions * 100) if total_decisions > 0 else 0
                )
                performance_compliance = (
                    (row[6] / total_decisions * 100) if total_decisions > 0 else 0
                )

                return {
                    "agent_type": agent_type,
                    "time_range_hours": time_range_hours,
                    "total_decisions": total_decisions,
                    "avg_decision_time_ms": float(row[1]) if row[1] else 0.0,
                    "max_decision_time_ms": float(row[2]) if row[2] else 0.0,
                    "min_decision_time_ms": float(row[3]) if row[3] else 0.0,
                    "avg_confidence": float(row[4]) if row[4] else 0.0,
                    "successful_decisions": row[5] or 0,
                    "success_rate_percent": round(success_rate, 2),
                    "sub_1000ms_decisions": row[6] or 0,
                    "performance_compliance_percent": round(performance_compliance, 2),
                    "architecture_compliant": performance_compliance
                    >= 95.0,  # 95% of decisions should be <1000ms
                }
            else:
                return {
                    "agent_type": agent_type,
                    "time_range_hours": time_range_hours,
                    "total_decisions": 0,
                    "avg_decision_time_ms": 0.0,
                    "architecture_compliant": False,
                }

        except Exception as e:
            logger.error(
                f"Error getting agent performance aggregates for {agent_type}: {e}"
            )
            return {
                "agent_type": agent_type,
                "time_range_hours": time_range_hours,
                "total_decisions": 0,
                "error": str(e),
            }
