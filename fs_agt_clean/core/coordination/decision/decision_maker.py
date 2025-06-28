"""
Decision maker component for the FlipSync application.

This module provides the decision maker component for the Decision Pipeline,
which is responsible for making decisions based on context, options, and
constraints. It evaluates options and selects the best one based on various
factors.

The decision maker is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Extensible: Supporting custom decision-making strategies
"""

import abc
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.decision.interfaces import DecisionMaker
from fs_agt_clean.core.coordination.decision.models import (
    Decision,
    DecisionConfidence,
    DecisionError,
    DecisionStatus,
    DecisionType,
)

logger = logging.getLogger(__name__)


class BaseDecisionMaker(DecisionMaker):
    """Base class for decision makers."""

    def __init__(self, maker_id: str):
        """Initialize the decision maker.

        Args:
            maker_id: Unique identifier for this decision maker
        """
        self.maker_id = maker_id
        self.decisions: Dict[str, Decision] = {}
        logger.debug(f"Initialized decision maker {maker_id}")


class InMemoryDecisionMaker(BaseDecisionMaker):
    """In-memory implementation of a decision maker.

    This implementation stores decisions in memory and provides basic
    decision-making capabilities. It is suitable for testing and development,
    but not for production use with large numbers of decisions.
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
        logger.debug(f"Making decision with {len(options)} options")

        # Validate inputs
        if not options:
            raise DecisionError(
                message="No options provided for decision making",
                error_code="NO_OPTIONS",
            )

        # Apply constraints if provided
        filtered_options = options
        if constraints:
            filtered_options = self._apply_constraints(options, constraints)

        # Check for mobile optimization needs
        battery_efficient = False
        network_efficient = False

        device_info = context.get("device_info", {})
        battery_level = device_info.get("battery_level", 1.0)
        network_type = device_info.get("network_type", "wifi")

        # Enable battery efficiency if battery is low
        if battery_level < 0.3:
            battery_efficient = True
            logger.debug("Enabling battery efficiency due to low battery")

        # Enable network efficiency if on cellular network
        if network_type == "cellular":
            network_efficient = True
            logger.debug("Enabling network efficiency due to cellular network")

        # Score options
        scored_options = self._score_options(
            filtered_options, context, battery_efficient, network_efficient
        )

        # Select the best option
        best_option = max(scored_options, key=lambda x: x[1])
        selected_option_id = best_option[0]["id"]
        selected_confidence = best_option[1]

        # Generate alternatives (options not selected)
        alternatives = [
            option["id"]
            for option, _ in scored_options
            if option["id"] != selected_option_id
        ]

        # If we're using constraints, only include alternatives that meet the constraints
        if constraints:
            alternatives = [
                option_id
                for option_id in alternatives
                if any(opt["id"] == option_id for opt in filtered_options)
            ]

        # Generate reasoning
        reasoning = self._generate_reasoning(
            best_option[0], selected_confidence, context
        )

        # Create the decision
        decision = Decision.create(
            decision_type=DecisionType.SELECTION,
            action=selected_option_id,
            confidence=selected_confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            source=self.maker_id,
            context=context,
            battery_efficient=battery_efficient,
            network_efficient=network_efficient,
        )

        # Store the decision
        self.decisions[decision.metadata.decision_id] = decision

        logger.debug(
            f"Made decision {decision.metadata.decision_id} with confidence {selected_confidence:.2f}"
        )
        return decision

    async def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID.

        Args:
            decision_id: ID of the decision to get

        Returns:
            The decision, or None if not found
        """
        return self.decisions.get(decision_id)

    async def list_decisions(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Decision]:
        """List decisions matching the given filters.

        Args:
            filters: Optional filters to apply

        Returns:
            List of matching decisions
        """
        if not filters:
            return list(self.decisions.values())

        # Apply filters
        result = []
        for decision in self.decisions.values():
            if self._matches_filters(decision, filters):
                result.append(decision)

        return result

    def _apply_constraints(
        self, options: List[Dict[str, Any]], constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Apply constraints to options.

        Args:
            options: Available options
            constraints: Constraints to apply

        Returns:
            Filtered options

        Raises:
            DecisionError: If no options meet the constraints
        """
        result = []

        for option in options:
            if self._option_meets_constraints(option, constraints):
                result.append(option)

        if not result:
            raise DecisionError(
                message="No options meet the constraints",
                error_code="NO_VALID_OPTIONS",
                details={"constraints": constraints},
            )

        return result

    def _option_meets_constraints(
        self, option: Dict[str, Any], constraints: Dict[str, Any]
    ) -> bool:
        """Check if an option meets the constraints.

        Args:
            option: Option to check
            constraints: Constraints to apply

        Returns:
            True if the option meets the constraints, False otherwise
        """
        for key, value in constraints.items():
            if key not in option:
                continue

            if key == "min_value" and option.get("value", 0) < value:
                return False
            elif key == "max_value" and option.get("value", 0) > value:
                return False
            elif key == "allowed_values" and option.get("value") not in value:
                return False
            elif key == "required_tags" and not all(
                tag in option.get("tags", []) for tag in value
            ):
                return False

        return True

    def _score_options(
        self,
        options: List[Dict[str, Any]],
        context: Dict[str, Any],
        battery_efficient: bool,
        network_efficient: bool,
    ) -> List[Tuple[Dict[str, Any], float]]:
        """Score options based on context and constraints.

        Args:
            options: Available options
            context: Decision context
            battery_efficient: Whether to prioritize battery efficiency
            network_efficient: Whether to prioritize network efficiency

        Returns:
            List of (option, score) tuples
        """
        result = []

        for option in options:
            # Base score is the option's value if available, otherwise 0.5
            base_score = option.get("value", 50) / 100

            # Adjust for battery efficiency if needed
            if battery_efficient and "battery_cost" in option:
                # Lower battery cost is better
                battery_factor = 1.0 - option["battery_cost"]
                base_score = base_score * 0.5 + battery_factor * 0.5

            # Adjust for network efficiency if needed
            if network_efficient and "network_cost" in option:
                # Lower network cost is better
                network_factor = 1.0 - option["network_cost"]
                base_score = base_score * 0.7 + network_factor * 0.3

            # Clamp score to [0, 1]
            final_score = max(0.0, min(1.0, base_score))
            result.append((option, final_score))

        return result

    def _generate_reasoning(
        self, option: Dict[str, Any], confidence: float, context: Dict[str, Any]
    ) -> str:
        """Generate reasoning for a decision.

        Args:
            option: Selected option
            confidence: Confidence in the decision
            context: Decision context

        Returns:
            Reasoning string
        """
        reasons = []

        # Add option name if available
        if "name" in option:
            reasons.append(f"Selected '{option['name']}'")
        else:
            reasons.append(f"Selected option '{option['id']}'")

        # Add value-based reasoning if available
        if "value" in option:
            reasons.append(f"with value {option['value']}")

        # Add confidence
        reasons.append(f"with confidence {confidence:.2f}")

        # Add context-specific reasoning
        if "scenario" in context:
            reasons.append(f"for scenario '{context['scenario']}'")

        # Add mobile optimization reasoning
        device_info = context.get("device_info", {})
        if "battery_level" in device_info and device_info["battery_level"] < 0.3:
            reasons.append("considering low battery level")

        if "network_type" in device_info and device_info["network_type"] == "cellular":
            reasons.append("optimizing for cellular network")

        return " ".join(reasons)

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

        return True
