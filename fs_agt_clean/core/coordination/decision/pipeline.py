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

import asyncio
import copy
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

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
)
from fs_agt_clean.core.decision.rule_engine import FlipSyncRuleEngine

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

        # PERFORMANCE OPTIMIZATION: Add decision cache
        self._decision_cache: Dict[str, tuple] = (
            {}
        )  # {context_hash: (decision, timestamp)}
        self._cache_ttl = 60  # 1 minute cache for similar decisions

        logger.debug(f"Initialized decision pipeline {pipeline_id}")


class StandardDecisionPipeline(BaseDecisionPipeline):
    """Standard implementation of a decision pipeline.

    This implementation provides a standard decision-making workflow:
    1. Apply rule engine for algorithmic decision-making
    2. Make a decision
    3. Validate the decision
    4. Execute the decision
    5. Process feedback
    6. Learn from feedback

    It is designed to be mobile-optimized and vision-aligned.
    """

    def __init__(self, *args, **kwargs):
        """Initialize StandardDecisionPipeline with integrated rule engine."""
        super().__init__(*args, **kwargs)

        # Initialize integrated FlipSyncRuleEngine for algorithmic decisions
        self.rule_engine = FlipSyncRuleEngine(
            cache_size=10000, cache_ttl=300  # 5 minutes cache for rule evaluations
        )

        logger.info(
            "StandardDecisionPipeline initialized with integrated FlipSyncRuleEngine"
        )

    async def _apply_rule_engine(
        self,
        context: Dict[str, Any],
        options: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Optional[Decision]:
        """Apply FlipSyncRuleEngine for algorithmic decision-making.

        Args:
            context: Decision context
            options: Available options
            constraints: Optional constraints

        Returns:
            Decision if rule engine can make one, None otherwise
        """
        try:
            # Convert context to rule engine format
            rule_context = {
                "agent_type": context.get("agent_type", "unknown"),
                "decision_type": context.get("decision_type", "general"),
                "marketplace": context.get("marketplace", "ebay"),
                "priority": context.get("priority", "medium"),
                **context,
            }

            # Create DecisionContext for rule engine
            from fs_agt_clean.core.decision.rule_engine import DecisionContext

            decision_context = DecisionContext(
                context_id=f"decision_{hash(str(rule_context))}",
                agent_type=rule_context["agent_type"],
                decision_type=rule_context["decision_type"],
                input_data=rule_context,
            )

            # Evaluate using rule engine
            rule_result = await self.rule_engine.make_decision(decision_context)

            if rule_result and rule_result.confidence_score > 0.7:
                # Create decision from rule result
                from fs_agt_clean.core.coordination.decision.models import (
                    DecisionMetadata,
                )

                decision = Decision(
                    decision_id=rule_result.decision_id,
                    decision_type=DecisionType.ALGORITHMIC,
                    content=str(rule_result.result_data),
                    confidence=(
                        DecisionConfidence.HIGH
                        if rule_result.confidence_score > 0.8
                        else DecisionConfidence.MEDIUM
                    ),
                    metadata=DecisionMetadata(
                        decision_id=rule_result.decision_id,
                        timestamp=datetime.now(timezone.utc),
                        context=rule_context,
                        source="FlipSyncRuleEngine",
                    ),
                )

                logger.info(
                    f"Rule engine decision: {rule_result.confidence_score:.2f} confidence"
                )
                return decision

            return None

        except Exception as e:
            logger.warning(f"Rule engine evaluation failed: {e}")
            return None

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
            # PERFORMANCE OPTIMIZATION: Check decision cache first
            context_hash = self._hash_context(context, options, constraints)
            current_time = datetime.now(timezone.utc)

            if context_hash in self._decision_cache:
                cached_decision, cached_time = self._decision_cache[context_hash]
                if (current_time - cached_time).total_seconds() < self._cache_ttl:
                    logger.debug("Using cached decision")
                    return cached_decision

            # Apply confidence adjustment based on learning
            adjusted_context = await self._apply_learning(context)

            # INTEGRATED: Apply FlipSyncRuleEngine for algorithmic decision-making
            rule_decision = await self._apply_rule_engine(
                adjusted_context, options, constraints
            )

            if rule_decision:
                logger.info("Decision made using FlipSyncRuleEngine (algorithmic)")
                decision = rule_decision
            else:
                # Fallback to standard decision maker
                logger.info("Falling back to standard decision maker")
                decision = await self.decision_maker.make_decision(
                    adjusted_context, options, constraints
                )

            # PERFORMANCE OPTIMIZATION: Cache the decision
            self._decision_cache[context_hash] = (decision, current_time)

            # Track the decision (run in background to not block)
            asyncio.create_task(self.decision_tracker.track_decision(decision))

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
        """Apply learning to the context with performance optimization.

        Args:
            context: Original context

        Returns:
            Adjusted context
        """
        # Create a copy of the context to avoid modifying the original
        adjusted_context = copy.deepcopy(context)

        # Add learning-based adjustments
        adjusted_context["learning_adjustments"] = {}

        try:
            # PERFORMANCE OPTIMIZATION: Skip learning adjustments for better performance
            # In Docker environment, learning adjustments cause significant delays
            # This can be re-enabled when performance is optimized
            skip_learning_adjustments = True

            if skip_learning_adjustments:
                logger.debug(
                    "Skipping learning adjustments for performance optimization"
                )
                return adjusted_context

            # PERFORMANCE OPTIMIZATION: Parallelize confidence adjustment queries
            # Instead of sequential queries, fetch all adjustments in parallel
            adjustment_tasks = [
                self.learning_engine.get_confidence_adjustment(decision_type)
                for decision_type in DecisionType
            ]

            # Execute all queries in parallel with timeout (increased for Docker)
            adjustments = await asyncio.wait_for(
                asyncio.gather(*adjustment_tasks, return_exceptions=True),
                timeout=1.0,  # Increased to 1000ms for Docker environment
            )

            # Process results
            for decision_type, adjustment in zip(DecisionType, adjustments):
                if isinstance(adjustment, Exception):
                    logger.warning(
                        f"Failed to get adjustment for {decision_type}: {adjustment}"
                    )
                    continue

                if adjustment != 0:
                    adjusted_context["learning_adjustments"][
                        decision_type.value
                    ] = adjustment

        except asyncio.TimeoutError:
            logger.warning(
                "Learning adjustment queries timed out, proceeding without adjustments"
            )
        except Exception as e:
            logger.warning(f"Error applying learning adjustments: {e}")

        return adjusted_context

    def _hash_context(
        self,
        context: Dict[str, Any],
        options: List[Any],
        constraints: Optional[Dict[str, Any]],
    ) -> str:
        """PERFORMANCE OPTIMIZATION: Create a hash of the decision context for caching."""
        try:
            # Create a simplified representation for hashing
            hash_data = {
                "query_type": context.get("query_type", ""),
                "product_info": str(context.get("product_info", {}))[
                    :100
                ],  # Limit size
                "options_count": len(options) if options else 0,
                "constraints": str(constraints)[:50] if constraints else "",
            }

            # Create hash
            hash_string = json.dumps(hash_data, sort_keys=True)
            return hashlib.md5(hash_string.encode()).hexdigest()
        except Exception:
            # Fallback to timestamp-based hash if serialization fails
            return hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()
