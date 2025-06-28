"""
Learning engine component for the FlipSync application.

This module provides the learning engine component for the Decision Pipeline,
which is responsible for learning from decision outcomes and feedback. It adapts
decision-making strategies based on past performance.

The learning engine is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Extensible: Supporting custom learning strategies
"""

import abc
import asyncio
import copy
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.decision.interfaces import LearningEngine
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


class BaseLearningEngine(LearningEngine):
    """Base class for learning engines."""

    def __init__(self, engine_id: str, publisher: EventPublisher):
        """Initialize the learning engine.

        Args:
            engine_id: Unique identifier for this engine
            publisher: Event publisher for publishing learning events
        """
        self.engine_id = engine_id
        self.publisher = publisher
        logger.debug(f"Initialized learning engine {engine_id}")


class InMemoryLearningEngine(BaseLearningEngine):
    """In-memory implementation of a learning engine.

    This implementation stores learning data in memory and provides basic
    learning capabilities. It is suitable for testing and development,
    but not for production use with large amounts of data.
    """

    def __init__(self, engine_id: str, publisher: EventPublisher):
        """Initialize the in-memory learning engine.

        Args:
            engine_id: Unique identifier for this engine
            publisher: Event publisher for publishing learning events
        """
        super().__init__(engine_id, publisher)
        self.learning_data = {
            "feedback_count": 0,
            "learning_iterations": 0,
            "confidence_adjustments": {},
            "decision_type_weights": {},
            "last_learning_time": None,
            "battery_efficient_learning": False,
        }

    async def learn_from_feedback(
        self,
        feedback_data: Dict[str, Any],
        publish_event: bool = False,
        battery_efficient: bool = False,
    ) -> bool:
        """Learn from feedback on decision outcomes.

        Args:
            feedback_data: Feedback data
            publish_event: Whether to publish an event about the learning
            battery_efficient: Whether to use battery-efficient learning

        Returns:
            True if learning was successful, False otherwise
        """
        logger.debug("Learning from feedback")

        # Extract data from feedback
        decision_id = feedback_data.get("decision_id")
        decision_type = feedback_data.get("decision_type")
        confidence = feedback_data.get("confidence", 0.5)
        actual_outcome = feedback_data.get("actual_outcome", "unknown")
        quality = feedback_data.get("quality", 0.5)
        relevance = feedback_data.get("relevance", 0.5)

        # Update learning data
        self.learning_data["feedback_count"] += 1
        self.learning_data["learning_iterations"] += 1
        self.learning_data["last_learning_time"] = datetime.now().isoformat()
        self.learning_data["battery_efficient_learning"] = battery_efficient

        # Calculate confidence adjustment based on outcome and quality
        confidence_adjustment = self._calculate_confidence_adjustment(
            actual_outcome, quality, relevance, battery_efficient
        )

        # Update confidence adjustments for this decision type
        if decision_type not in self.learning_data["confidence_adjustments"]:
            self.learning_data["confidence_adjustments"][decision_type] = 0

        self.learning_data["confidence_adjustments"][
            decision_type
        ] += confidence_adjustment

        # Update decision type weights
        if decision_type not in self.learning_data["decision_type_weights"]:
            self.learning_data["decision_type_weights"][decision_type] = 1.0

        # Adjust weight based on quality
        weight_adjustment = quality - 0.5  # -0.5 to 0.5
        self.learning_data["decision_type_weights"][decision_type] += weight_adjustment

        # Ensure weight is positive
        self.learning_data["decision_type_weights"][decision_type] = max(
            0.1, self.learning_data["decision_type_weights"][decision_type]
        )

        # Publish event if requested
        if publish_event:
            try:
                await self.publisher.publish_notification(
                    notification_name="learning_completed",
                    data={
                        "decision_id": decision_id,
                        "decision_type": decision_type,
                        "confidence_adjustment": confidence_adjustment,
                        "quality": quality,
                        "relevance": relevance,
                        "timestamp": datetime.now().isoformat(),
                        "battery_efficient": battery_efficient,
                    },
                )
                logger.debug("Published learning_completed event")
            except Exception as e:
                logger.error(f"Error publishing learning_completed event: {e}")

        return True

    async def get_learning_metrics(self) -> Dict[str, Any]:
        """Get metrics on learning.

        Returns:
            Dictionary of metrics
        """
        logger.debug("Getting learning metrics")
        return copy.deepcopy(self.learning_data)

    async def reset_learning(self, publish_event: bool = False) -> bool:
        """Reset learning state.

        Args:
            publish_event: Whether to publish an event about the reset

        Returns:
            True if reset was successful, False otherwise
        """
        logger.debug("Resetting learning state")

        # Reset learning data
        self.learning_data = {
            "feedback_count": 0,
            "learning_iterations": 0,
            "confidence_adjustments": {},
            "decision_type_weights": {},
            "last_learning_time": None,
            "battery_efficient_learning": False,
        }

        # Publish event if requested
        if publish_event:
            try:
                await self.publisher.publish_notification(
                    notification_name="learning_reset",
                    data={"timestamp": datetime.now().isoformat()},
                )
                logger.debug("Published learning_reset event")
            except Exception as e:
                logger.error(f"Error publishing learning_reset event: {e}")

        return True

    async def get_confidence_adjustment(self, decision_type: DecisionType) -> float:
        """Get confidence adjustment for a decision type.

        Args:
            decision_type: Type of decision

        Returns:
            Confidence adjustment value
        """
        logger.debug(f"Getting confidence adjustment for {decision_type}")
        return self.learning_data["confidence_adjustments"].get(decision_type.value, 0)

    def _calculate_confidence_adjustment(
        self,
        actual_outcome: str,
        quality: float,
        relevance: float,
        battery_efficient: bool,
    ) -> float:
        """Calculate confidence adjustment based on outcome and quality.

        Args:
            actual_outcome: Actual outcome of the decision
            quality: Quality rating of the decision
            relevance: Relevance rating of the decision
            battery_efficient: Whether to use battery-efficient calculation

        Returns:
            Confidence adjustment value
        """
        # Base adjustment based on outcome
        if actual_outcome == "success":
            base_adjustment = 0.05
        elif actual_outcome == "partial_success":
            base_adjustment = 0.02
        elif actual_outcome == "failure":
            base_adjustment = -0.05
        else:
            base_adjustment = 0

        # If battery efficient, use simplified calculation
        if battery_efficient:
            return base_adjustment

        # Otherwise, adjust based on quality and relevance
        quality_factor = quality - 0.5  # -0.5 to 0.5
        relevance_factor = relevance - 0.5  # -0.5 to 0.5

        # Combine factors
        adjustment = (
            base_adjustment + (quality_factor * 0.02) + (relevance_factor * 0.01)
        )

        # Limit adjustment range
        return max(-0.1, min(0.1, adjustment))
