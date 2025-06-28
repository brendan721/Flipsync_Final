"""
Validation module for the FlipSync Decision Engine type system.
Provides validation functions for all core types and utilities for validation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fs_agt_clean.core.brain.types import (
    Decision,
    DecisionConfidence,
    Memory,
    MemoryImportance,
    Pattern,
    PatternType,
    Strategy,
    ValidationResult,
)


def validate_confidence(confidence: float) -> ValidationResult:
    """Validate a confidence value."""
    errors = []
    if not isinstance(confidence, (int, float)):
        errors.append(f"Confidence must be a number, got {type(confidence)}")
    elif not 0.0 <= confidence <= 1.0:
        errors.append(f"Confidence must be between 0.0 and 1.0, got {confidence}")
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_timestamp(timestamp: datetime) -> ValidationResult:
    """Validate a timestamp."""
    errors = []
    if not isinstance(timestamp, datetime):
        errors.append(f"Timestamp must be a datetime object, got {type(timestamp)}")
    elif timestamp.tzinfo is None:
        errors.append("Timestamp must be timezone-aware")
    elif timestamp > datetime.now(timezone.utc):
        errors.append("Timestamp cannot be in the future")
    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_metadata(metadata: Dict[str, Any]) -> ValidationResult:
    """Validate metadata structure."""
    errors = []
    if not isinstance(metadata, dict):
        errors.append(f"Metadata must be a dictionary, got {type(metadata)}")
    else:
        # Check for non-serializable types
        try:
            import json

            json.dumps(metadata)
        except (TypeError, ValueError) as e:
            errors.append(f"Metadata must be JSON serializable: {str(e)}")

        # Check for sensitive patterns
        sensitive_patterns = ["password", "token", "secret", "key", "auth"]
        found_sensitive = [
            k
            for k in metadata.keys()
            if any(p in k.lower() for p in sensitive_patterns)
        ]
        if found_sensitive:
            errors.append(
                f"Metadata contains potentially sensitive keys: {found_sensitive}"
            )

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_pattern(pattern: Pattern) -> ValidationResult:
    """Validate a Pattern instance."""
    errors = []

    # Validate type
    if not isinstance(pattern.type, PatternType):
        errors.append(
            f"Pattern type must be a PatternType enum, got {type(pattern.type)}"
        )

    # Validate name
    if not pattern.name or not isinstance(pattern.name, str):
        errors.append("Pattern name must be a non-empty string")

    # Validate confidence
    confidence_result = validate_confidence(pattern.confidence)
    if not confidence_result:
        errors.extend(confidence_result.errors)

    # Validate metadata
    metadata_result = validate_metadata(pattern.metadata)
    if not metadata_result:
        errors.extend(metadata_result.errors)

    # Validate timestamp
    timestamp_result = validate_timestamp(pattern.timestamp)
    if not timestamp_result:
        errors.extend(timestamp_result.errors)

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_decision(decision: Decision) -> ValidationResult:
    """Validate a Decision instance."""
    errors = []

    # Validate action
    if not decision.action or not isinstance(decision.action, str):
        errors.append("Decision action must be a non-empty string")

    # Validate confidence
    confidence_result = validate_confidence(decision.confidence)
    if not confidence_result:
        errors.extend(confidence_result.errors)

    # Validate reasoning
    if not decision.reasoning or not isinstance(decision.reasoning, str):
        errors.append("Decision reasoning must be a non-empty string")

    # Validate patterns
    for pattern in decision.patterns:
        pattern_result = validate_pattern(pattern)
        if not pattern_result:
            errors.extend(
                [f"Pattern validation error: {e}" for e in pattern_result.errors]
            )

    # Validate metadata
    metadata_result = validate_metadata(decision.metadata)
    if not metadata_result:
        errors.extend(metadata_result.errors)

    # Validate timestamp
    timestamp_result = validate_timestamp(decision.timestamp)
    if not timestamp_result:
        errors.extend(timestamp_result.errors)

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_strategy(strategy: Strategy) -> ValidationResult:
    """Validate a Strategy instance."""
    errors = []

    # Validate ID
    if not strategy.id or not isinstance(strategy.id, str):
        errors.append("Strategy ID must be a non-empty string")

    # Validate name
    if not strategy.name or not isinstance(strategy.name, str):
        errors.append("Strategy name must be a non-empty string")

    # Validate weights
    if not isinstance(strategy.weights, dict):
        errors.append(
            f"Strategy weights must be a dictionary, got {type(strategy.weights)}"
        )
    else:
        for action, weight in strategy.weights.items():
            if not isinstance(action, str):
                errors.append(
                    f"Strategy weight key must be a string, got {type(action)}"
                )
            if not isinstance(weight, (int, float)):
                errors.append(
                    f"Strategy weight value must be a number, got {type(weight)}"
                )
            elif not 0.0 <= weight <= 1.0:
                errors.append(
                    f"Strategy weight must be between 0.0 and 1.0, got {weight}"
                )

    # Validate metadata
    metadata_result = validate_metadata(strategy.metadata)
    if not metadata_result:
        errors.extend(metadata_result.errors)

    # Validate timestamp
    timestamp_result = validate_timestamp(strategy.last_updated)
    if not timestamp_result:
        errors.extend(timestamp_result.errors)

    return ValidationResult(valid=len(errors) == 0, errors=errors)


def validate_memory(memory: Memory) -> ValidationResult:
    """Validate a Memory instance."""
    errors = []

    # Validate content
    if not isinstance(memory.content, dict):
        errors.append(
            f"Memory content must be a dictionary, got {type(memory.content)}"
        )

    # Validate context
    if not isinstance(memory.context, dict):
        errors.append(
            f"Memory context must be a dictionary, got {type(memory.context)}"
        )

    # Validate importance
    importance_result = validate_confidence(
        memory.importance
    )  # Reuse confidence validation
    if not importance_result:
        errors.extend(
            [f"Importance validation error: {e}" for e in importance_result.errors]
        )

    # Validate tags
    if not isinstance(memory.tags, set):
        errors.append(f"Memory tags must be a set, got {type(memory.tags)}")
    else:
        for tag in memory.tags:
            if not isinstance(tag, str):
                errors.append(f"Memory tag must be a string, got {type(tag)}")

    # Validate TTL
    if memory.ttl is not None and not isinstance(memory.ttl, int):
        errors.append(f"Memory TTL must be None or an integer, got {type(memory.ttl)}")
    elif isinstance(memory.ttl, int) and memory.ttl <= 0:
        errors.append(f"Memory TTL must be positive, got {memory.ttl}")

    # Validate timestamp
    timestamp_result = validate_timestamp(memory.timestamp)
    if not timestamp_result:
        errors.extend(timestamp_result.errors)

    return ValidationResult(valid=len(errors) == 0, errors=errors)


# Utility function for batch validation
def validate_all(
    items: Union[List[Pattern], List[Decision], List[Strategy], List[Memory]],
) -> Dict[int, ValidationResult]:
    """Validate a list of items of the same type."""
    results = {}
    for i, item in enumerate(items):
        if isinstance(item, Pattern):
            results[i] = validate_pattern(item)
        elif isinstance(item, Decision):
            results[i] = validate_decision(item)
        elif isinstance(item, Strategy):
            results[i] = validate_strategy(item)
        elif isinstance(item, Memory):
            results[i] = validate_memory(item)
        else:
            results[i] = ValidationResult(
                valid=False, errors=[f"Unknown type for validation: {type(item)}"]
            )
    return results


__all__ = [
    "validate_confidence",
    "validate_timestamp",
    "validate_metadata",
    "validate_pattern",
    "validate_decision",
    "validate_strategy",
    "validate_memory",
    "validate_all",
]
