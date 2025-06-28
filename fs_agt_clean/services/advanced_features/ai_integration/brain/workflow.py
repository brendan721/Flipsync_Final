"""Workflow management for the brain service."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class WorkflowState(Enum):
    """Workflow states."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Workflow:
    """Workflow model."""

    workflow_id: str
    state: WorkflowState
    config: Dict[str, bool]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
