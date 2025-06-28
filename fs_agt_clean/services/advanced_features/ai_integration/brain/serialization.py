"""
Serialization module for the FlipSync Decision Engine type system.
Provides utilities for converting between types and handling serialization.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, cast

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

T = TypeVar("T", Pattern, Decision, Strategy, Memory)


class SerializationError(Exception):
    """Error raised during serialization/deserialization."""

    pass


def to_dict(obj: Union[Pattern, Decision, Strategy, Memory]) -> Dict[str, Any]:
    """Convert any type system object to a dictionary."""
    if isinstance(obj, Pattern):
        return {
            "type": obj.type.value,
            "name": obj.name,
            "confidence": obj.confidence,
            "metadata": obj.metadata,
            "timestamp": obj.timestamp.isoformat(),
        }
    elif isinstance(obj, Decision):
        return {
            "action": obj.action,
            "confidence": obj.confidence,
            "reasoning": obj.reasoning,
            "patterns": [to_dict(p) for p in obj.patterns],
            "metadata": obj.metadata,
            "timestamp": obj.timestamp.isoformat(),
        }
    elif isinstance(obj, Strategy):
        return {
            "id": obj.id,
            "name": obj.name,
            "weights": obj.weights,
            "metadata": obj.metadata,
            "active": obj.active,
            "last_updated": obj.last_updated.isoformat(),
        }
    elif isinstance(obj, Memory):
        return {
            "content": obj.content,
            "context": obj.context,
            "importance": obj.importance,
            "tags": list(obj.tags),
            "timestamp": obj.timestamp.isoformat(),
            "ttl": obj.ttl,
        }
    else:
        raise SerializationError(f"Unsupported type for serialization: {type(obj)}")


def from_dict(data: Dict[str, Any], target_type: Type[T]) -> T:
    """Convert a dictionary to a type system object."""
    try:
        if target_type == Pattern:
            return Pattern(
                type=PatternType(data["type"]),
                name=data["name"],
                confidence=float(data["confidence"]),
                metadata=data.get("metadata", {}),
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
        elif target_type == Decision:
            return Decision(
                action=data["action"],
                confidence=float(data["confidence"]),
                reasoning=data["reasoning"],
                patterns=[from_dict(p, Pattern) for p in data.get("patterns", [])],
                metadata=data.get("metadata", {}),
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
        elif target_type == Strategy:
            return Strategy(
                id=data["id"],
                name=data["name"],
                weights=data["weights"],
                metadata=data.get("metadata", {}),
                active=data.get("active", True),
                last_updated=datetime.fromisoformat(data["last_updated"]),
            )
        elif target_type == Memory:
            return Memory(
                content=data["content"],
                context=data["context"],
                importance=float(data["importance"]),
                tags=set(data.get("tags", [])),
                timestamp=datetime.fromisoformat(data["timestamp"]),
                ttl=data.get("ttl"),
            )
        else:
            raise SerializationError(f"Unsupported target type: {target_type}")
    except (KeyError, ValueError, TypeError) as e:
        raise SerializationError(
            f"Error deserializing to {target_type.__name__}: {str(e)}"
        )


def to_json_string(obj: Union[Pattern, Decision, Strategy, Memory]) -> str:
    """Convert object to JSON string."""
    import json

    try:
        return json.dumps(to_dict(obj), default=str)
    except (TypeError, ValueError) as e:
        raise SerializationError(f"Error serializing to JSON: {str(e)}")


def from_json_string(json_str: str, target_type: Type[T]) -> T:
    """Convert JSON string to object."""
    import json

    try:
        data = json.loads(json_str)
        return from_dict(data, target_type)
    except json.JSONDecodeError as e:
        raise SerializationError(f"Invalid JSON string: {str(e)}")


def to_compact_dict(obj: Union[Pattern, Decision, Strategy, Memory]) -> Dict[str, Any]:
    """Convert object to a minimal dictionary representation."""
    full_dict = to_dict(obj)
    return {k: v for k, v in full_dict.items() if v is not None and v != {} and v != []}


def merge_metadata(
    base: Dict[str, Any], update: Dict[str, Any], overwrite: bool = False
) -> Dict[str, Any]:
    """Merge two metadata dictionaries."""
    if overwrite:
        return {**base, **update}

    result = base.copy()
    for key, value in update.items():
        if key not in result:
            result[key] = value
        elif isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_metadata(result[key], value, overwrite)
        elif isinstance(result[key], list) and isinstance(value, list):
            result[key] = list(set(result[key] + value))
    return result


class TypeConverter:
    """Utility class for type conversion operations."""

    @staticmethod
    def to_confidence_level(value: float) -> DecisionConfidence:
        """Convert float to DecisionConfidence enum."""
        if value >= DecisionConfidence.VERY_HIGH.value:
            return DecisionConfidence.VERY_HIGH
        elif value >= DecisionConfidence.HIGH.value:
            return DecisionConfidence.HIGH
        elif value >= DecisionConfidence.MEDIUM.value:
            return DecisionConfidence.MEDIUM
        return DecisionConfidence.LOW

    @staticmethod
    def to_importance_level(value: float) -> MemoryImportance:
        """Convert float to MemoryImportance enum."""
        if value >= MemoryImportance.CRITICAL.value:
            return MemoryImportance.CRITICAL
        elif value >= MemoryImportance.HIGH.value:
            return MemoryImportance.HIGH
        elif value >= MemoryImportance.MEDIUM.value:
            return MemoryImportance.MEDIUM
        return MemoryImportance.LOW

    @staticmethod
    def ensure_utc(dt: datetime) -> datetime:
        """Ensure datetime is timezone.utc timezone-aware."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


__all__ = [
    "SerializationError",
    "to_dict",
    "from_dict",
    "to_json_string",
    "from_json_string",
    "to_compact_dict",
    "merge_metadata",
    "TypeConverter",
]
