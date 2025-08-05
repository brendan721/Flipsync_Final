"""
Database-backed Learning Engine for FlipSync Agentic System

This module provides a production-ready database-backed implementation of the
LearningEngine interface, storing all learning data in PostgreSQL for
persistence across agent restarts and enabling cross-agent learning sharing.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import text

from fs_agt_clean.core.coordination.decision.learning_engine import BaseLearningEngine
from fs_agt_clean.core.coordination.decision.models import DecisionError
from fs_agt_clean.core.coordination.event_system import (
    EventPublisher,
    NotificationEvent,
)
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class DatabaseLearningEngine(BaseLearningEngine):
    """Database-backed implementation of LearningEngine.

    This implementation stores all learning data in PostgreSQL, providing:
    - Persistent learning data across agent restarts
    - Cross-agent learning data sharing and insights
    - Transaction-safe learning data updates
    - Performance optimized learning analytics
    """

    def __init__(self, engine_id: str, publisher: EventPublisher, database: Database):
        """Initialize the database learning engine.

        Args:
            engine_id: Unique identifier for this engine
            publisher: Event publisher for publishing learning events
            database: Database instance for persistence operations
        """
        super().__init__(engine_id, publisher)
        self.database = database
        self._metrics_cache: Dict[str, Any] = {}
        # PERFORMANCE OPTIMIZATION: Cache confidence adjustments
        self._confidence_cache: Dict[str, tuple] = (
            {}
        )  # {decision_type: (adjustment, timestamp)}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 300  # Cache metrics for 5 minutes
        logger.info(f"Initialized DatabaseLearningEngine {engine_id}")

    async def learn_from_feedback(
        self,
        feedback_data: Dict[str, Any],
        publish_event: bool = True,
        battery_efficient: bool = False,
    ) -> bool:
        """Learn from feedback on decision outcomes.

        Args:
            feedback_data: Feedback data containing decision outcomes and performance metrics
            publish_event: Whether to publish an event about the learning
            battery_efficient: Whether to use battery-efficient learning

        Returns:
            True if learning was successful, False otherwise

        Raises:
            DecisionError: If there is an error learning from feedback
        """
        try:
            # Check if database is initialized
            if (
                not self.database
                or not hasattr(self.database, "_session_factory")
                or not self.database._session_factory
            ):
                logger.error("Failed to learn from feedback: Database not initialized")
                return False

            # Validate feedback data
            if not feedback_data or not isinstance(feedback_data, dict):
                logger.warning("Invalid feedback data provided for learning")
                return False

            # Extract learning information
            decision_id = feedback_data.get("decision_id")
            feedback_data.get("quality", 0.5)
            feedback_data.get("outcome", "unknown")
            feedback_data.get("execution_time", 0.0)

            # Store learning data in database
            await self._store_learning_data(feedback_data)

            # Update learning metrics
            await self._update_learning_metrics(feedback_data)

            # Publish learning event (only if publish_event is True)
            if publish_event:
                await self._publish_learning_event(feedback_data)

            # Invalidate metrics cache
            self._invalidate_metrics_cache()

            logger.debug(f"Learning completed from feedback for decision {decision_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to learn from feedback: {e}")
            raise DecisionError(
                f"Failed to learn from feedback: {str(e)}",
                error_code="LEARNING_FAILED",
                details={"engine_id": self.engine_id, "feedback_data": feedback_data},
            )

    async def get_learning_metrics(self) -> Dict[str, Any]:
        """Get metrics on learning.

        Returns:
            Dictionary of learning metrics

        Raises:
            DecisionError: If there is an error getting metrics
        """
        try:
            # Check cache first
            if self._is_metrics_cache_valid():
                logger.debug("Returning cached learning metrics")
                return self._metrics_cache.copy()

            async with self.database.get_session() as session:
                # Get total learning records
                result = await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM agent_learning_data 
                        WHERE agent_id LIKE :engine_pattern
                    """
                    ),
                    {"engine_pattern": f"%{self.engine_id.split('_')[0]}%"},
                )
                total_learning_records = result.scalar()

                # Get learning by type
                result = await session.execute(
                    text(
                        """
                        SELECT learning_type, COUNT(*) as count
                        FROM agent_learning_data 
                        WHERE agent_id LIKE :engine_pattern
                        GROUP BY learning_type
                    """
                    ),
                    {"engine_pattern": f"%{self.engine_id.split('_')[0]}%"},
                )
                learning_by_type = {row[0]: row[1] for row in result.fetchall()}

                # Get average performance score
                result = await session.execute(
                    text(
                        """
                        SELECT AVG(performance_score) FROM agent_learning_data 
                        WHERE agent_id LIKE :engine_pattern
                        AND performance_score IS NOT NULL
                    """
                    ),
                    {"engine_pattern": f"%{self.engine_id.split('_')[0]}%"},
                )
                avg_performance = result.scalar() or 0.0

                # Get recent learning activity (last 24 hours)
                result = await session.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM agent_learning_data 
                        WHERE agent_id LIKE :engine_pattern
                        AND created_at >= NOW() - INTERVAL '24 hours'
                    """
                    ),
                    {"engine_pattern": f"%{self.engine_id.split('_')[0]}%"},
                )
                recent_learning = result.scalar()

                # Get learning trend (last 7 days)
                result = await session.execute(
                    text(
                        """
                        SELECT DATE(created_at) as learning_date, COUNT(*) as count
                        FROM agent_learning_data 
                        WHERE agent_id LIKE :engine_pattern
                        AND created_at >= NOW() - INTERVAL '7 days'
                        GROUP BY DATE(created_at)
                        ORDER BY learning_date
                    """
                    ),
                    {"engine_pattern": f"%{self.engine_id.split('_')[0]}%"},
                )
                learning_trend = {str(row[0]): row[1] for row in result.fetchall()}

                metrics = {
                    "total_learning_records": total_learning_records,
                    "learning_by_type": learning_by_type,
                    "average_performance_score": float(avg_performance),
                    "recent_learning_24h": recent_learning,
                    "learning_trend_7d": learning_trend,
                    "engine_id": self.engine_id,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "cache_ttl_seconds": self._cache_ttl_seconds,
                }

                # Cache the metrics
                self._metrics_cache = metrics.copy()
                self._cache_timestamp = datetime.now(timezone.utc)

                logger.debug(
                    f"Generated learning metrics: {total_learning_records} total records"
                )
                return metrics

        except Exception as e:
            logger.error(f"Failed to get learning metrics: {e}")
            raise DecisionError(
                f"Failed to get learning metrics: {str(e)}",
                error_code="LEARNING_METRICS_RETRIEVAL_FAILED",
                details={"engine_id": self.engine_id},
            )

    async def reset_learning(self) -> bool:
        """Reset learning state.

        Returns:
            True if reset was successful, False otherwise

        Raises:
            DecisionError: If there is an error resetting learning
        """
        try:
            async with self.database.get_session() as session:
                # Delete learning data for this engine
                result = await session.execute(
                    text(
                        """
                        DELETE FROM agent_learning_data 
                        WHERE agent_id LIKE :engine_pattern
                    """
                    ),
                    {"engine_pattern": f"%{self.engine_id.split('_')[0]}%"},
                )

                await session.commit()
                deleted_count = result.rowcount

                # Invalidate metrics cache
                self._invalidate_metrics_cache()

                # Publish reset event
                await self._publish_reset_event(deleted_count)

                logger.info(
                    f"Reset learning state for {self.engine_id}: deleted {deleted_count} records"
                )
                return True

        except Exception as e:
            logger.error(f"Failed to reset learning: {e}")
            raise DecisionError(
                f"Failed to reset learning: {str(e)}",
                error_code="LEARNING_RESET_FAILED",
                details={"engine_id": self.engine_id},
            )

    async def get_decision_recommendations(
        self, decision_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get learning-based recommendations for decision making.

        Args:
            decision_type: Type of decision being made
            context: Decision context

        Returns:
            Dictionary of recommendations based on learning data
        """
        try:
            # Check if database is initialized
            if (
                not self.database
                or not hasattr(self.database, "_session_factory")
                or not self.database._session_factory
            ):
                logger.error(
                    "Failed to get decision recommendations: Database not initialized"
                )
                return {
                    "recommendations": [],
                    "confidence": 0.0,
                    "source": "database_not_initialized",
                }

            async with self.database.get_session() as session:
                # Get relevant learning data for this decision type
                result = await session.execute(
                    text(
                        """
                        SELECT data, performance_score, created_at
                        FROM agent_learning_data 
                        WHERE agent_id LIKE :engine_pattern
                        AND learning_type = :decision_type
                        AND performance_score IS NOT NULL
                        ORDER BY created_at DESC
                        LIMIT 10
                    """
                    ),
                    {
                        "engine_pattern": f"%{self.engine_id.split('_')[0]}%",
                        "decision_type": decision_type,
                    },
                )

                learning_records = result.fetchall()

                if not learning_records:
                    return {
                        "recommendations": [],
                        "confidence": 0.0,
                        "source": "no_learning_data",
                    }

                # Analyze learning data to generate recommendations
                recommendations = []
                total_performance = 0.0

                for record in learning_records:
                    try:
                        if isinstance(record[0], str):
                            data = json.loads(record[0])
                        else:
                            data = record[0]

                        performance = record[1]
                        total_performance += performance

                        # Extract actionable recommendations
                        if performance > 0.7:  # High performance threshold
                            recommendations.append(
                                {
                                    "action": data.get("strategy", "unknown"),
                                    "confidence": performance,
                                    "context_match": self._calculate_context_similarity(
                                        context, data
                                    ),
                                    "performance_score": performance,
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Failed to process learning record: {e}")
                        continue

                # Sort recommendations by performance and context match
                recommendations.sort(
                    key=lambda x: x["performance_score"] * x["context_match"],
                    reverse=True,
                )

                avg_confidence = (
                    total_performance / len(learning_records)
                    if learning_records
                    else 0.0
                )

                return {
                    "recommendations": recommendations[:5],  # Top 5 recommendations
                    "confidence": avg_confidence,
                    "source": "learning_data",
                    "records_analyzed": len(learning_records),
                }

        except Exception as e:
            logger.error(f"Failed to get decision recommendations: {e}")
            return {
                "recommendations": [],
                "confidence": 0.0,
                "source": "error",
                "error": str(e),
            }

    async def get_confidence_adjustment(self, decision_type) -> float:
        """Get confidence adjustment based on learning data for a decision type.

        Args:
            decision_type: The type of decision to get adjustment for

        Returns:
            Float adjustment value (-1.0 to 1.0)
        """
        try:
            # Convert decision_type to string if it's an enum
            decision_type_str = (
                decision_type.value
                if hasattr(decision_type, "value")
                else str(decision_type)
            )

            # PERFORMANCE OPTIMIZATION: Check cache first
            current_time = datetime.now(timezone.utc)
            if decision_type_str in self._confidence_cache:
                cached_adjustment, cached_time = self._confidence_cache[
                    decision_type_str
                ]
                if (current_time - cached_time).total_seconds() < self._cache_ttl:
                    return cached_adjustment

            # Check if database is initialized
            if (
                not self.database
                or not hasattr(self.database, "_session_factory")
                or not self.database._session_factory
            ):
                logger.warning("Database not initialized")
                return 0.0

            async with self.database.get_session() as session:
                # Get recent learning data for this decision type
                result = await session.execute(
                    text(
                        """
                        SELECT AVG(performance_score) as avg_performance, COUNT(*) as count
                        FROM agent_learning_data
                        WHERE agent_id LIKE :engine_pattern
                        AND learning_type = :decision_type
                        AND created_at >= NOW() - INTERVAL '30 days'
                    """
                    ),
                    {
                        "engine_pattern": f"%{self.engine_id.split('_')[0]}%",
                        "decision_type": decision_type_str,
                    },
                )

                row = result.fetchone()
                if not row or row[1] == 0:  # No data available
                    return 0.0

                avg_performance = row[0] or 0.5
                sample_count = row[1]

                # Calculate confidence adjustment based on performance and sample size
                # Better performance increases confidence, more samples increase reliability
                performance_adjustment = (
                    avg_performance - 0.5
                ) * 0.4  # Scale to -0.2 to +0.2
                sample_adjustment = (
                    min(sample_count / 10.0, 1.0) * 0.1
                )  # Up to +0.1 for sample size

                total_adjustment = performance_adjustment + sample_adjustment

                # Clamp to reasonable range
                final_adjustment = max(-0.3, min(0.3, total_adjustment))

                # PERFORMANCE OPTIMIZATION: Cache the result
                self._confidence_cache[decision_type_str] = (
                    final_adjustment,
                    current_time,
                )

                return final_adjustment

        except Exception as e:
            logger.warning(f"Failed to get confidence adjustment: {e}")
            return 0.0

    async def _store_learning_data(self, feedback_data: Dict[str, Any]) -> None:
        """Store learning data in the database."""
        try:
            # Check if database is initialized
            if (
                not self.database
                or not hasattr(self.database, "_session_factory")
                or not self.database._session_factory
            ):
                logger.error("Failed to store learning data: Database not initialized")
                return

            async with self.database.get_session() as session:
                # Prepare learning data
                learning_type = feedback_data.get("decision_type", "general")
                performance_score = feedback_data.get("quality", 0.5)

                # Store in agent_learning_data table
                await session.execute(
                    text(
                        """
                        INSERT INTO agent_learning_data
                        (agent_id, learning_type, data, performance_score, created_at)
                        VALUES (:agent_id, :learning_type, :data, :performance_score, :created_at)
                    """
                    ),
                    {
                        "agent_id": self.engine_id,
                        "learning_type": learning_type,
                        "data": json.dumps(feedback_data),
                        "performance_score": performance_score,
                        "created_at": datetime.now(timezone.utc),
                    },
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store learning data: {e}")
            raise

    async def _update_learning_metrics(self, feedback_data: Dict[str, Any]) -> None:
        """Update learning metrics based on feedback."""
        # This could be expanded to update aggregate metrics tables
        # For now, metrics are calculated on-demand from raw data

    async def _publish_learning_event(self, feedback_data: Dict[str, Any]) -> None:
        """Publish learning event."""
        try:
            event = NotificationEvent(
                notification_name="learning_completed",
                data={
                    "engine_id": self.engine_id,
                    "decision_id": feedback_data.get("decision_id"),
                    "learning_type": feedback_data.get("decision_type", "general"),
                    "performance_score": feedback_data.get("quality", 0.5),
                    "outcome": feedback_data.get("outcome", "unknown"),
                },
                source=self.engine_id,
            )
            await self.publisher.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish learning event: {e}")

    async def _publish_reset_event(self, deleted_count: int) -> None:
        """Publish learning reset event."""
        try:
            event = NotificationEvent(
                notification_name="learning_reset",
                data={
                    "engine_id": self.engine_id,
                    "deleted_records": deleted_count,
                    "reset_at": datetime.now(timezone.utc).isoformat(),
                },
                source=self.engine_id,
            )
            await self.publisher.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish reset event: {e}")

    def _calculate_context_similarity(
        self, context1: Dict[str, Any], context2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two contexts."""
        try:
            # Simple similarity calculation based on common keys and values
            common_keys = set(context1.keys()) & set(context2.keys())
            if not common_keys:
                return 0.0

            matches = 0
            for key in common_keys:
                if context1[key] == context2[key]:
                    matches += 1

            return matches / len(common_keys)
        except Exception:
            return 0.0

    def _is_metrics_cache_valid(self) -> bool:
        """Check if metrics cache is still valid."""
        if not self._cache_timestamp or not self._metrics_cache:
            return False

        cache_age = (datetime.now(timezone.utc) - self._cache_timestamp).total_seconds()
        return cache_age < self._cache_ttl_seconds

    def _invalidate_metrics_cache(self) -> None:
        """Invalidate the metrics cache."""
        self._metrics_cache = {}
        self._cache_timestamp = None
