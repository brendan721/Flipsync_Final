from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DirectiveType(str, Enum):
    STRATEGIC = "strategic"
    TACTICAL = "tactical"
    OPERATIONAL = "operational"


class DirectivePriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DirectiveRequest(BaseModel):
    """Request model for distributing directives to subordinate agents"""

    title: str = Field(..., description="Title of the directive")
    description: str = Field(..., description="Detailed description of the directive")
    directive_type: DirectiveType = Field(..., description="Type of directive")
    priority: DirectivePriority = Field(
        ..., description="Priority level of the directive"
    )
    target_agents: List[str] = Field(
        ..., description="List of agent IDs to receive the directive"
    )
    parameters: Dict[str, Any] = Field(
        default={}, description="Additional parameters for the directive"
    )
    deadline: Optional[datetime] = Field(
        None, description="Optional deadline for directive completion"
    )


class DirectiveResponse(BaseModel):
    """Response model for directive distribution"""

    directive_id: str = Field(
        ..., description="Unique identifier for the created directive"
    )
    status: str = Field(..., description="Status of the directive distribution")
    received_by: List[str] = Field(
        ..., description="List of agent IDs that received the directive"
    )
    pending: List[str] = Field(
        default=[],
        description="List of agent IDs that have not yet received the directive",
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the directive was created"
    )


class AgentStatus(str, Enum):
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class AgentStatusDetail(BaseModel):
    """Status details for an individual agent"""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    status: AgentStatus = Field(..., description="Current status of the agent")
    current_task: Optional[str] = Field(
        None, description="ID of the current task being executed, if any"
    )
    last_active: datetime = Field(
        ..., description="Timestamp when the agent was last active"
    )
    performance_metrics: Dict[str, Any] = Field(
        default={}, description="Performance metrics for the agent"
    )
    resource_utilization: Dict[str, float] = Field(
        default={}, description="Resource utilization metrics"
    )
    error_details: Optional[str] = Field(
        None, description="Error details if agent is in error state"
    )


class StatusResponse(BaseModel):
    """Response model for agent status reporting"""

    timestamp: datetime = Field(..., description="Timestamp of the status report")
    agents: List[AgentStatusDetail] = Field(
        ..., description="List of agent status details"
    )
    system_health: Dict[str, Any] = Field(
        default={}, description="Overall system health metrics"
    )


class DecisionType(str, Enum):
    PRICING = "pricing"
    INVENTORY = "inventory"
    MARKETING = "marketing"
    LOGISTICS = "logistics"
    CONTENT = "content"


class DecisionRequest(BaseModel):
    """Request model for executive agent decision making"""

    decision_type: DecisionType = Field(..., description="Type of decision to be made")
    context: Dict[str, Any] = Field(
        ..., description="Context information for the decision"
    )
    options: List[Dict[str, Any]] = Field(
        ..., description="Available options for the decision"
    )
    constraints: Dict[str, Any] = Field(
        default={}, description="Constraints to consider in the decision"
    )
    deadline: Optional[datetime] = Field(
        None, description="Optional deadline for the decision"
    )


class DecisionResponse(BaseModel):
    """Response model for executive agent decision making"""

    decision_id: str = Field(..., description="Unique identifier for the decision")
    selected_option: Dict[str, Any] = Field(..., description="The selected option")
    reasoning: str = Field(..., description="Reasoning behind the decision")
    confidence: float = Field(
        ..., description="Confidence level in the decision (0.0-1.0)"
    )
    alternative_options: List[Dict[str, Any]] = Field(
        default=[], description="Alternative options considered"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the decision was made"
    )


class EventType(str, Enum):
    DIRECTIVE_ISSUED = "directive_issued"
    DIRECTIVE_COMPLETED = "directive_completed"
    DECISION_MADE = "decision_made"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    SYSTEM_ALERT = "system_alert"


class EventSubscriptionRequest(BaseModel):
    """Request model for subscribing to coordination events"""

    event_types: List[EventType] = Field(
        ..., description="Types of events to subscribe to"
    )
    agent_ids: Optional[List[str]] = Field(
        None, description="Optional filter for specific agent IDs"
    )
    min_priority: Optional[DirectivePriority] = Field(
        None, description="Optional minimum priority filter"
    )
    callback_url: Optional[str] = Field(
        None, description="Optional callback URL for event notifications"
    )


class EventSubscriptionResponse(BaseModel):
    """Response model for event subscription"""

    subscription_id: str = Field(
        ..., description="Unique identifier for the subscription"
    )
    event_types: List[EventType] = Field(
        ..., description="Types of events subscribed to"
    )
    filters: Dict[str, Any] = Field(
        default={}, description="Active filters for the subscription"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the subscription was created"
    )
