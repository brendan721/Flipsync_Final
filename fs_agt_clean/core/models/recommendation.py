"""
Recommendation models for FlipSync.

This module provides data models for recommendation functionality including
recommendation contexts, results, and scoring.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .chat import UnifiedAgentResponse, MessageIntent

logger = logging.getLogger(__name__)


@dataclass
class RecommendationScore:
    """Represents a recommendation score with reasoning."""

    score: float
    reasoning: Optional[str] = None
    factors: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "score": self.score,
            "reasoning": self.reasoning,
            "factors": self.factors,
            "metadata": self.metadata,
        }


@dataclass
class Recommendation:
    """Represents a recommendation."""

    recommendation_id: str
    title: str
    description: str
    recommendation_type: str  # action, tip, product, etc.
    score: RecommendationScore
    action: Optional[str] = None
    action_params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher number = higher priority
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize default values after creation."""
        if self.created_at is None:
            self.created_at = datetime.now()

    def is_expired(self) -> bool:
        """Check if the recommendation has expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "recommendation_id": self.recommendation_id,
            "title": self.title,
            "description": self.description,
            "recommendation_type": self.recommendation_type,
            "score": self.score.to_dict(),
            "action": self.action,
            "action_params": self.action_params,
            "priority": self.priority,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.metadata,
        }


@dataclass
class ChatRecommendationContext:
    """Context for generating chat-based recommendations."""

    user_id: str
    message: str
    intent: Optional[MessageIntent] = None
    agent_response: Optional[UnifiedAgentResponse] = None
    conversation_id: Optional[str] = None
    session_data: Dict[str, Any] = field(default_factory=dict)
    user_profile: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after creation."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "user_id": self.user_id,
            "message": self.message,
            "intent": self.intent.to_dict() if self.intent else None,
            "agent_response": (
                self.agent_response.to_dict() if self.agent_response else None
            ),
            "conversation_id": self.conversation_id,
            "session_data": self.session_data,
            "user_profile": self.user_profile,
            "context": self.context,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


@dataclass
class RecommendationRequest:
    """Request for recommendations."""

    request_id: str
    user_id: str
    context: ChatRecommendationContext
    recommendation_types: List[str] = field(default_factory=list)  # Filter by types
    max_recommendations: int = 5
    min_score: float = 0.0
    include_expired: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after creation."""
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "context": self.context.to_dict(),
            "recommendation_types": self.recommendation_types,
            "max_recommendations": self.max_recommendations,
            "min_score": self.min_score,
            "include_expired": self.include_expired,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass
class RecommendationResponse:
    """Response containing recommendations."""

    request_id: str
    recommendations: List[Recommendation]
    total_count: int
    processing_time_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize default values after creation."""
        if self.created_at is None:
            self.created_at = datetime.now()

    def get_top_recommendations(self, limit: int = 3) -> List[Recommendation]:
        """Get top recommendations by score and priority."""
        sorted_recs = sorted(
            self.recommendations,
            key=lambda r: (r.priority, r.score.score),
            reverse=True,
        )
        return sorted_recs[:limit]

    def filter_by_type(self, recommendation_type: str) -> List[Recommendation]:
        """Filter recommendations by type."""
        return [
            r
            for r in self.recommendations
            if r.recommendation_type == recommendation_type
        ]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "request_id": self.request_id,
            "recommendations": [rec.to_dict() for rec in self.recommendations],
            "total_count": self.total_count,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
