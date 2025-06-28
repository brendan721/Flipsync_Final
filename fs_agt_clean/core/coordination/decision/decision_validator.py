"""
Decision validator component for the FlipSync application.

This module provides the decision validator component for the Decision Pipeline,
which is responsible for validating decisions against rules and constraints.
It ensures that decisions are valid and can be executed.

The decision validator is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Extensible: Supporting custom validation rules
"""

import abc
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.decision.interfaces import DecisionValidator
from fs_agt_clean.core.coordination.decision.models import (
    Decision,
    DecisionConfidence,
    DecisionError,
    DecisionStatus,
    DecisionType,
)

logger = logging.getLogger(__name__)


# Type for validation rule functions
ValidationRule = Callable[[Decision], Tuple[bool, Optional[str]]]


class BaseDecisionValidator(DecisionValidator):
    """Base class for decision validators."""

    def __init__(self, validator_id: str):
        """Initialize the decision validator.

        Args:
            validator_id: Unique identifier for this validator
        """
        self.validator_id = validator_id
        logger.debug(f"Initialized decision validator {validator_id}")


class RuleBasedValidator(BaseDecisionValidator):
    """Rule-based implementation of a decision validator.

    This implementation validates decisions against a set of rules. Each rule
    is a function that takes a decision and returns a tuple of (is_valid, message).
    If is_valid is False, the message explains why the decision is invalid.
    """

    def __init__(self, validator_id: str):
        """Initialize the rule-based validator.

        Args:
            validator_id: Unique identifier for this validator
        """
        super().__init__(validator_id)
        self.rules: Dict[str, ValidationRule] = {}

    async def validate_decision(self, decision: Decision) -> Tuple[bool, List[str]]:
        """Validate a decision against rules and constraints.

        Args:
            decision: The decision to validate

        Returns:
            Tuple of (is_valid, validation_messages)
        """
        logger.debug(f"Validating decision {decision.metadata.decision_id}")

        # If no rules, decision is valid
        if not self.rules:
            return True, []

        # Apply all rules
        is_valid = True
        messages = []

        for rule_name, rule_function in self.rules.items():
            rule_result, rule_message = await rule_function(decision)

            if not rule_result:
                is_valid = False
                messages.append(f"{rule_name}: {rule_message}")

        if is_valid:
            logger.debug(f"Decision {decision.metadata.decision_id} is valid")
        else:
            logger.debug(
                f"Decision {decision.metadata.decision_id} is invalid: {messages}"
            )

        return is_valid, messages

    async def add_validation_rule(
        self, rule_name: str, rule_function: ValidationRule
    ) -> bool:
        """Add a validation rule.

        Args:
            rule_name: Name of the rule
            rule_function: Function that implements the rule

        Returns:
            True if the rule was added, False otherwise

        Raises:
            DecisionError: If the rule already exists
        """
        if rule_name in self.rules:
            raise DecisionError(
                message=f"Rule {rule_name} already exists", error_code="RULE_EXISTS"
            )

        self.rules[rule_name] = rule_function
        logger.debug(f"Added validation rule {rule_name}")
        return True

    async def remove_validation_rule(self, rule_name: str) -> bool:
        """Remove a validation rule.

        Args:
            rule_name: Name of the rule to remove

        Returns:
            True if the rule was removed, False otherwise
        """
        if rule_name not in self.rules:
            logger.debug(f"Rule {rule_name} not found")
            return False

        del self.rules[rule_name]
        logger.debug(f"Removed validation rule {rule_name}")
        return True

    async def list_validation_rules(self) -> List[str]:
        """List all validation rules.

        Returns:
            List of rule names
        """
        return list(self.rules.keys())

    async def add_built_in_rule(self, rule_name: str, **kwargs: Any) -> bool:
        """Add a built-in validation rule.

        Args:
            rule_name: Name of the built-in rule
            **kwargs: Parameters for the rule

        Returns:
            True if the rule was added, False otherwise

        Raises:
            DecisionError: If the rule already exists or is not a valid built-in rule
        """
        if rule_name == "minimum_confidence":
            min_confidence = kwargs.get("min_confidence", 0.5)

            async def minimum_confidence_rule(
                decision: Decision,
            ) -> Tuple[bool, Optional[str]]:
                if decision.confidence < min_confidence:
                    return (
                        False,
                        f"Confidence too low ({decision.confidence:.2f} < {min_confidence:.2f})",
                    )
                return True, None

            return await self.add_validation_rule(
                "minimum_confidence", minimum_confidence_rule
            )

        elif rule_name == "required_reasoning":
            min_length = kwargs.get("min_length", 10)

            async def required_reasoning_rule(
                decision: Decision,
            ) -> Tuple[bool, Optional[str]]:
                if not decision.reasoning or len(decision.reasoning) < min_length:
                    return (
                        False,
                        f"Reasoning too short or missing (min length: {min_length})",
                    )
                return True, None

            return await self.add_validation_rule(
                "required_reasoning", required_reasoning_rule
            )

        elif rule_name == "allowed_decision_types":
            allowed_types = kwargs.get("allowed_types", set(DecisionType))

            async def allowed_decision_types_rule(
                decision: Decision,
            ) -> Tuple[bool, Optional[str]]:
                if decision.decision_type not in allowed_types:
                    return False, f"Decision type {decision.decision_type} not allowed"
                return True, None

            return await self.add_validation_rule(
                "allowed_decision_types", allowed_decision_types_rule
            )

        elif rule_name == "battery_efficiency":
            required = kwargs.get("required", False)

            async def battery_efficiency_rule(
                decision: Decision,
            ) -> Tuple[bool, Optional[str]]:
                if required and not decision.battery_efficient:
                    return False, "Battery efficiency required but not provided"
                return True, None

            return await self.add_validation_rule(
                "battery_efficiency", battery_efficiency_rule
            )

        elif rule_name == "network_efficiency":
            required = kwargs.get("required", False)

            async def network_efficiency_rule(
                decision: Decision,
            ) -> Tuple[bool, Optional[str]]:
                if required and not decision.network_efficient:
                    return False, "Network efficiency required but not provided"
                return True, None

            return await self.add_validation_rule(
                "network_efficiency", network_efficiency_rule
            )

        else:
            raise DecisionError(
                message=f"Unknown built-in rule: {rule_name}", error_code="UNKNOWN_RULE"
            )
