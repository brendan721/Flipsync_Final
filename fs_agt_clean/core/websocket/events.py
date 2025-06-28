"""
WebSocket Events Definition for FlipSync Real-time Communication
===============================================================

This module defines the event types, message formats, and data structures
used in WebSocket communication between clients and the FlipSync backend.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """WebSocket event types."""

    # Connection events
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_CONFIRMED = "connection_confirmed"
    PING = "ping"
    PONG = "pong"
    SUBSCRIBE = "subscribe"

    # Chat events
    MESSAGE = "message"
    TYPING = "typing"
    MESSAGE_REACTION = "message_reaction"
    MESSAGE_EDIT = "message_edit"
    MESSAGE_DELETE = "message_delete"

    # UnifiedAgent events
    AGENT_STATUS = "agent_status"
    AGENT_DECISION = "agent_decision"
    AGENT_TASK_UPDATE = "agent_task_update"
    AGENT_METRIC = "agent_metric"
    AGENT_RESPONSE_STREAM = "agent_response_stream"

    # Workflow coordination events
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    AGENT_COORDINATION = "agent_coordination"

    # Approval workflow events
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_ESCALATED = "approval_escalated"

    # System events
    SYSTEM_ALERT = "system_alert"
    SYSTEM_NOTIFICATION = "system_notification"
    ERROR = "error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Conversation events
    CONVERSATION_CREATED = "conversation_created"
    CONVERSATION_UPDATED = "conversation_updated"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"


class SenderType(str, Enum):
    """Message sender types."""

    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class UnifiedAgentType(str, Enum):
    """UnifiedAgent types for routing and identification."""

    MARKET = "market"
    EXECUTIVE = "executive"
    CONTENT = "content"
    LOGISTICS = "logistics"
    ASSISTANT = "assistant"


class MessageStatus(str, Enum):
    """Message status types."""

    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class BaseWebSocketEvent(BaseModel):
    """Base WebSocket event structure."""

    type: EventType
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class ConnectionEvent(BaseWebSocketEvent):
    """Connection-related events."""

    data: Dict[str, Any] = Field(default_factory=dict)


class ChatMessageData(BaseModel):
    """Chat message data structure."""

    id: str
    conversation_id: str
    content: str
    sender: SenderType
    agent_type: Optional[UnifiedAgentType] = None
    timestamp: str
    thread_id: Optional[str] = None
    parent_id: Optional[str] = None
    status: MessageStatus = MessageStatus.SENT
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatMessageEvent(BaseWebSocketEvent):
    """Chat message event."""

    type: EventType = EventType.MESSAGE
    conversation_id: str
    data: ChatMessageData


class TypingIndicatorData(BaseModel):
    """Typing indicator data."""

    user_id: Optional[str] = None
    agent_type: Optional[UnifiedAgentType] = None
    is_typing: bool
    conversation_id: str


class TypingEvent(BaseWebSocketEvent):
    """Typing indicator event."""

    type: EventType = EventType.TYPING
    conversation_id: str
    data: TypingIndicatorData


class MessageReactionData(BaseModel):
    """Message reaction data."""

    message_id: str
    user_id: str
    reaction_type: str  # 'like', 'dislike', 'helpful', 'not_helpful'
    action: str  # 'add' or 'remove'


class MessageReactionEvent(BaseWebSocketEvent):
    """Message reaction event."""

    type: EventType = EventType.MESSAGE_REACTION
    conversation_id: str
    data: MessageReactionData


class UnifiedAgentStatusData(BaseModel):
    """UnifiedAgent status data."""

    agent_id: str
    agent_type: UnifiedAgentType
    status: str  # 'running', 'stopped', 'error', 'idle'
    metrics: Dict[str, Any] = Field(default_factory=dict)
    last_activity: Optional[str] = None
    error_message: Optional[str] = None


class UnifiedAgentStatusEvent(BaseWebSocketEvent):
    """UnifiedAgent status update event."""

    type: EventType = EventType.AGENT_STATUS
    data: UnifiedAgentStatusData


class UnifiedAgentDecisionData(BaseModel):
    """UnifiedAgent decision data."""

    decision_id: str
    agent_id: str
    agent_type: UnifiedAgentType
    decision_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    status: str = "pending"  # 'pending', 'approved', 'rejected', 'executed'
    requires_approval: bool = True


class UnifiedAgentDecisionEvent(BaseWebSocketEvent):
    """UnifiedAgent decision event."""

    type: EventType = EventType.AGENT_DECISION
    data: UnifiedAgentDecisionData


class UnifiedAgentTaskData(BaseModel):
    """UnifiedAgent task data."""

    task_id: str
    agent_id: str
    task_type: str
    task_name: str
    status: str  # 'queued', 'running', 'completed', 'failed'
    progress: Optional[float] = None  # 0.0 to 1.0
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class UnifiedAgentTaskEvent(BaseWebSocketEvent):
    """UnifiedAgent task update event."""

    type: EventType = EventType.AGENT_TASK_UPDATE
    data: UnifiedAgentTaskData


class SystemAlertData(BaseModel):
    """System alert data."""

    alert_id: str
    severity: str  # 'info', 'warning', 'error', 'critical'
    title: str
    message: str
    source: str
    action_required: bool = False
    action_url: Optional[str] = None


class SystemAlertEvent(BaseWebSocketEvent):
    """System alert event."""

    type: EventType = EventType.SYSTEM_ALERT
    data: SystemAlertData


class ErrorData(BaseModel):
    """Error event data."""

    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    retry_after: Optional[int] = None


class ErrorEvent(BaseWebSocketEvent):
    """Error event."""

    type: EventType = EventType.ERROR
    data: ErrorData


class ConversationData(BaseModel):
    """Conversation data."""

    conversation_id: str
    title: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConversationEvent(BaseWebSocketEvent):
    """Conversation event."""

    conversation_id: str
    data: ConversationData


class ApprovalWorkflowData(BaseModel):
    """Approval workflow data structure."""

    approval_id: str
    decision_type: str
    confidence: float
    auto_approve: bool
    escalation_required: bool
    agent_type: str
    user_id: str
    conversation_id: str
    status: str  # 'pending', 'approved', 'rejected', 'escalated'
    approved_by: Optional[str] = None
    rejected_by: Optional[str] = None
    reason: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None


class ApprovalEvent(BaseWebSocketEvent):
    """Approval workflow event."""

    type: EventType
    conversation_id: str
    data: ApprovalWorkflowData


class UnifiedAgentResponseStreamData(BaseModel):
    """UnifiedAgent response streaming data."""

    message_id: str
    conversation_id: str
    content: str
    agent_type: UnifiedAgentType
    is_streaming: bool = True
    chunk_index: Optional[int] = None
    total_chunks: Optional[int] = None
    is_final: bool = False
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UnifiedAgentResponseStreamEvent(BaseWebSocketEvent):
    """UnifiedAgent response streaming event."""

    type: EventType = EventType.AGENT_RESPONSE_STREAM
    conversation_id: str
    data: UnifiedAgentResponseStreamData


class WorkflowData(BaseModel):
    """Workflow coordination data."""

    workflow_id: str
    workflow_type: str
    participating_agents: List[str]
    status: str  # 'started', 'running', 'completed', 'failed'
    progress: float = 0.0  # 0.0 to 1.0
    current_agent: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class WorkflowEvent(BaseWebSocketEvent):
    """Workflow coordination event."""

    type: EventType
    conversation_id: Optional[str] = None
    data: WorkflowData


class UnifiedAgentCoordinationData(BaseModel):
    """UnifiedAgent coordination data."""

    coordination_id: str
    coordinating_agents: List[str]
    task: str
    progress: float = 0.0  # 0.0 to 1.0
    current_phase: str
    agent_statuses: Dict[str, str] = Field(default_factory=dict)  # agent_name -> status
    context: Dict[str, Any] = Field(default_factory=dict)


class UnifiedAgentCoordinationEvent(BaseWebSocketEvent):
    """UnifiedAgent coordination event."""

    type: EventType = EventType.AGENT_COORDINATION
    conversation_id: Optional[str] = None
    data: UnifiedAgentCoordinationData


# Union type for all possible WebSocket events
WebSocketEvent = Union[
    ConnectionEvent,
    ChatMessageEvent,
    TypingEvent,
    MessageReactionEvent,
    UnifiedAgentStatusEvent,
    UnifiedAgentDecisionEvent,
    UnifiedAgentTaskEvent,
    SystemAlertEvent,
    ErrorEvent,
    ConversationEvent,
    ApprovalEvent,
    UnifiedAgentResponseStreamEvent,
    WorkflowEvent,
    UnifiedAgentCoordinationEvent,
]


class WebSocketMessage(BaseModel):
    """Complete WebSocket message structure."""

    type: EventType
    conversation_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    @field_validator("timestamp", mode="before")
    @classmethod
    def validate_timestamp(cls, v):
        """Convert various timestamp formats to ISO 8601 string."""
        if isinstance(v, str):
            # Already a string, validate it's a proper ISO format
            try:
                datetime.fromisoformat(v.replace("Z", "+00:00"))
                return v
            except ValueError:
                # If not valid ISO format, use current time
                return datetime.now(timezone.utc).isoformat()
        elif isinstance(v, (int, float)):
            # Convert numeric timestamp to ISO 8601 string
            try:
                # Handle both seconds and milliseconds timestamps
                if v > 1e10:  # Likely milliseconds
                    dt = datetime.fromtimestamp(v / 1000, tz=timezone.utc)
                else:  # Likely seconds
                    dt = datetime.fromtimestamp(v, tz=timezone.utc)
                return dt.isoformat()
            except (ValueError, OSError):
                # If conversion fails, use current time
                return datetime.now(timezone.utc).isoformat()
        elif isinstance(v, datetime):
            # Convert datetime object to ISO 8601 string
            return v.isoformat()
        else:
            # For any other type, use current time
            return datetime.now(timezone.utc).isoformat()


def create_message_event(
    conversation_id: str,
    message_id: str,
    content: str,
    sender: SenderType,
    agent_type: Optional[UnifiedAgentType] = None,
    thread_id: Optional[str] = None,
    parent_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> ChatMessageEvent:
    """Create a chat message event."""
    return ChatMessageEvent(
        conversation_id=conversation_id,
        data=ChatMessageData(
            id=message_id,
            conversation_id=conversation_id,
            content=content,
            sender=sender,
            agent_type=agent_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            thread_id=thread_id,
            parent_id=parent_id,
            metadata=metadata or {},
        ),
    )


def create_typing_event(
    conversation_id: str,
    is_typing: bool,
    user_id: Optional[str] = None,
    agent_type: Optional[UnifiedAgentType] = None,
) -> TypingEvent:
    """Create a typing indicator event."""
    return TypingEvent(
        conversation_id=conversation_id,
        data=TypingIndicatorData(
            user_id=user_id,
            agent_type=agent_type,
            is_typing=is_typing,
            conversation_id=conversation_id,
        ),
    )


def create_agent_status_event(
    agent_id: str,
    agent_type: UnifiedAgentType,
    status: str,
    metrics: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
) -> UnifiedAgentStatusEvent:
    """Create an agent status event."""
    return UnifiedAgentStatusEvent(
        data=UnifiedAgentStatusData(
            agent_id=agent_id,
            agent_type=agent_type,
            status=status,
            metrics=metrics or {},
            last_activity=datetime.now(timezone.utc).isoformat(),
            error_message=error_message,
        )
    )


def create_system_alert_event(
    severity: str,
    title: str,
    message: str,
    source: str,
    action_required: bool = False,
    action_url: Optional[str] = None,
) -> SystemAlertEvent:
    """Create a system alert event."""
    return SystemAlertEvent(
        data=SystemAlertData(
            alert_id=str(uuid.uuid4()),
            severity=severity,
            title=title,
            message=message,
            source=source,
            action_required=action_required,
            action_url=action_url,
        )
    )


def create_error_event(
    error_code: str,
    error_message: str,
    details: Optional[Dict[str, Any]] = None,
    retry_after: Optional[int] = None,
) -> ErrorEvent:
    """Create an error event."""
    return ErrorEvent(
        data=ErrorData(
            error_code=error_code,
            error_message=error_message,
            details=details,
            retry_after=retry_after,
        )
    )


def create_approval_event(
    approval_id: str,
    decision_type: str,
    confidence: float,
    auto_approve: bool,
    escalation_required: bool,
    agent_type: str,
    user_id: str,
    conversation_id: str,
    status: str,
    event_type: EventType = EventType.APPROVAL_REQUIRED,
    approved_by: Optional[str] = None,
    rejected_by: Optional[str] = None,
    reason: Optional[str] = None,
) -> ApprovalEvent:
    """Create an approval workflow event."""
    return ApprovalEvent(
        type=event_type,
        conversation_id=conversation_id,
        data=ApprovalWorkflowData(
            approval_id=approval_id,
            decision_type=decision_type,
            confidence=confidence,
            auto_approve=auto_approve,
            escalation_required=escalation_required,
            agent_type=agent_type,
            user_id=user_id,
            conversation_id=conversation_id,
            status=status,
            approved_by=approved_by,
            rejected_by=rejected_by,
            reason=reason,
            created_at=datetime.now(timezone.utc).isoformat(),
            updated_at=(
                datetime.now(timezone.utc).isoformat() if status != "pending" else None
            ),
        ),
    )


def create_agent_response_stream_event(
    message_id: str,
    conversation_id: str,
    content: str,
    agent_type: UnifiedAgentType,
    is_streaming: bool = True,
    chunk_index: Optional[int] = None,
    total_chunks: Optional[int] = None,
    is_final: bool = False,
    confidence: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> UnifiedAgentResponseStreamEvent:
    """Create an agent response streaming event."""
    return UnifiedAgentResponseStreamEvent(
        type=EventType.AGENT_RESPONSE_STREAM,
        conversation_id=conversation_id,
        data=UnifiedAgentResponseStreamData(
            message_id=message_id,
            conversation_id=conversation_id,
            content=content,
            agent_type=agent_type,
            is_streaming=is_streaming,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            is_final=is_final,
            confidence=confidence,
            metadata=metadata or {},
        ),
    )


def create_workflow_event(
    event_type: EventType,
    workflow_id: str,
    workflow_type: str,
    participating_agents: List[str],
    status: str,
    progress: float = 0.0,
    current_agent: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    results: Optional[Dict[str, Any]] = None,
    error_message: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> WorkflowEvent:
    """Create a workflow coordination event."""
    now = datetime.now(timezone.utc).isoformat()
    return WorkflowEvent(
        type=event_type,
        conversation_id=conversation_id,
        data=WorkflowData(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            participating_agents=participating_agents,
            status=status,
            progress=progress,
            current_agent=current_agent,
            context=context or {},
            results=results or {},
            error_message=error_message,
            created_at=now,
            updated_at=now,
        ),
    )


def create_agent_coordination_event(
    coordination_id: str,
    coordinating_agents: List[str],
    task: str,
    progress: float = 0.0,
    current_phase: str = "initializing",
    agent_statuses: Optional[Dict[str, str]] = None,
    context: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[str] = None,
) -> UnifiedAgentCoordinationEvent:
    """Create an agent coordination event."""
    return UnifiedAgentCoordinationEvent(
        conversation_id=conversation_id,
        data=UnifiedAgentCoordinationData(
            coordination_id=coordination_id,
            coordinating_agents=coordinating_agents,
            task=task,
            progress=progress,
            current_phase=current_phase,
            agent_statuses=agent_statuses or {},
            context=context or {},
        ),
    )
