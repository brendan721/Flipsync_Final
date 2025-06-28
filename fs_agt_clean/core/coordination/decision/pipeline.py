"""
Decision pipeline component for the FlipSync application.

This module provides the decision pipeline component, which orchestrates the
entire decision-making process, from making a decision to executing it and
learning from the outcome. It combines all the other components into a cohesive
workflow.

The decision pipeline is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Extensible: Supporting custom decision-making workflows
"""

import abc
import asyncio
import copy
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.decision.interfaces import (
    DecisionMaker,
    DecisionPipeline,
    DecisionTracker,
    DecisionValidator,
    FeedbackProcessor,
    LearningEngine,
)
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


class BaseDecisionPipeline(DecisionPipeline):
    """Base class for decision pipelines."""

    def __init__(
        self,
        pipeline_id: str,
        decision_maker: DecisionMaker,
        decision_validator: DecisionValidator,
        decision_tracker: DecisionTracker,
        feedback_processor: FeedbackProcessor,
        learning_engine: LearningEngine,
        publisher: EventPublisher,
    ):
        """Initialize the decision pipeline.

        Args:
            pipeline_id: Unique identifier for this pipeline
            decision_maker: Component for making decisions
            decision_validator: Component for validating decisions
            decision_tracker: Component for tracking decisions
            feedback_processor: Component for processing feedback
            learning_engine: Component for learning from feedback
            publisher: Event publisher for publishing pipeline events
        """
        self.pipeline_id = pipeline_id
        self.decision_maker = decision_maker
        self.decision_validator = decision_validator
        self.decision_tracker = decision_tracker
        self.feedback_processor = feedback_processor
        self.learning_engine = learning_engine
        self.publisher = publisher
        logger.debug(f"Initialized decision pipeline {pipeline_id}")


class StandardDecisionPipeline(BaseDecisionPipeline):
    """Standard implementation of a decision pipeline.

    This implementation provides a standard decision-making workflow:
    1. Make a decision
    2. Validate the decision
    3. Execute the decision
    4. Process feedback
    5. Learn from feedback

    It is designed to be mobile-optimized and vision-aligned.
    """

    async def make_decision(
        self,
        context: Dict[str, Any],
        options: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Decision:
        """Make a decision based on context, options, and constraints.

        Args:
            context: Context in which the decision is being made
            options: Available options to choose from
            constraints: Optional constraints on the decision

        Returns:
            The decision that was made

        Raises:
            DecisionError: If the decision cannot be made
        """
        logger.debug("Making decision")

        try:
            # Apply confidence adjustment based on learning
            adjusted_context = await self._apply_learning(context)

            # Make the decision
            decision = await self.decision_maker.make_decision(
                adjusted_context, options, constraints
            )

            # Track the decision
            await self.decision_tracker.track_decision(decision)

            return decision
        except Exception as e:
            logger.error(f"Error making decision: {e}")
            raise DecisionError(
                message=f"Failed to make decision: {e}",
                error_code="DECISION_MAKING_ERROR",
            )

    async def validate_decision(self, decision: Decision) -> Tuple[bool, List[str]]:
        """Validate a decision against rules and constraints.

        Args:
            decision: The decision to validate

        Returns:
            Tuple of (is_valid, validation_messages)

        Raises:
            DecisionError: If there is an error validating the decision
        """
        logger.debug(f"Validating decision {decision.metadata.decision_id}")

        try:
            # Validate the decision
            is_valid, messages = await self.decision_validator.validate_decision(
                decision
            )

            # Update decision status based on validation
            if is_valid:
                decision.update_status(DecisionStatus.APPROVED)
                await self.decision_tracker.update_decision_status(
                    decision.metadata.decision_id, DecisionStatus.APPROVED
                )
            else:
                decision.update_status(DecisionStatus.REJECTED)
                await self.decision_tracker.update_decision_status(
                    decision.metadata.decision_id, DecisionStatus.REJECTED
                )

            return is_valid, messages
        except Exception as e:
            logger.error(f"Error validating decision: {e}")
            raise DecisionError(
                message=f"Failed to validate decision: {e}",
                error_code="DECISION_VALIDATION_ERROR",
            )

    async def execute_decision(
        self, decision: Decision, validate: bool = False, offline: bool = False
    ) -> bool:
        """Execute a decision.

        Args:
            decision: The decision to execute
            validate: Whether to validate the decision before executing
            offline: Whether to execute the decision in offline mode

        Returns:
            True if execution was successful, False otherwise

        Raises:
            DecisionError: If there is an error executing the decision
        """
        logger.debug(f"Executing decision {decision.metadata.decision_id}")

        try:
            # Validate the decision if requested
            if validate:
                is_valid, messages = await self.validate_decision(decision)
                if not is_valid:
                    raise DecisionError(
                        message=f"Decision validation failed: {messages}",
                        error_code="DECISION_VALIDATION_FAILED",
                    )

            # Always track the decision first
            await self.decision_tracker.track_decision(
                decision, publish_event=not offline, offline=offline
            )

            # Update decision status
            decision.update_status(DecisionStatus.EXECUTING)
            await self.decision_tracker.update_decision_status(
                decision.metadata.decision_id,
                DecisionStatus.EXECUTING,
                publish_event=not offline,
            )

            # Simulate execution (in a real implementation, this would perform the action)
            # For now, we just update the status to COMPLETED
            decision.update_status(DecisionStatus.COMPLETED)
            await self.decision_tracker.update_decision_status(
                decision.metadata.decision_id,
                DecisionStatus.COMPLETED,
                publish_event=not offline,
            )

            # Publish execution event if not offline
            if not offline:
                try:
                    await self.publisher.publish_notification(
                        notification_name="decision_executed",
                        data={
                            "decision_id": decision.metadata.decision_id,
                            "action": decision.action,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )
                    logger.debug(
                        f"Published decision_executed event for {decision.metadata.decision_id}"
                    )
                except Exception as e:
                    logger.error(f"Error publishing decision_executed event: {e}")

            return True
        except DecisionError:
            # Re-raise decision errors
            raise
        except Exception as e:
            logger.error(f"Error executing decision: {e}")
            raise DecisionError(
                message=f"Failed to execute decision: {e}",
                error_code="DECISION_EXECUTION_ERROR",
            )

    async def process_feedback(
        self,
        decision_id: str,
        feedback_data: Dict[str, Any],
        offline: bool = False,
        battery_efficient: bool = False,
    ) -> bool:
        """Process feedback on a decision and learn from it.

        Args:
            decision_id: ID of the decision
            feedback_data: Feedback data
            offline: Whether to process feedback in offline mode
            battery_efficient: Whether to use battery-efficient learning

        Returns:
            True if processing was successful, False otherwise

        Raises:
            DecisionError: If there is an error processing feedback
        """
        logger.debug(f"Processing feedback for decision {decision_id}")

        try:
            # Get the decision
            decision = await self.get_decision(decision_id)
            if not decision:
                raise DecisionError(
                    message=f"Decision {decision_id} not found",
                    error_code="DECISION_NOT_FOUND",
                )

            # Process feedback
            result, feedback_id = await self.feedback_processor.process_feedback(
                decision_id, feedback_data, publish_event=not offline, offline=offline
            )

            # Prepare learning data
            learning_data = {
                "decision_id": decision_id,
                "decision_type": decision.decision_type.value,
                "confidence": decision.confidence,
                "actual_outcome": feedback_data.get("outcome", "unknown"),
                "quality": feedback_data.get("quality", 0.5),
                "relevance": feedback_data.get("relevance", 0.5),
            }

            # Add device info if available
            if "battery_level" in feedback_data:
                learning_data["battery_level"] = feedback_data["battery_level"]

            if "network_type" in feedback_data:
                learning_data["network_type"] = feedback_data["network_type"]

            # Learn from feedback
            await self.learning_engine.learn_from_feedback(
                learning_data,
                publish_event=not offline,
                battery_efficient=battery_efficient,
            )

            return True
        except DecisionError:
            # Re-raise decision errors
            raise
        except Exception as e:
            logger.error(f"Error processing feedback: {e}")
            raise DecisionError(
                message=f"Failed to process feedback: {e}",
                error_code="FEEDBACK_PROCESSING_ERROR",
            )

    async def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID.

        Args:
            decision_id: ID of the decision to get

        Returns:
            The decision, or None if not found

        Raises:
            DecisionError: If there is an error getting the decision
        """
        logger.debug(f"Getting decision {decision_id}")

        try:
            return await self.decision_tracker.get_decision(decision_id)
        except Exception as e:
            logger.error(f"Error getting decision: {e}")
            raise DecisionError(
                message=f"Failed to get decision: {e}",
                error_code="DECISION_RETRIEVAL_ERROR",
            )

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

        Raises:
            DecisionError: If there is an error getting the history
        """
        logger.debug("Getting decision history")

        try:
            return await self.decision_tracker.get_decision_history(
                decision_id=decision_id, filters=filters
            )
        except Exception as e:
            logger.error(f"Error getting decision history: {e}")
            raise DecisionError(
                message=f"Failed to get decision history: {e}",
                error_code="DECISION_HISTORY_ERROR",
            )

    async def _apply_learning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply learning to the context.

        Args:
            context: Original context

        Returns:
            Adjusted context
        """
        # Create a copy of the context to avoid modifying the original
        adjusted_context = copy.deepcopy(context)

        # Add learning-based adjustments
        adjusted_context["learning_adjustments"] = {}

        # Add confidence adjustments for each decision type
        for decision_type in DecisionType:
            adjustment = await self.learning_engine.get_confidence_adjustment(
                decision_type
            )
            if adjustment != 0:
                adjusted_context["learning_adjustments"][
                    decision_type.value
                ] = adjustment

        return adjusted_context
