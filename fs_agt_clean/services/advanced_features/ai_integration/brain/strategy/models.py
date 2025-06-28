"""Strategy models for the brain service."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4


@dataclass
class Strategy:
    """Strategy model for decision making."""

    name: str
    description: str
    rules: Dict[str, Any]
    parameters: Dict[str, Any]
    tags: Set[str] = field(default_factory=set)
    strategy_id: UUID = field(default_factory=uuid4)
    performance: float = 0.5
    confidence: float = 0.5
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0
    success_count: int = 0


@dataclass
class StrategyResult:
    """Result of applying a strategy."""

    strategy_id: UUID
    success: bool
    performance: float
    decisions: List[Dict[str, Any]]
    outcome: Dict[str, Any]
    context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
