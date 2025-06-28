"""
Decision tracker component for the FlipSync application.

This module provides the decision tracker component for the Decision Pipeline,
which is responsible for tracking decisions and their outcomes. It maintains
a history of decisions and provides metrics on decision quality.

The decision tracker is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Extensible: Supporting custom tracking strategies
"""

import abc
import asyncio
import copy
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.decision.interfaces import DecisionTracker
from fs_agt_clean.core.coordination.decision.models import (
    Decision,
    DecisionConfidence,
    DecisionError,
    DecisionStatus,
    DecisionType,
)
from fs_agt_clean.core.coordination.event_system import (
    EventPublisher,
    NotificationEvent,
)

logger = logging.getLogger(__name__)


class BaseDecisionTracker(DecisionTracker):
    """Base class for decision trackers."""

    def __init__(self, tracker_id: str, publisher: EventPublisher):
        """Initialize the decision tracker.

        Args:
            tracker_id: Unique identifier for this tracker
            publisher: Event publisher for publishing decision events
        """
        self.tracker_id = tracker_id
        self.publisher = publisher
        logger.debug(f"Initialized decision tracker {tracker_id}")


class InMemoryDecisionTracker(BaseDecisionTracker):
    """In-memory implementation of a decision tracker.

    This implementation stores decisions in memory and provides basic
    tracking capabilities. It is suitable for testing and development,
    but not for production use with large numbers of decisions.
    """

    def __init__(self, tracker_id: str, publisher: EventPublisher):
        """Initialize the in-memory decision tracker.

        Args:
            tracker_id: Unique identifier for this tracker
            publisher: Event publisher for publishing decision events
        """
        super().__init__(tracker_id, publisher)
        self.decisions: Dict[str, Decision] = {}
        self.decision_history: List[Decision] = []
        self.offline_decisions: List[Decision] = []
        self.metrics: Dict[str, Any] = {
            "total_decisions": 0,
            "decisions_by_status": {},
            "decisions_by_type": {},
            "average_confidence": 0.0,
        }

    async def track_decision(
        self, decision: Decision, publish_event: bool = False, offline: bool = False
    ) -> bool:
        """Track a decision.

        Args:
            decision: The decision to track
            publish_event: Whether to publish an event about the decision
            offline: Whether to track the decision in offline mode

        Returns:
            True if the decision was tracked, False otherwise
        """
        logger.debug(f"Tracking decision {decision.metadata.decision_id}")

        # Store the decision
        self.decisions[decision.metadata.decision_id] = decision
        self.decision_history.append(decision)

        # Update metrics
        self._update_metrics_for_decision(decision)

        # If offline, add to offline decisions
        if offline:
            # Store the decision ID in the offline_decisions list
            if decision.metadata.decision_id not in [
                d.metadata.decision_id for d in self.offline_decisions
            ]:
                self.offline_decisions.append(decision)
                logger.debug(
                    f"Added decision {decision.metadata.decision_id} to offline queue"
                )
        # Otherwise, publish event if requested
        elif publish_event:
            try:
                await self.publisher.publish_notification(
                    notification_name="decision_tracked",
                    data={
                        "decision_id": decision.metadata.decision_id,
                        "decision_type": decision.decision_type.value,
                        "action": decision.action,
                        "confidence": decision.confidence,
                        "status": decision.metadata.status.value,
                        "decision_source": decision.metadata.source,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                logger.debug(
                    f"Published decision_tracked event for {decision.metadata.decision_id}"
                )
            except Exception as e:
                logger.error(f"Error publishing decision_tracked event: {e}")

        return True

    async def update_decision_status(
        self, decision_id: str, status: DecisionStatus, publish_event: bool = False
    ) -> bool:
        """Update the status of a decision.

        Args:
            decision_id: ID of the decision to update
            status: New status
            publish_event: Whether to publish an event about the status update

        Returns:
            True if the status was updated, False otherwise
        """
        logger.debug(f"Updating decision {decision_id} status to {status}")

        # Check if the decision exists
        if decision_id not in self.decisions:
            logger.warning(f"Decision {decision_id} not found")
            return False

        # Get the decision
        decision = self.decisions[decision_id]

        # Update metrics for old status
        old_status = decision.metadata.status
        if old_status.value in self.metrics["decisions_by_status"]:
            self.metrics["decisions_by_status"][old_status.value] -= 1

        # Update the status
        decision.update_status(status)

        # Update metrics for new status
        if status.value not in self.metrics["decisions_by_status"]:
            self.metrics["decisions_by_status"][status.value] = 0
        self.metrics["decisions_by_status"][status.value] += 1

        # Publish event if requested
        if publish_event:
            try:
                await self.publisher.publish_notification(
                    notification_name="decision_status_updated",
                    data={
                        "decision_id": decision_id,
                        "status": status.value,
                        "previous_status": old_status.value,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                logger.debug(
                    f"Published decision_status_updated event for {decision_id}"
                )
            except Exception as e:
                logger.error(f"Error publishing decision_status_updated event: {e}")

        return True

    async def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID.

        Args:
            decision_id: ID of the decision to get

        Returns:
            The decision, or None if not found
        """
        logger.debug(f"Getting decision {decision_id}")

        return self.decisions.get(decision_id)

    async def get_decision_history(
        self,
        decision_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Decision]:
        """Get the history of decisions.

        Args:
            decision_id: Optional ID of a specific decision
            filters: Optional filters to apply

        Returns:
            List of decisions
        """
        logger.debug("Getting decision history")

        # If decision_id is provided, return only that decision
        if decision_id:
            if decision_id in self.decisions:
                return [self.decisions[decision_id]]
            return []

        # If filters are provided, apply them
        if filters:
            return [
                decision
                for decision in self.decision_history
                if self._matches_filters(decision, filters)
            ]

        # Otherwise, return all decisions
        return self.decision_history

    async def get_decision_metrics(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get metrics on decisions.

        Args:
            filters: Optional filters to apply

        Returns:
            Dictionary of metrics
        """
        logger.debug("Getting decision metrics")

        # If no filters, return the global metrics
        if not filters:
            return copy.deepcopy(self.metrics)

        # Otherwise, calculate metrics for filtered decisions
        filtered_decisions = [
            decision
            for decision in self.decision_history
            if self._matches_filters(decision, filters)
        ]

        # Calculate metrics
        metrics = {
            "total_decisions": len(filtered_decisions),
            "decisions_by_status": {},
            "decisions_by_type": {},
            "average_confidence": 0.0,
        }

        # Calculate status and type counts
        for decision in filtered_decisions:
            status = decision.metadata.status.value
            if status not in metrics["decisions_by_status"]:
                metrics["decisions_by_status"][status] = 0
            metrics["decisions_by_status"][status] += 1

            decision_type = decision.decision_type.value
            if decision_type not in metrics["decisions_by_type"]:
                metrics["decisions_by_type"][decision_type] = 0
            metrics["decisions_by_type"][decision_type] += 1

        # Calculate average confidence
        if filtered_decisions:
            total_confidence = sum(
                decision.confidence for decision in filtered_decisions
            )
            metrics["average_confidence"] = total_confidence / len(filtered_decisions)

        return metrics

    async def sync_offline_decisions(self) -> int:
        """Synchronize offline decisions.

        This method publishes events for decisions that were tracked offline.

        Returns:
            Number of decisions synchronized
        """
        logger.debug(f"Syncing {len(self.offline_decisions)} offline decisions")

        count = 0
        for decision in self.offline_decisions:
            try:
                await self.publisher.publish_notification(
                    notification_name="decision_tracked",
                    data={
                        "decision_id": decision.metadata.decision_id,
                        "decision_type": decision.decision_type.value,
                        "action": decision.action,
                        "confidence": decision.confidence,
                        "status": decision.metadata.status.value,
                        "decision_source": decision.metadata.source,
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                count += 1
                logger.debug(f"Synced offline decision {decision.metadata.decision_id}")
            except Exception as e:
                logger.error(f"Error syncing offline decision: {e}")

        # Clear the offline decisions
        self.offline_decisions = []

        return count

    def _update_metrics_for_decision(self, decision: Decision) -> None:
        """Update metrics for a new decision.

        Args:
            decision: The decision to update metrics for
        """
        # Update total count
        self.metrics["total_decisions"] += 1

        # Update status count
        status = decision.metadata.status.value
        if status not in self.metrics["decisions_by_status"]:
            self.metrics["decisions_by_status"][status] = 0
        self.metrics["decisions_by_status"][status] += 1

        # Update type count
        decision_type = decision.decision_type.value
        if decision_type not in self.metrics["decisions_by_type"]:
            self.metrics["decisions_by_type"][decision_type] = 0
        self.metrics["decisions_by_type"][decision_type] += 1

        # Update average confidence
        total_confidence = self.metrics["average_confidence"] * (
            self.metrics["total_decisions"] - 1
        )
        total_confidence += decision.confidence
        self.metrics["average_confidence"] = (
            total_confidence / self.metrics["total_decisions"]
        )

    def _matches_filters(self, decision: Decision, filters: Dict[str, Any]) -> bool:
        """Check if a decision matches the given filters.

        Args:
            decision: Decision to check
            filters: Filters to apply

        Returns:
            True if the decision matches the filters, False otherwise
        """
        for key, value in filters.items():
            if key == "decision_type" and decision.decision_type != value:
                return False
            elif key == "action" and decision.action != value:
                return False
            elif key == "min_confidence" and decision.confidence < value:
                return False
            elif key == "max_confidence" and decision.confidence > value:
                return False
            elif key == "status" and decision.metadata.status != value:
                return False
            elif key == "source" and decision.metadata.source != value:
                return False
            elif key == "target" and decision.metadata.target != value:
                return False
            elif key == "created_after" and decision.metadata.created_at < value:
                return False
            elif key == "created_before" and decision.metadata.created_at > value:
                return False
            elif key == "battery_efficient" and decision.battery_efficient != value:
                return False
            elif key == "network_efficient" and decision.network_efficient != value:
                return False

        return True
