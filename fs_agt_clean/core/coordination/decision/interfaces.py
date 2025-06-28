"""
Decision Pipeline interfaces for the FlipSync application.

This module provides the core interfaces for the Decision Pipeline component,
defining the contracts that implementations must follow. These interfaces
ensure consistent behavior across different implementations and enable
dependency injection and testing.

The interfaces are designed to be:
- Mobile-optimized: Supporting efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Extensible: Supporting future decision types and workflows
"""

import abc
from typing import Any, Dict, List, Optional, Tuple, Union

from fs_agt_clean.core.coordination.decision.models import Decision, DecisionStatus


class DecisionMaker(abc.ABC):
    """Interface for decision makers.

    A decision maker is responsible for making decisions based on context,
    options, and constraints. It evaluates options and selects the best one
    based on various factors.
    """

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    async def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID.

        Args:
            decision_id: ID of the decision to get

        Returns:
            The decision, or None if not found

        Raises:
            DecisionError: If there is an error getting the decision
        """
        pass

    @abc.abstractmethod
    async def list_decisions(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Decision]:
        """List decisions matching the given filters.

        Args:
            filters: Optional filters to apply

        Returns:
            List of matching decisions

        Raises:
            DecisionError: If there is an error listing decisions
        """
        pass


class DecisionValidator(abc.ABC):
    """Interface for decision validators.

    A decision validator is responsible for validating decisions against
    rules and constraints. It ensures that decisions are valid and can be
    executed.
    """

    @abc.abstractmethod
    async def validate_decision(self, decision: Decision) -> Tuple[bool, List[str]]:
        """Validate a decision against rules and constraints.

        Args:
            decision: The decision to validate

        Returns:
            Tuple of (is_valid, validation_messages)

        Raises:
            DecisionError: If there is an error validating the decision
        """
        pass

    @abc.abstractmethod
    async def add_validation_rule(self, rule_name: str, rule_function: Any) -> bool:
        """Add a validation rule.

        Args:
            rule_name: Name of the rule
            rule_function: Function that implements the rule

        Returns:
            True if the rule was added, False otherwise

        Raises:
            DecisionError: If there is an error adding the rule
        """
        pass

    @abc.abstractmethod
    async def remove_validation_rule(self, rule_name: str) -> bool:
        """Remove a validation rule.

        Args:
            rule_name: Name of the rule to remove

        Returns:
            True if the rule was removed, False otherwise

        Raises:
            DecisionError: If there is an error removing the rule
        """
        pass

    @abc.abstractmethod
    async def list_validation_rules(self) -> List[str]:
        """List all validation rules.

        Returns:
            List of rule names

        Raises:
            DecisionError: If there is an error listing rules
        """
        pass


class DecisionTracker(abc.ABC):
    """Interface for decision trackers.

    A decision tracker is responsible for tracking decisions and their
    outcomes. It maintains a history of decisions and provides metrics
    on decision quality.
    """

    @abc.abstractmethod
    async def track_decision(self, decision: Decision) -> bool:
        """Track a decision.

        Args:
            decision: The decision to track

        Returns:
            True if the decision was tracked, False otherwise

        Raises:
            DecisionError: If there is an error tracking the decision
        """
        pass

    @abc.abstractmethod
    async def update_decision_status(
        self, decision_id: str, status: DecisionStatus
    ) -> bool:
        """Update the status of a decision.

        Args:
            decision_id: ID of the decision to update
            status: New status

        Returns:
            True if the status was updated, False otherwise

        Raises:
            DecisionError: If there is an error updating the status
        """
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    async def get_decision_metrics(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get metrics on decisions.

        Args:
            filters: Optional filters to apply

        Returns:
            Dictionary of metrics

        Raises:
            DecisionError: If there is an error getting metrics
        """
        pass


class FeedbackProcessor(abc.ABC):
    """Interface for feedback processors.

    A feedback processor is responsible for processing feedback on decision
    outcomes. It collects feedback and prepares it for learning.
    """

    @abc.abstractmethod
    async def process_feedback(
        self, decision_id: str, feedback_data: Dict[str, Any]
    ) -> bool:
        """Process feedback on a decision.

        Args:
            decision_id: ID of the decision
            feedback_data: Feedback data

        Returns:
            True if the feedback was processed, False otherwise

        Raises:
            DecisionError: If there is an error processing feedback
        """
        pass

    @abc.abstractmethod
    async def get_feedback(self, feedback_id: str) -> Optional[Dict[str, Any]]:
        """Get feedback by ID.

        Args:
            feedback_id: ID of the feedback to get

        Returns:
            The feedback, or None if not found

        Raises:
            DecisionError: If there is an error getting feedback
        """
        pass

    @abc.abstractmethod
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
        pass


class LearningEngine(abc.ABC):
    """Interface for learning engines.

    A learning engine is responsible for learning from decision outcomes
    and feedback. It adapts decision-making strategies based on past
    performance.
    """

    @abc.abstractmethod
    async def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> bool:
        """Learn from feedback on decision outcomes.

        Args:
            feedback_data: Feedback data

        Returns:
            True if learning was successful, False otherwise

        Raises:
            DecisionError: If there is an error learning from feedback
        """
        pass

    @abc.abstractmethod
    async def get_learning_metrics(self) -> Dict[str, Any]:
        """Get metrics on learning.

        Returns:
            Dictionary of metrics

        Raises:
            DecisionError: If there is an error getting metrics
        """
        pass

    @abc.abstractmethod
    async def reset_learning(self) -> bool:
        """Reset learning state.

        Returns:
            True if reset was successful, False otherwise

        Raises:
            DecisionError: If there is an error resetting learning
        """
        pass


class DecisionPipeline(abc.ABC):
    """Interface for decision pipelines.

    A decision pipeline orchestrates the entire decision-making process,
    from making a decision to executing it and learning from the outcome.
    It combines all the other components into a cohesive workflow.
    """

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    async def validate_decision(self, decision: Decision) -> Tuple[bool, List[str]]:
        """Validate a decision against rules and constraints.

        Args:
            decision: The decision to validate

        Returns:
            Tuple of (is_valid, validation_messages)

        Raises:
            DecisionError: If there is an error validating the decision
        """
        pass

    @abc.abstractmethod
    async def execute_decision(self, decision: Decision) -> bool:
        """Execute a decision.

        Args:
            decision: The decision to execute

        Returns:
            True if execution was successful, False otherwise

        Raises:
            DecisionError: If there is an error executing the decision
        """
        pass

    @abc.abstractmethod
    async def process_feedback(
        self, decision_id: str, feedback_data: Dict[str, Any]
    ) -> bool:
        """Process feedback on a decision and learn from it.

        Args:
            decision_id: ID of the decision
            feedback_data: Feedback data

        Returns:
            True if processing was successful, False otherwise

        Raises:
            DecisionError: If there is an error processing feedback
        """
        pass

    @abc.abstractmethod
    async def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID.

        Args:
            decision_id: ID of the decision to get

        Returns:
            The decision, or None if not found

        Raises:
            DecisionError: If there is an error getting the decision
        """
        pass

    @abc.abstractmethod
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
        pass
