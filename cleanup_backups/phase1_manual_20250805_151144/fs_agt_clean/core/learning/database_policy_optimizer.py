"""
Database-Backed Policy Optimizer for FlipSync Agentic System
Phase 3 Step 3: Learning Data Database Persistence

This module extends the existing PolicyOptimizer with database persistence,
storing optimization history, strategy evolution, and performance metrics
in PostgreSQL for learning continuity across agent restarts.
"""

import logging
import time
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, select

from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.learning.database.models import (
    PolicyOptimizationHistory,
    PolicyStrategyEvolution,
    LearningPerformanceMetrics,
)
from fs_agt_clean.core.learning.policy_optimization import (
    PolicyOptimizer,
    OptimizationObjective,
    OptimizationAlgorithm,
)

logger = logging.getLogger(__name__)


class DatabasePolicyOptimizer(PolicyOptimizer):
    """Database-backed PolicyOptimizer with persistent learning storage.

    This class extends the existing PolicyOptimizer to add:
    - Persistent optimization history storage
    - Strategy evolution tracking
    - Performance metrics persistence
    - Learning recovery across agent restarts
    """

    def __init__(
        self,
        config: Dict[str, Any],
        agent_id: str,
        database: Database,
        agent_type: str = "unknown",
    ):
        """Initialize the database-backed policy optimizer.

        Args:
            config: Optimization configuration
            agent_id: Unique identifier for the agent
            database: Database instance for persistence
            agent_type: Type of agent (market, executive, content, logistics)
        """
        super().__init__(config)
        self.agent_id = agent_id
        self.database = database
        self.agent_type = agent_type

        # Performance tracking
        self.optimization_history: List[Dict[str, Any]] = []
        self.strategy_cache: Dict[str, Dict[str, Any]] = {}

        logger.info(
            f"Initialized DatabasePolicyOptimizer for {agent_id} ({agent_type})"
        )

    async def initialize(self) -> bool:
        """Initialize the database-backed policy optimizer.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Create database tables if they don't exist
            await self._ensure_tables_exist()

            # Load existing optimization history
            await self._load_optimization_history()

            # Load strategy cache
            await self._load_strategy_cache()

            logger.info(f"✅ DatabasePolicyOptimizer initialized for {self.agent_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize DatabasePolicyOptimizer: {e}")
            return False

    async def optimize_policy(
        self,
        current_policy: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        objective: OptimizationObjective,
        algorithm: OptimizationAlgorithm = OptimizationAlgorithm.GRADIENT_DESCENT,
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Optimize policy with database persistence.

        Args:
            current_policy: Current policy configuration
            performance_metrics: Performance metrics for optimization
            objective: Optimization objective
            constraints: Optional constraints on optimization

        Returns:
            Optimized policy configuration
        """
        start_time = time.time()
        optimization_id = str(uuid.uuid4())

        try:
            # Call parent optimization method
            optimized_policy = super().optimize_policy(
                current_policy, performance_metrics, objective, algorithm, constraints
            )

            # Calculate improvement metrics
            improvement_score = await self._calculate_improvement_score(
                current_policy, optimized_policy, performance_metrics
            )

            confidence_score = await self._calculate_confidence_score(
                optimized_policy, performance_metrics
            )

            # Store optimization history in database
            await self._store_optimization_history(
                optimization_id=optimization_id,
                current_policy=current_policy,
                optimized_policy=optimized_policy,
                objective=objective,
                performance_metrics=performance_metrics,
                improvement_score=improvement_score,
                confidence_score=confidence_score,
                processing_time=time.time() - start_time,
            )

            # Update strategy evolution if significant improvement
            if improvement_score > 0.1:  # 10% improvement threshold
                await self._update_strategy_evolution(
                    optimized_policy, improvement_score, performance_metrics
                )

            # Update performance metrics
            await self._update_performance_metrics(
                "optimization_improvement", improvement_score, performance_metrics
            )

            logger.debug(
                f"Policy optimization completed for {self.agent_id}: {improvement_score:.3f} improvement"
            )
            return optimized_policy

        except Exception as e:
            logger.error(f"Policy optimization failed for {self.agent_id}: {e}")
            # Return current policy as fallback
            return current_policy

    async def process_feedback(self, feedback: Dict[str, Any]) -> None:
        """Process decision feedback for policy optimization.

        Args:
            feedback: Decision feedback containing success metrics and performance data
        """
        try:
            decision_id = feedback.get("decision_id")
            success = feedback.get("success", False)
            decision_time = feedback.get("decision_time", 0.0)
            performance_metrics = feedback.get("performance_metrics", {})

            # Store performance metrics in database
            await self._update_performance_metrics(
                metric_type="decision_success",
                metric_value=1.0 if success else 0.0,
                context={
                    "decision_id": decision_id,
                    "decision_time": decision_time,
                    "agent_id": self.agent_id,
                },
            )

            await self._update_performance_metrics(
                metric_type="decision_time",
                metric_value=decision_time,
                context={
                    "decision_id": decision_id,
                    "success": success,
                    "agent_id": self.agent_id,
                },
            )

            # Update strategy evolution based on feedback
            if performance_metrics:
                improvement_score = self._calculate_feedback_improvement_score(
                    success, decision_time, performance_metrics
                )

                await self._update_strategy_evolution(
                    optimized_policy={"feedback_based": True},
                    improvement_score=improvement_score,
                    performance_metrics=performance_metrics,
                )

            logger.debug(
                f"Processed feedback for decision {decision_id}: success={success}, time={decision_time}s"
            )

        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")

    def _calculate_feedback_improvement_score(
        self, success: bool, decision_time: float, performance_metrics: Dict[str, Any]
    ) -> float:
        """Calculate improvement score from decision feedback."""
        try:
            # Base score on success
            base_score = 0.8 if success else 0.2

            # Adjust for decision time (target <0.5s)
            time_penalty = max(0.0, min(0.3, (decision_time - 0.5) * 0.1))
            time_score = base_score - time_penalty

            # Factor in performance metrics
            accuracy = performance_metrics.get("accuracy", 0.5)
            efficiency = performance_metrics.get("efficiency", 0.5)

            final_score = (time_score * 0.4) + (accuracy * 0.3) + (efficiency * 0.3)
            return max(0.0, min(1.0, final_score))

        except Exception:
            return 0.5  # Default neutral score

    async def get_optimization_history(
        self, limit: int = 50, objective: Optional[OptimizationObjective] = None
    ) -> List[Dict[str, Any]]:
        """Get optimization history from database.

        Args:
            limit: Maximum number of records to return
            objective: Optional filter by optimization objective

        Returns:
            List of optimization history records
        """
        try:
            async with self.database.get_session() as session:
                query = (
                    select(PolicyOptimizationHistory)
                    .where(PolicyOptimizationHistory.agent_id == self.agent_id)
                    .order_by(desc(PolicyOptimizationHistory.created_at))
                    .limit(limit)
                )

                if objective:
                    query = query.where(
                        PolicyOptimizationHistory.optimization_objective
                        == objective.value
                    )

                result = await session.execute(query)
                records = result.scalars().all()

                return [
                    {
                        "optimization_id": str(record.optimization_id),
                        "current_policy": record.current_policy,
                        "optimized_policy": record.optimized_policy,
                        "objective": record.optimization_objective,
                        "algorithm": record.optimization_algorithm,
                        "performance_metrics": record.performance_metrics,
                        "improvement_score": float(record.improvement_score),
                        "confidence_score": float(record.confidence_score),
                        "created_at": record.created_at.isoformat(),
                    }
                    for record in records
                ]

        except Exception as e:
            logger.error(f"Failed to get optimization history: {e}")
            return []

    async def get_strategy_evolution(self, strategy_name: str) -> List[Dict[str, Any]]:
        """Get strategy evolution history from database.

        Args:
            strategy_name: Name of the strategy to track

        Returns:
            List of strategy evolution records
        """
        try:
            async with self.database.get_session() as session:
                query = (
                    select(PolicyStrategyEvolution)
                    .where(
                        and_(
                            PolicyStrategyEvolution.agent_id == self.agent_id,
                            PolicyStrategyEvolution.strategy_name == strategy_name,
                        )
                    )
                    .order_by(PolicyStrategyEvolution.strategy_version)
                )

                result = await session.execute(query)
                records = result.scalars().all()

                return [
                    {
                        "strategy_id": str(record.strategy_id),
                        "strategy_name": record.strategy_name,
                        "strategy_parameters": record.strategy_parameters,
                        "strategy_version": record.strategy_version,
                        "success_rate": float(record.success_rate),
                        "average_performance": float(record.average_performance),
                        "usage_count": record.usage_count,
                        "evolution_reason": record.evolution_reason,
                        "created_at": record.created_at.isoformat(),
                    }
                    for record in records
                ]

        except Exception as e:
            logger.error(f"Failed to get strategy evolution: {e}")
            return []

    async def _ensure_tables_exist(self):
        """Ensure database tables exist for policy optimization."""
        try:
            # Tables are created by the database initialization
            # This method can be extended for additional table checks
            pass
        except Exception as e:
            logger.error(f"Failed to ensure tables exist: {e}")
            raise

    async def _load_optimization_history(self):
        """Load recent optimization history for performance tracking."""
        try:
            recent_history = await self.get_optimization_history(limit=20)
            self.optimization_history = recent_history
            logger.debug(
                f"Loaded {len(recent_history)} optimization records for {self.agent_id}"
            )
        except Exception as e:
            logger.error(f"Failed to load optimization history: {e}")

    async def _load_strategy_cache(self):
        """Load strategy cache from database."""
        try:
            async with self.database.get_session() as session:
                query = (
                    select(PolicyStrategyEvolution)
                    .where(PolicyStrategyEvolution.agent_id == self.agent_id)
                    .order_by(desc(PolicyStrategyEvolution.created_at))
                    .limit(10)
                )

                result = await session.execute(query)
                records = result.scalars().all()

                for record in records:
                    self.strategy_cache[record.strategy_name] = {
                        "parameters": record.strategy_parameters,
                        "success_rate": float(record.success_rate),
                        "performance": float(record.average_performance),
                        "version": record.strategy_version,
                    }

                logger.debug(
                    f"Loaded {len(self.strategy_cache)} strategies for {self.agent_id}"
                )

        except Exception as e:
            logger.error(f"Failed to load strategy cache: {e}")

    async def _store_optimization_history(
        self,
        optimization_id: str,
        current_policy: Dict[str, Any],
        optimized_policy: Dict[str, Any],
        objective: OptimizationObjective,
        performance_metrics: Dict[str, Any],
        improvement_score: float,
        confidence_score: float,
        processing_time: float,
    ):
        """Store optimization history in database."""
        try:
            async with self.database.get_session() as session:
                record = PolicyOptimizationHistory(
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    optimization_id=optimization_id,  # Keep as string
                    current_policy=current_policy,
                    optimized_policy=optimized_policy,
                    optimization_objective=objective.value,
                    optimization_algorithm=str(
                        self.config.get("algorithm", "gradient_descent")
                    ),
                    performance_metrics={
                        **performance_metrics,
                        "processing_time_seconds": processing_time,
                    },
                    improvement_score=improvement_score,
                    confidence_score=confidence_score,
                    learning_rate=self.config.get("learning_rate", 0.01),
                    iteration_count=1,
                    convergence_status="completed",
                )

                session.add(record)
                await session.commit()

                logger.debug(f"Stored optimization history: {optimization_id}")

        except Exception as e:
            logger.error(f"Failed to store optimization history: {e}")

    async def _update_strategy_evolution(
        self,
        optimized_policy: Dict[str, Any],
        improvement_score: float,
        performance_metrics: Dict[str, Any],
    ):
        """Update strategy evolution tracking."""
        try:
            strategy_name = optimized_policy.get("strategy_name", "default_strategy")

            async with self.database.get_session() as session:
                # Get latest version of this strategy
                query = (
                    select(PolicyStrategyEvolution)
                    .where(
                        and_(
                            PolicyStrategyEvolution.agent_id == self.agent_id,
                            PolicyStrategyEvolution.strategy_name == strategy_name,
                        )
                    )
                    .order_by(desc(PolicyStrategyEvolution.strategy_version))
                    .limit(1)
                )

                result = await session.execute(query)
                latest_strategy = result.scalar_one_or_none()

                new_version = (
                    (latest_strategy.strategy_version + 1) if latest_strategy else 1
                )

                # Create new strategy evolution record
                evolution_record = PolicyStrategyEvolution(
                    agent_id=self.agent_id,
                    strategy_name=strategy_name,
                    strategy_parameters=optimized_policy,
                    strategy_version=new_version,
                    success_rate=performance_metrics.get("success_rate", 0.0),
                    average_performance=performance_metrics.get(
                        "average_performance", 0.0
                    ),
                    usage_count=1,
                    parent_strategy_id=(
                        latest_strategy.strategy_id if latest_strategy else None
                    ),
                    evolution_reason=f"Optimization improvement: {improvement_score:.3f}",
                )

                session.add(evolution_record)
                await session.commit()

                logger.debug(
                    f"Updated strategy evolution: {strategy_name} v{new_version}"
                )

        except Exception as e:
            logger.error(f"Failed to update strategy evolution: {e}")

    async def _update_performance_metrics(
        self, metric_type: str, metric_value: float, context: Dict[str, Any]
    ):
        """Update performance metrics in database."""
        try:
            async with self.database.get_session() as session:
                metric_record = LearningPerformanceMetrics(
                    agent_id=self.agent_id,
                    metric_type=metric_type,
                    metric_value=metric_value,
                    baseline_value=context.get("baseline", 0.0),
                    improvement_percentage=(
                        (metric_value - context.get("baseline", 0.0))
                        / max(context.get("baseline", 0.1), 0.1)
                    )
                    * 100,
                    measurement_context=context,
                    measurement_period="optimization",
                )

                session.add(metric_record)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")

    async def _calculate_improvement_score(
        self,
        current_policy: Dict[str, Any],
        optimized_policy: Dict[str, Any],
        performance_metrics: Dict[str, Any],
    ) -> float:
        """Calculate improvement score for optimization."""
        try:
            # Simple improvement calculation based on performance metrics
            current_performance = performance_metrics.get("current_performance", 0.5)
            expected_performance = performance_metrics.get(
                "expected_performance", current_performance
            )

            improvement = (expected_performance - current_performance) / max(
                current_performance, 0.1
            )
            return max(0.0, min(1.0, improvement))  # Clamp between 0 and 1

        except Exception:
            return 0.0

    async def _calculate_confidence_score(
        self, optimized_policy: Dict[str, Any], performance_metrics: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for optimization."""
        try:
            # Base confidence on data quality and historical performance
            data_quality = performance_metrics.get("data_quality", 0.5)
            historical_accuracy = performance_metrics.get("historical_accuracy", 0.5)

            confidence = (data_quality + historical_accuracy) / 2.0
            return max(0.0, min(1.0, confidence))  # Clamp between 0 and 1

        except Exception:
            return 0.5
