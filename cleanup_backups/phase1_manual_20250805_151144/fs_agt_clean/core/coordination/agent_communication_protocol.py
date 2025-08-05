"""
Agent-to-Agent Communication Protocol for FlipSync Agentic System
================================================================

This module implements standardized inter-agent communication protocols that enable
the 4 autonomous agents to communicate directly with each other for complex workflows,
conflict resolution, and state synchronization.

Key Features:
- Standardized message format for inter-agent communication
- Workflow orchestration for multi-agent tasks
- Conflict resolution when agents disagree
- State synchronization across agents
- Integration with existing AdvancedMultiAgentCoordinator
- Performance-optimized communication (<200ms coordination targets)
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable
from uuid import uuid4

from fs_agt_clean.core.coordination.advanced_multi_agent_coordinator import (
    AdvancedMultiAgentCoordinator,
    CoordinationStrategy,
    CoordinationTask,
)
from fs_agt_clean.core.coordination.conflict_resolution_system import (
    ConflictResolutionSystem,
    ConflictType,
)
from fs_agt_clean.core.coordination.priority_arbitration_system import (
    PriorityArbitrationSystem,
    Priority,
)
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of inter-agent messages."""

    REQUEST = "request"  # Request for action or information
    RESPONSE = "response"  # Response to a request
    NOTIFICATION = "notification"  # One-way notification
    COORDINATION = "coordination"  # Coordination message
    CONFLICT_RESOLUTION = "conflict_resolution"  # Conflict resolution message
    STATE_SYNC = "state_sync"  # State synchronization message
    WORKFLOW = "workflow"  # Workflow orchestration message


class AgentRole(Enum):
    """Agent roles in communication."""

    INITIATOR = "initiator"  # Agent that starts communication
    PARTICIPANT = "participant"  # Agent that participates in communication
    COORDINATOR = "coordinator"  # Agent that coordinates workflow
    RESOLVER = "resolver"  # Agent that resolves conflicts


@dataclass
class AgentMessage:
    """Standardized message format for inter-agent communication."""

    message_id: str = field(default_factory=lambda: str(uuid4()))
    message_type: MessageType = MessageType.REQUEST
    sender_agent: str = ""
    recipient_agent: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.MEDIUM
    requires_response: bool = False
    correlation_id: Optional[str] = None  # For request-response correlation
    workflow_id: Optional[str] = None  # For workflow tracking
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None


@dataclass
class WorkflowStep:
    """Represents a step in a multi-agent workflow."""

    step_id: str
    agent_id: str
    action: str
    input_data: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)  # Step IDs this depends on
    timeout_seconds: int = 30
    retry_count: int = 0
    max_retries: int = 3
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class MultiAgentWorkflow:
    """Represents a multi-agent workflow with orchestration."""

    workflow_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    coordination_strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "created"  # created, running, completed, failed, cancelled
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentCommunicationProtocol:
    """
    Standardized protocol for inter-agent communication.

    Provides standardized messaging, workflow orchestration, conflict resolution,
    and state synchronization capabilities for the 4 autonomous agents.
    """

    def __init__(self, database: Optional[Database] = None):
        """Initialize the agent communication protocol."""
        self.database = database

        # Core coordination components
        self.multi_agent_coordinator = AdvancedMultiAgentCoordinator(
            coordinator_id="communication_protocol_coordinator", database=database
        )
        self.conflict_resolver = ConflictResolutionSystem()
        self.priority_arbitrator = PriorityArbitrationSystem()

        # Message handling
        self.message_handlers: Dict[str, Callable] = {}
        self.pending_messages: Dict[str, AgentMessage] = {}
        self.message_responses: Dict[str, AgentMessage] = {}

        # Workflow management
        self.active_workflows: Dict[str, MultiAgentWorkflow] = {}
        self.workflow_handlers: Dict[str, Callable] = {}

        # Agent registry
        self.registered_agents: Set[str] = set()
        self.agent_capabilities: Dict[str, List[str]] = {}

        logger.info("✅ Agent Communication Protocol initialized")

    async def initialize(self):
        """Initialize the communication protocol."""
        try:
            await self.multi_agent_coordinator.initialize()
            await self.conflict_resolver.initialize()
            await self.priority_arbitrator.initialize()

            logger.info("✅ Agent Communication Protocol fully initialized")

        except Exception as e:
            logger.error(f"❌ Failed to initialize communication protocol: {e}")
            raise

    async def register_agent(
        self,
        agent_id: str,
        capabilities: List[str],
        message_handler: Optional[Callable] = None,
    ):
        """Register an agent with the communication protocol."""
        try:
            self.registered_agents.add(agent_id)
            self.agent_capabilities[agent_id] = capabilities

            if message_handler:
                self.message_handlers[agent_id] = message_handler

            # Register with multi-agent coordinator
            await self.multi_agent_coordinator.register_agent(
                agent_id=agent_id,
                agent_type=agent_id.split("_")[0],  # Extract type from ID
                capabilities=capabilities,
            )

            logger.info(f"✅ Agent {agent_id} registered with communication protocol")

        except Exception as e:
            logger.error(f"❌ Failed to register agent {agent_id}: {e}")
            raise

    async def send_message(
        self,
        sender_agent: str,
        recipient_agent: str,
        message_type: MessageType,
        content: Dict[str, Any],
        priority: Priority = Priority.MEDIUM,
        requires_response: bool = False,
        timeout_seconds: int = 30,
    ) -> Optional[AgentMessage]:
        """Send a message between agents."""
        try:
            # Create message
            message = AgentMessage(
                message_type=message_type,
                sender_agent=sender_agent,
                recipient_agent=recipient_agent,
                content=content,
                priority=priority,
                requires_response=requires_response,
                expires_at=(
                    datetime.now(timezone.utc).replace(microsecond=0)
                    + timedelta(seconds=timeout_seconds)
                    if requires_response
                    else None
                ),
            )

            # Validate agents are registered
            if sender_agent not in self.registered_agents:
                raise ValueError(f"Sender agent {sender_agent} not registered")
            if recipient_agent not in self.registered_agents:
                raise ValueError(f"Recipient agent {recipient_agent} not registered")

            # Store message if response required
            if requires_response:
                self.pending_messages[message.message_id] = message

            # Route message to recipient
            response = await self._route_message(message)

            logger.info(f"✅ Message sent from {sender_agent} to {recipient_agent}")
            return response

        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return None

    async def create_workflow(
        self,
        name: str,
        steps: List[WorkflowStep],
        coordination_strategy: CoordinationStrategy = CoordinationStrategy.SEQUENTIAL,
    ) -> str:
        """Create a multi-agent workflow."""
        try:
            workflow = MultiAgentWorkflow(
                name=name, steps=steps, coordination_strategy=coordination_strategy
            )

            self.active_workflows[workflow.workflow_id] = workflow

            logger.info(f"✅ Workflow '{name}' created with ID {workflow.workflow_id}")
            return workflow.workflow_id

        except Exception as e:
            logger.error(f"❌ Failed to create workflow: {e}")
            raise

    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a multi-agent workflow."""
        try:
            if workflow_id not in self.active_workflows:
                raise ValueError(f"Workflow {workflow_id} not found")

            workflow = self.active_workflows[workflow_id]
            workflow.status = "running"

            # Create coordination task
            coordination_task = CoordinationTask(
                task_id=workflow_id,
                task_type="workflow_execution",
                coordination_strategy=workflow.coordination_strategy,
                participating_agents=[step.agent_id for step in workflow.steps],
                task_data={"workflow": workflow},
            )

            # Execute through multi-agent coordinator
            result = await self.multi_agent_coordinator.coordinate_task(
                coordination_task
            )

            # Update workflow status
            if result.get("success", False):
                workflow.status = "completed"
                workflow.result = result
            else:
                workflow.status = "failed"
                workflow.error = result.get("error", "Unknown error")

            logger.info(f"✅ Workflow {workflow_id} execution completed")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to execute workflow {workflow_id}: {e}")
            if workflow_id in self.active_workflows:
                self.active_workflows[workflow_id].status = "failed"
                self.active_workflows[workflow_id].error = str(e)
            raise

    async def resolve_conflict(
        self,
        conflicting_agents: List[str],
        conflict_data: Dict[str, Any],
        conflict_type: ConflictType = ConflictType.DECISION_CONFLICT,
    ) -> Dict[str, Any]:
        """Resolve conflicts between agents."""
        try:
            # Use conflict resolution system
            resolution_result = await self.conflict_resolver.resolve_conflict(
                conflict_type=conflict_type,
                involved_agents=conflicting_agents,
                conflict_data=conflict_data,
            )

            # Notify agents of resolution
            for agent_id in conflicting_agents:
                await self.send_message(
                    sender_agent="communication_protocol",
                    recipient_agent=agent_id,
                    message_type=MessageType.CONFLICT_RESOLUTION,
                    content={
                        "resolution_result": resolution_result,
                        "conflict_type": conflict_type.value,
                    },
                )

            logger.info(f"✅ Conflict resolved between agents: {conflicting_agents}")
            return resolution_result

        except Exception as e:
            logger.error(f"❌ Failed to resolve conflict: {e}")
            raise

    async def synchronize_state(
        self, agents: List[str], state_data: Dict[str, Any]
    ) -> bool:
        """Synchronize state across multiple agents."""
        try:
            # Send state sync messages to all agents
            sync_tasks = []
            for agent_id in agents:
                if agent_id in self.registered_agents:
                    task = self.send_message(
                        sender_agent="communication_protocol",
                        recipient_agent=agent_id,
                        message_type=MessageType.STATE_SYNC,
                        content=state_data,
                    )
                    sync_tasks.append(task)

            # Wait for all sync operations
            await asyncio.gather(*sync_tasks, return_exceptions=True)

            logger.info(f"✅ State synchronized across {len(agents)} agents")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to synchronize state: {e}")
            return False

    async def _route_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Route message to recipient agent."""
        try:
            # Get message handler for recipient
            handler = self.message_handlers.get(message.recipient_agent)
            if not handler:
                logger.warning(
                    f"No message handler for agent {message.recipient_agent}"
                )
                return None

            # Process message with handler
            response = await handler(message)

            # Handle response if required
            if message.requires_response and response:
                # Store response
                self.message_responses[message.message_id] = response

                # Clean up pending message
                if message.message_id in self.pending_messages:
                    del self.pending_messages[message.message_id]

            return response

        except Exception as e:
            logger.error(f"❌ Failed to route message: {e}")
            return None

    async def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """Get capabilities of a registered agent."""
        return self.agent_capabilities.get(agent_id, [])

    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a workflow."""
        if workflow_id not in self.active_workflows:
            return None

        workflow = self.active_workflows[workflow_id]
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status,
            "steps_completed": len(
                [s for s in workflow.steps if s.status == "completed"]
            ),
            "total_steps": len(workflow.steps),
            "result": workflow.result,
            "error": workflow.error,
        }

    async def cleanup_expired_messages(self):
        """Clean up expired messages to prevent memory leaks."""
        try:
            current_time = datetime.now(timezone.utc)
            expired_messages = [
                msg_id
                for msg_id, msg in self.pending_messages.items()
                if msg.expires_at and msg.expires_at < current_time
            ]

            for msg_id in expired_messages:
                del self.pending_messages[msg_id]
                if msg_id in self.message_responses:
                    del self.message_responses[msg_id]

            if expired_messages:
                logger.info(f"Cleaned up {len(expired_messages)} expired messages")

        except Exception as e:
            logger.error(f"Error cleaning up expired messages: {e}")
