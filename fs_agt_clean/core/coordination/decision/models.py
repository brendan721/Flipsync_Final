"""
Decision models for the FlipSync application.

This module provides the core data models for the Decision Pipeline component,
including the Decision class, decision types, status, and related metadata.

The models are designed to be:
- Mobile-optimized: Efficient serialization and minimal memory footprint
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive validation and error handling
- Extensible: Supporting future decision types and metadata
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union


class DecisionType(str, Enum):
    """Types of decisions that can be made by the system."""

    ACTION = "action"  # Decision to take an action
    RECOMMENDATION = "recommendation"  # Decision to recommend something
    OPTIMIZATION = "optimization"  # Decision to optimize something
    ALLOCATION = "allocation"  # Decision to allocate resources
    PRIORITIZATION = "prioritization"  # Decision to prioritize something
    SCHEDULING = "scheduling"  # Decision to schedule something
    SELECTION = "selection"  # Decision to select something
    CLASSIFICATION = "classification"  # Decision to classify something
    PREDICTION = "prediction"  # Decision to predict something
    CUSTOM = "custom"  # Custom decision type


class DecisionStatus(str, Enum):
    """Status of a decision in the system."""

    PENDING = "pending"  # Decision is pending
    VALIDATING = "validating"  # Decision is being validated
    APPROVED = "approved"  # Decision has been approved
    REJECTED = "rejected"  # Decision has been rejected
    EXECUTING = "executing"  # Decision is being executed
    COMPLETED = "completed"  # Decision has been completed
    FAILED = "failed"  # Decision execution failed
    CANCELED = "canceled"  # Decision was canceled
    EXPIRED = "expired"  # Decision has expired


class DecisionConfidence(Enum):
    """Standardized confidence levels for decisions."""

    VERY_HIGH = 0.9  # Very high confidence (90%+)
    HIGH = 0.75  # High confidence (75-90%)
    MEDIUM = 0.5  # Medium confidence (50-75%)
    LOW = 0.0  # Low confidence (0-50%)


class DecisionMetadata:
    """Metadata for a decision."""

    def __init__(
        self,
        decision_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        causation_id: Optional[str] = None,
        version: str = "1.0",
        source: Optional[str] = None,
        target: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        status: DecisionStatus = DecisionStatus.PENDING,
        retry_count: int = 0,
        max_retries: int = 3,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        custom: Optional[Dict[str, Any]] = None,
    ):
        """Initialize decision metadata.

        Args:
            decision_id: Unique identifier for the decision
            correlation_id: ID for correlating related decisions
            causation_id: ID of the decision that caused this one
            version: Version of the decision model
            source: Source of the decision (e.g., agent ID)
            target: Target of the decision (e.g., agent ID)
            created_at: When the decision was created
            updated_at: When the decision was last updated
            status: Current status of the decision
            retry_count: Number of times the decision has been retried
            max_retries: Maximum number of retries allowed
            conversation_id: ID of the conversation this decision is part of
            user_id: ID of the user this decision is for
            custom: Custom metadata
        """
        self.decision_id = decision_id or str(uuid.uuid4())
        self.correlation_id = correlation_id
        self.causation_id = causation_id
        self.version = version
        self.source = source
        self.target = target
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or self.created_at
        self.status = status
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.custom = custom or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary.

        Returns:
            Dictionary representation of the metadata
        """
        return {
            "decision_id": self.decision_id,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "version": self.version,
            "source": self.source,
            "target": self.target,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status.value,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "custom": self.custom,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionMetadata":
        """Create metadata from a dictionary.

        Args:
            data: Dictionary representation of the metadata

        Returns:
            DecisionMetadata instance
        """
        # Convert string timestamps to datetime objects
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if updated_at and isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        # Convert string status to enum
        status = data.get("status")
        if status and isinstance(status, str):
            status = DecisionStatus(status)

        return cls(
            decision_id=data.get("decision_id"),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
            version=data.get("version", "1.0"),
            source=data.get("source"),
            target=data.get("target"),
            created_at=created_at,
            updated_at=updated_at,
            status=status or DecisionStatus.PENDING,
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            conversation_id=data.get("conversation_id"),
            user_id=data.get("user_id"),
            custom=data.get("custom", {}),
        )

    def to_json(self) -> str:
        """Convert metadata to a JSON string.

        Returns:
            JSON string representation of the metadata
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "DecisionMetadata":
        """Create metadata from a JSON string.

        Args:
            json_str: JSON string representation of the metadata

        Returns:
            DecisionMetadata instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)


class Decision:
    """Decision model for the Decision Pipeline component."""

    def __init__(
        self,
        decision_type: DecisionType,
        action: str,
        confidence: float,
        reasoning: str,
        alternatives: Optional[List[str]] = None,
        metadata: Optional[DecisionMetadata] = None,
        context: Optional[Dict[str, Any]] = None,
        battery_efficient: bool = False,
        network_efficient: bool = False,
    ):
        """Initialize a decision.

        Args:
            decision_type: Type of decision
            action: Action to take
            confidence: Confidence level (0.0 to 1.0)
            reasoning: Reasoning behind the decision
            alternatives: Alternative actions that were considered
            metadata: Decision metadata
            context: Context in which the decision was made
            battery_efficient: Whether the decision is battery-efficient
            network_efficient: Whether the decision is network-efficient
        """
        self.decision_type = decision_type
        self.action = action
        self.confidence = confidence
        self.reasoning = reasoning
        self.alternatives = alternatives or []
        self.metadata = metadata or DecisionMetadata()
        self.context = context or {}
        self.battery_efficient = battery_efficient
        self.network_efficient = network_efficient

    @property
    def confidence_level(self) -> DecisionConfidence:
        """Get standardized confidence level.

        Returns:
            Standardized confidence level
        """
        if self.confidence >= DecisionConfidence.VERY_HIGH.value:
            return DecisionConfidence.VERY_HIGH
        elif self.confidence >= DecisionConfidence.HIGH.value:
            return DecisionConfidence.HIGH
        elif self.confidence >= DecisionConfidence.MEDIUM.value:
            return DecisionConfidence.MEDIUM
        return DecisionConfidence.LOW

    def update_status(self, status: DecisionStatus) -> None:
        """Update the decision status.

        Args:
            status: New status
        """
        self.metadata.status = status
        self.metadata.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert decision to a dictionary.

        Returns:
            Dictionary representation of the decision
        """
        return {
            "decision_type": self.decision_type.value,
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "alternatives": self.alternatives,
            "metadata": self.metadata.to_dict(),
            "context": self.context,
            "battery_efficient": self.battery_efficient,
            "network_efficient": self.network_efficient,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Decision":
        """Create a decision from a dictionary.

        Args:
            data: Dictionary representation of the decision

        Returns:
            Decision instance
        """
        # Convert string decision type to enum
        decision_type = data.get("decision_type")
        if decision_type and isinstance(decision_type, str):
            decision_type = DecisionType(decision_type)

        # Create metadata from dict
        metadata_dict = data.get("metadata", {})
        metadata = DecisionMetadata.from_dict(metadata_dict)

        return cls(
            decision_type=decision_type,
            action=data.get("action", ""),
            confidence=data.get("confidence", 0.0),
            reasoning=data.get("reasoning", ""),
            alternatives=data.get("alternatives", []),
            metadata=metadata,
            context=data.get("context", {}),
            battery_efficient=data.get("battery_efficient", False),
            network_efficient=data.get("network_efficient", False),
        )

    def to_json(self) -> str:
        """Convert decision to a JSON string.

        Returns:
            JSON string representation of the decision
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "Decision":
        """Create a decision from a JSON string.

        Args:
            json_str: JSON string representation of the decision

        Returns:
            Decision instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    @classmethod
    def create(
        cls,
        decision_type: DecisionType,
        action: str,
        confidence: float,
        reasoning: str,
        alternatives: Optional[List[str]] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        battery_efficient: bool = False,
        network_efficient: bool = False,
    ) -> "Decision":
        """Create a decision with metadata.

        Args:
            decision_type: Type of decision
            action: Action to take
            confidence: Confidence level (0.0 to 1.0)
            reasoning: Reasoning behind the decision
            alternatives: Alternative actions that were considered
            source: Source of the decision (e.g., agent ID)
            target: Target of the decision (e.g., agent ID)
            context: Context in which the decision was made
            battery_efficient: Whether the decision is battery-efficient
            network_efficient: Whether the decision is network-efficient

        Returns:
            Decision instance with metadata
        """
        metadata = DecisionMetadata(source=source, target=target)

        return cls(
            decision_type=decision_type,
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=alternatives,
            metadata=metadata,
            context=context,
            battery_efficient=battery_efficient,
            network_efficient=network_efficient,
        )


class DecisionError(Exception):
    """Error raised by the Decision Pipeline component."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a decision error.

        Args:
            message: Error message
            error_code: Error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "DECISION_ERROR"
        self.details = details or {}

    def __str__(self) -> str:
        """Get string representation of the error.

        Returns:
            String representation
        """
        return f"{self.error_code}: {self.message}"
