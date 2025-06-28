from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set
from uuid import UUID, uuid4

"Experience model for memory management."


@dataclass
class Experience:
    """Represents a stored experience in memory."""

    experience_id: UUID = field(default_factory=uuid4)
    content: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    tags: Set[str] = field(default_factory=set)
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert experience to dictionary."""
        return {
            "experience_id": str(self.experience_id),
            "content": self.content,
            "context": self.context,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "tags": list(self.tags),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Experience":
        """Create experience from dictionary."""
        return cls(
            experience_id=UUID(data["experience_id"]),
            content=data["content"],
            context=data["context"],
            importance=data["importance"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data["access_count"],
            tags=set(data["tags"]),
            metadata=data.get("metadata"),
        )

    def update_access(self) -> None:
        """Update access statistics."""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1

    def update_importance(self, importance: float) -> None:
        """Update importance score."""
        self.importance = max(0.0, min(1.0, importance))

    def add_tags(self, tags: Set[str]) -> None:
        """Add tags to experience."""
        self.tags.update(tags)

    def remove_tags(self, tags: Set[str]) -> None:
        """Remove tags from experience."""
        self.tags.difference_update(tags)

    def matches_context(self, context: Dict[str, Any], threshold: float = 0.7) -> bool:
        """Check if experience matches given context."""
        if not context or not self.context:
            return bool(False)
        matches = sum(
            (
                1
                for k, v in context.items()
                if k in self.context and self.context[k] == v
            )
        )
        similarity = matches / max(len(context), len(self.context))
        return similarity >= threshold

    def get_age(self) -> float:
        """Get age of experience in days."""
        return (datetime.utcnow() - self.created_at).total_seconds() / 86400

    def get_staleness(self) -> float:
        """Get staleness score (0 to 1) based on last access."""
        days_since_access = (
            datetime.utcnow() - self.last_accessed
        ).total_seconds() / 86400
        return min(1.0, days_since_access / 30)

    def get_relevance_score(self) -> float:
        """Calculate overall relevance score."""
        staleness_penalty = self.get_staleness() * 0.3
        access_bonus = min(0.2, self.access_count * 0.02)
        return max(0.0, min(1.0, self.importance - staleness_penalty + access_bonus))
