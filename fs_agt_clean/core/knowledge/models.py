"""Data models for the knowledge sharing module."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeType(str, Enum):
    """Types of knowledge that can be shared between agents."""

    MARKET_INSIGHT = "market_insight"
    PRICING_STRATEGY = "pricing_strategy"
    INVENTORY_PREDICTION = "inventory_prediction"
    CUSTOMER_BEHAVIOR = "customer_behavior"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    OPERATIONAL_INSIGHT = "operational_insight"
    GENERAL = "general"


class KnowledgeStatus(str, Enum):
    """Status of a knowledge entry."""

    PENDING = "pending_validation"
    VALIDATED = "validated"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class ValidationRecord(BaseModel):
    """Record of a validation performed on a knowledge entry."""

    validator_agent_id: str
    validation_score: float
    validated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeEntry(BaseModel):
    """A single entry in the knowledge repository."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: Dict[str, Any]
    knowledge_type: KnowledgeType
    source_agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: KnowledgeStatus = KnowledgeStatus.PENDING
    confidence: float
    tags: List[str] = Field(default_factory=list)
    validations: List[ValidationRecord] = Field(default_factory=list)
    vector: Optional[List[float]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_validation(self, validation: ValidationRecord) -> None:
        """Add a validation record to this knowledge entry."""
        validations = list(self.validations)
        validations.append(validation)
        self.validations = validations
        self.updated_at = datetime.utcnow()

    def update_status(self, new_status: KnowledgeStatus) -> None:
        """Update the status of this knowledge entry."""
        self.status = new_status
        self.updated_at = datetime.utcnow()

    def get_average_validation_score(self) -> float:
        """Get the average validation score for this knowledge entry."""
        if not self.validations:
            return 0.0
        return sum(v.validation_score for v in self.validations) / len(self.validations)


class KnowledgeSubscription(BaseModel):
    """A subscription to knowledge updates."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    knowledge_types: List[KnowledgeType] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    min_confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    active: bool = True

    def matches_entry(self, entry: KnowledgeEntry) -> bool:
        """Check if this subscription matches a knowledge entry."""
        # Check knowledge type
        if self.knowledge_types and entry.knowledge_type not in self.knowledge_types:
            return False

        # Check confidence
        if entry.confidence < self.min_confidence:
            return False

        # Check tags
        if self.tags and not any(tag in entry.tags for tag in self.tags):
            return False

        return True


class KnowledgeNotification(BaseModel):
    """A notification about a knowledge entry."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entry_id: str
    subscription_id: str
    agent_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered: bool = False
    delivered_at: Optional[datetime] = None
    processed: bool = False
    processed_at: Optional[datetime] = None

    def mark_delivered(self) -> None:
        """Mark this notification as delivered."""
        self.delivered = True
        self.delivered_at = datetime.utcnow()

    def mark_processed(self) -> None:
        """Mark this notification as processed."""
        self.processed = True
        self.processed_at = datetime.utcnow()


class KnowledgeStats(BaseModel):
    """Statistics about the knowledge repository."""

    total_entries: int = 0
    entries_by_status: Dict[KnowledgeStatus, int] = Field(default_factory=dict)
    entries_by_type: Dict[KnowledgeType, int] = Field(default_factory=dict)
    total_subscriptions: int = 0
    active_subscriptions: int = 0
    total_validations: int = 0
    average_validation_score: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
