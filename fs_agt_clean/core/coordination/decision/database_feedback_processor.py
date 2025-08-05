"""
Database-backed Feedback Processor for FlipSync Agentic System

This module provides a production-ready database-backed implementation of the
FeedbackProcessor interface, storing all feedback data in PostgreSQL for
persistence across agent restarts and enabling cross-agent feedback sharing.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from fs_agt_clean.core.coordination.decision.feedback_processor import (
    BaseFeedbackProcessor,
)
from fs_agt_clean.core.coordination.decision.models import DecisionError
from fs_agt_clean.core.coordination.event_system import (
    EventPublisher,
    NotificationEvent,
)
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class DatabaseFeedbackProcessor(BaseFeedbackProcessor):
    """Database-backed implementation of FeedbackProcessor.

    This implementation stores all feedback data in PostgreSQL, providing:
    - Persistent feedback data across agent restarts
    - Cross-agent feedback data sharing and analysis
    - Transaction-safe feedback data operations
    - Performance optimized feedback queries and analytics
    """

    def __init__(
        self, processor_id: str, publisher: EventPublisher, database: Database
    ):
        """Initialize the database feedback processor.

        Args:
            processor_id: Unique identifier for this processor
            publisher: Event publisher for publishing feedback events
            database: Database instance for persistence operations
        """
        super().__init__(processor_id, publisher)
        self.database = database
        self._metrics_cache: Dict[str, Any] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl_seconds = 180  # Cache metrics for 3 minutes
        logger.info(f"Initialized DatabaseFeedbackProcessor {processor_id}")

    async def process_feedback(
        self,
        decision_id: str,
        feedback_data: Dict[str, Any],
        publish_event: bool = True,
        offline: bool = False,
    ) -> Tuple[bool, str]:
        """Process feedback on a decision and store it in the database.

        Args:
            decision_id: ID of the decision
            feedback_data: Feedback data
            publish_event: Whether to publish an event about the feedback
            offline: Whether to process the feedback in offline mode

        Returns:
            Tuple of (success, feedback_id)

        Raises:
            DecisionError: If there is an error processing feedback
        """
        try:
            # Validate feedback data
            if not feedback_data or not isinstance(feedback_data, dict):
                logger.warning(
                    f"Invalid feedback data provided for decision {decision_id}"
                )
                return False

            # Generate feedback ID
            feedback_id = str(uuid.uuid4())

            # Store feedback in database
            await self._store_feedback_data(feedback_id, decision_id, feedback_data)

            # Publish feedback event (only if not offline and publish_event is True)
            if publish_event and not offline:
                await self._publish_feedback_event(
                    feedback_id, decision_id, feedback_data
                )

            # Invalidate metrics cache
            self._invalidate_metrics_cache()

            logger.debug(f"Processed feedback {feedback_id} for decision {decision_id}")
            return True, feedback_id

        except Exception as e:
            logger.error(f"Failed to process feedback for decision {decision_id}: {e}")
            raise DecisionError(
                f"Failed to process feedback: {str(e)}",
                error_code="FEEDBACK_PROCESSING_FAILED",
                details={
                    "decision_id": decision_id,
                    "processor_id": self.processor_id,
                    "feedback_data": feedback_data,
                },
            )

    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback by ID.

        Args:
            feedback_id: ID of the feedback to get

        Returns:
            The feedback, or None if not found

        Raises:
            DecisionError: If there is an error getting feedback
        """
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text(
                        """
                        SELECT id, decision_id, feedback_data, quality_score, 
                               outcome, execution_time, created_at, processor_id
                        FROM agent_feedback 
                        WHERE id = :feedback_id
                    """
                    ),
                    {"feedback_id": feedback_id},
                )

                row = result.fetchone()
                if not row:
                    return None

                # Reconstruct feedback data
                feedback_data = (
                    json.loads(row[2]) if isinstance(row[2], str) else row[2]
                )

                return {
                    "feedback_id": row[0],
                    "decision_id": row[1],
                    "feedback_data": feedback_data,
                    "quality_score": row[3],
                    "outcome": row[4],
                    "execution_time": row[5],
                    "created_at": row[6].isoformat() if row[6] else None,
                    "processor_id": row[7],
                }

        except Exception as e:
            logger.error(f"Failed to get feedback {feedback_id}: {e}")
            raise DecisionError(
                f"Failed to get feedback: {str(e)}",
                error_code="FEEDBACK_RETRIEVAL_FAILED",
                details={"feedback_id": feedback_id, "processor_id": self.processor_id},
            )

    async def list_feedback(
        self,
        decision_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """List feedback matching the given filters.

        Args:
            decision_id: Optional ID of a specific decision
            filters: Optional filters to apply

        Returns:
            List of matching feedback

        Raises:
            DecisionError: If there is an error listing feedback
        """
        try:
            async with self.database.get_session() as session:
                # Build base query
                query = """
                    SELECT id, decision_id, feedback_data, quality_score, 
                           outcome, execution_time, created_at, processor_id
                    FROM agent_feedback 
                    WHERE processor_id LIKE :processor_pattern
                """
                params = {"processor_pattern": f"%{self.processor_id.split('_')[0]}%"}

                # Add decision_id filter if provided
                if decision_id:
                    query += " AND decision_id = :decision_id"
                    params["decision_id"] = decision_id

                # Apply additional filters
                if filters:
                    if "outcome" in filters:
                        query += " AND outcome = :outcome"
                        params["outcome"] = filters["outcome"]

                    if "min_quality" in filters:
                        query += " AND quality_score >= :min_quality"
                        params["min_quality"] = filters["min_quality"]

                    if "max_quality" in filters:
                        query += " AND quality_score <= :max_quality"
                        params["max_quality"] = filters["max_quality"]

                    if "date_from" in filters:
                        query += " AND created_at >= :date_from"
                        params["date_from"] = filters["date_from"]

                    if "date_to" in filters:
                        query += " AND created_at <= :date_to"
                        params["date_to"] = filters["date_to"]

                query += " ORDER BY created_at DESC"

                if filters and "limit" in filters:
                    query += " LIMIT :limit"
                    params["limit"] = filters["limit"]

                result = await session.execute(text(query), params)
                rows = result.fetchall()

                feedback_list = []
                for row in rows:
                    try:
                        feedback_data = (
                            json.loads(row[2]) if isinstance(row[2], str) else row[2]
                        )

                        feedback_entry = {
                            "feedback_id": row[0],
                            "decision_id": row[1],
                            "feedback_data": feedback_data,
                            "quality_score": row[3],
                            "outcome": row[4],
                            "execution_time": row[5],
                            "created_at": row[6].isoformat() if row[6] else None,
                            "processor_id": row[7],
                        }
                        feedback_list.append(feedback_entry)
                    except Exception as e:
                        logger.warning(f"Failed to process feedback row {row[0]}: {e}")
                        continue

                logger.debug(f"Retrieved {len(feedback_list)} feedback entries")
                return feedback_list

        except Exception as e:
            logger.error(f"Failed to list feedback: {e}")
            raise DecisionError(
                f"Failed to list feedback: {str(e)}",
                error_code="FEEDBACK_LIST_FAILED",
                details={
                    "decision_id": decision_id,
                    "filters": filters,
                    "processor_id": self.processor_id,
                },
            )

    async def get_feedback_metrics(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get metrics on feedback data.

        Args:
            filters: Optional filters to apply

        Returns:
            Dictionary of feedback metrics
        """
        try:
            # Check cache first
            if self._is_metrics_cache_valid():
                logger.debug("Returning cached feedback metrics")
                return self._metrics_cache.copy()

            async with self.database.get_session() as session:
                # Base query for this processor's feedback
                base_where = "WHERE processor_id LIKE :processor_pattern"
                params = {"processor_pattern": f"%{self.processor_id.split('_')[0]}%"}

                # Apply filters
                if filters:
                    if "outcome" in filters:
                        base_where += " AND outcome = :outcome"
                        params["outcome"] = filters["outcome"]

                    if "date_from" in filters:
                        base_where += " AND created_at >= :date_from"
                        params["date_from"] = filters["date_from"]

                    if "date_to" in filters:
                        base_where += " AND created_at <= :date_to"
                        params["date_to"] = filters["date_to"]

                # Get total feedback count
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM agent_feedback {base_where}"), params
                )
                total_feedback = result.scalar()

                # Get feedback by outcome
                result = await session.execute(
                    text(
                        f"""
                        SELECT outcome, COUNT(*) as count
                        FROM agent_feedback {base_where}
                        GROUP BY outcome
                    """
                    ),
                    params,
                )
                feedback_by_outcome = {row[0]: row[1] for row in result.fetchall()}

                # Get average quality score
                result = await session.execute(
                    text(f"SELECT AVG(quality_score) FROM agent_feedback {base_where}"),
                    params,
                )
                avg_quality = result.scalar() or 0.0

                # Get recent feedback (last 24 hours)
                result = await session.execute(
                    text(
                        f"""
                        SELECT COUNT(*) FROM agent_feedback {base_where}
                        AND created_at >= NOW() - INTERVAL '24 hours'
                    """
                    ),
                    params,
                )
                recent_feedback = result.scalar()

                # Get feedback trend (last 7 days)
                result = await session.execute(
                    text(
                        f"""
                        SELECT DATE(created_at) as feedback_date, COUNT(*) as count
                        FROM agent_feedback {base_where}
                        AND created_at >= NOW() - INTERVAL '7 days'
                        GROUP BY DATE(created_at)
                        ORDER BY feedback_date
                    """
                    ),
                    params,
                )
                feedback_trend = {str(row[0]): row[1] for row in result.fetchall()}

                metrics = {
                    "total_feedback": total_feedback,
                    "feedback_by_outcome": feedback_by_outcome,
                    "average_quality_score": float(avg_quality),
                    "recent_feedback_24h": recent_feedback,
                    "feedback_trend_7d": feedback_trend,
                    "processor_id": self.processor_id,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "cache_ttl_seconds": self._cache_ttl_seconds,
                }

                # Cache the metrics
                self._metrics_cache = metrics.copy()
                self._cache_timestamp = datetime.now(timezone.utc)

                logger.debug(
                    f"Generated feedback metrics: {total_feedback} total feedback"
                )
                return metrics

        except Exception as e:
            logger.error(f"Failed to get feedback metrics: {e}")
            raise DecisionError(
                f"Failed to get feedback metrics: {str(e)}",
                error_code="FEEDBACK_METRICS_RETRIEVAL_FAILED",
                details={"filters": filters, "processor_id": self.processor_id},
            )

    async def _store_feedback_data(
        self, feedback_id: str, decision_id: str, feedback_data: Dict[str, Any]
    ) -> None:
        """Store feedback data in the database."""
        try:
            async with self.database.get_session() as session:
                # Extract key metrics from feedback data
                quality_score = feedback_data.get("quality", 0.5)
                outcome = feedback_data.get("outcome", "unknown")
                execution_time = feedback_data.get("execution_time", 0.0)

                # Store in agent_feedback table
                await session.execute(
                    text(
                        """
                        INSERT INTO agent_feedback
                        (id, decision_id, feedback_data, quality_score, outcome,
                         execution_time, created_at, processor_id)
                        VALUES (:id, :decision_id, :feedback_data, :quality_score,
                                :outcome, :execution_time, :created_at, :processor_id)
                    """
                    ),
                    {
                        "id": feedback_id,
                        "decision_id": decision_id,
                        "feedback_data": json.dumps(feedback_data),
                        "quality_score": quality_score,
                        "outcome": outcome,
                        "execution_time": execution_time,
                        "created_at": datetime.now(timezone.utc),
                        "processor_id": self.processor_id,
                    },
                )
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to store feedback data: {e}")
            raise

    async def _publish_feedback_event(
        self, feedback_id: str, decision_id: str, feedback_data: Dict[str, Any]
    ) -> None:
        """Publish feedback processing event."""
        try:
            event = NotificationEvent(
                notification_name="feedback_processed",
                data={
                    "feedback_id": feedback_id,
                    "decision_id": decision_id,
                    "processor_id": self.processor_id,
                    "quality_score": feedback_data.get("quality", 0.5),
                    "outcome": feedback_data.get("outcome", "unknown"),
                    "feedback_summary": self._summarize_feedback(feedback_data),
                },
                source=self.processor_id,
            )
            await self.publisher.publish(event)
        except Exception as e:
            logger.warning(f"Failed to publish feedback event: {e}")

    def _summarize_feedback(self, feedback_data: Dict[str, Any]) -> str:
        """Create a summary of feedback data."""
        try:
            outcome = feedback_data.get("outcome", "unknown")
            quality = feedback_data.get("quality", 0.5)
            decision_type = feedback_data.get("decision_type", "unknown")

            return f"{decision_type} decision: {outcome} (quality: {quality:.2f})"
        except Exception:
            return "feedback processed"

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
