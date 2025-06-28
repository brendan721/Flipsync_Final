"""
Feedback processor component for the FlipSync application.

This module provides the feedback processor component for the Decision Pipeline,
which is responsible for processing feedback on decision outcomes. It collects
feedback and prepares it for learning.

The feedback processor is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Extensible: Supporting custom feedback processing strategies
"""

import abc
import asyncio
import copy
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.decision.interfaces import FeedbackProcessor
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


class BaseFeedbackProcessor(FeedbackProcessor):
    """Base class for feedback processors."""

    def __init__(self, processor_id: str, publisher: EventPublisher):
        """Initialize the feedback processor.

        Args:
            processor_id: Unique identifier for this processor
            publisher: Event publisher for publishing feedback events
        """
        self.processor_id = processor_id
        self.publisher = publisher
        logger.debug(f"Initialized feedback processor {processor_id}")


class InMemoryFeedbackProcessor(BaseFeedbackProcessor):
    """In-memory implementation of a feedback processor.

    This implementation stores feedback in memory and provides basic
    processing capabilities. It is suitable for testing and development,
    but not for production use with large amounts of feedback.
    """

    def __init__(self, processor_id: str, publisher: EventPublisher):
        """Initialize the in-memory feedback processor.

        Args:
            processor_id: Unique identifier for this processor
            publisher: Event publisher for publishing feedback events
        """
        super().__init__(processor_id, publisher)
        self.feedback: Dict[str, Dict[str, Any]] = {}
        self.feedback_by_decision: Dict[str, List[str]] = {}
        self.offline_feedback: Set[str] = set()

    async def process_feedback(
        self,
        decision_id: str,
        feedback_data: Dict[str, Any],
        publish_event: bool = False,
        offline: bool = False,
    ) -> Tuple[bool, str]:
        """Process feedback on a decision.

        Args:
            decision_id: ID of the decision
            feedback_data: Feedback data
            publish_event: Whether to publish an event about the feedback
            offline: Whether to process the feedback in offline mode

        Returns:
            Tuple of (success, feedback_id)
        """
        logger.debug(f"Processing feedback for decision {decision_id}")

        # Generate a feedback ID
        feedback_id = str(uuid.uuid4())

        # Create feedback entry
        feedback_entry = {
            "feedback_id": feedback_id,
            "decision_id": decision_id,
            "feedback_data": feedback_data,
            "timestamp": datetime.now().isoformat(),
        }

        # Store the feedback
        self.feedback[feedback_id] = feedback_entry

        # Index by decision ID
        if decision_id not in self.feedback_by_decision:
            self.feedback_by_decision[decision_id] = []
        self.feedback_by_decision[decision_id].append(feedback_id)

        # If offline, add to offline feedback
        if offline:
            self.offline_feedback.add(feedback_id)
            logger.debug(f"Added feedback {feedback_id} to offline queue")
        # Otherwise, publish event if requested
        elif publish_event:
            try:
                await self.publisher.publish_notification(
                    notification_name="feedback_processed",
                    data={
                        "feedback_id": feedback_id,
                        "decision_id": decision_id,
                        "feedback_summary": self._summarize_feedback(feedback_data),
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                logger.debug(f"Published feedback_processed event for {feedback_id}")
            except Exception as e:
                logger.error(f"Error publishing feedback_processed event: {e}")

        return True, feedback_id

    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback by ID.

        Args:
            feedback_id: ID of the feedback to get

        Returns:
            The feedback, or None if not found
        """
        return self.feedback.get(feedback_id)

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
        """
        logger.debug("Listing feedback")

        # If decision_id is provided, return only feedback for that decision
        if decision_id:
            if decision_id not in self.feedback_by_decision:
                return []

            feedback_ids = self.feedback_by_decision[decision_id]
            result = [self.feedback[fid] for fid in feedback_ids]

            # Apply filters if provided
            if filters:
                result = [f for f in result if self._matches_filters(f, filters)]

            return result

        # If filters are provided, apply them to all feedback
        if filters:
            return [
                f for f in self.feedback.values() if self._matches_filters(f, filters)
            ]

        # Otherwise, return all feedback
        return list(self.feedback.values())

    async def sync_offline_feedback(self) -> int:
        """Synchronize offline feedback.

        This method publishes events for feedback that was processed offline.

        Returns:
            Number of feedback entries synchronized
        """
        logger.debug(f"Syncing {len(self.offline_feedback)} offline feedback entries")

        count = 0
        offline_ids = list(
            self.offline_feedback
        )  # Create a copy to avoid modification during iteration

        for feedback_id in offline_ids:
            if feedback_id not in self.feedback:
                self.offline_feedback.remove(feedback_id)
                continue

            feedback = self.feedback[feedback_id]

            try:
                await self.publisher.publish_notification(
                    notification_name="feedback_processed",
                    data={
                        "feedback_id": feedback_id,
                        "decision_id": feedback["decision_id"],
                        "feedback_summary": self._summarize_feedback(
                            feedback["feedback_data"]
                        ),
                        "timestamp": datetime.now().isoformat(),
                    },
                )
                count += 1
                self.offline_feedback.remove(feedback_id)
                logger.debug(f"Synced offline feedback {feedback_id}")
            except Exception as e:
                logger.error(f"Error syncing offline feedback: {e}")

        return count

    def _summarize_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize feedback data for event publication.

        Args:
            feedback_data: Full feedback data

        Returns:
            Summarized feedback data
        """
        summary = {}

        # Include quality if available
        if "quality" in feedback_data:
            summary["quality"] = feedback_data["quality"]

        # Include relevance if available
        if "relevance" in feedback_data:
            summary["relevance"] = feedback_data["relevance"]

        # Include category if available
        if "category" in feedback_data:
            summary["category"] = feedback_data["category"]

        # Include mobile optimization flags
        if "battery_efficient" in feedback_data:
            summary["battery_efficient"] = feedback_data["battery_efficient"]

        if "network_efficient" in feedback_data:
            summary["network_efficient"] = feedback_data["network_efficient"]

        return summary

    def _matches_filters(
        self, feedback: Dict[str, Any], filters: Dict[str, Any]
    ) -> bool:
        """Check if feedback matches the given filters.

        Args:
            feedback: Feedback to check
            filters: Filters to apply

        Returns:
            True if the feedback matches the filters, False otherwise
        """
        for key, value in filters.items():
            # Check top-level keys
            if key in feedback and feedback[key] != value:
                return False

            # Check nested keys in feedback_data
            if "feedback_data" in feedback and key in feedback["feedback_data"]:
                if feedback["feedback_data"][key] != value:
                    return False

        return True
