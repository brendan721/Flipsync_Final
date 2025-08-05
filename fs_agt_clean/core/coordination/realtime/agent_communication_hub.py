"""
Real-Time Agent Communication Hub for FlipSync Phase 4
=====================================================

Ultra-fast agent-to-agent communication system with WebSocket integration,
event-driven coordination, and sub-100ms performance targets.

Built upon the optimized Phase 1-3 foundation with production-grade reliability.
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any, Callable
from dataclasses import dataclass
from enum import Enum

# Import unified status enums - SINGLE SOURCE OF TRUTH
from fs_agt_clean.core.enums.agent_status import (
    UnifiedAgentStatus,
    AgentType,
    normalize_legacy_status,
    is_operational,
    is_error_state,
)

logger = logging.getLogger(__name__)


class CommunicationEventType(Enum):
    """Types of real-time communication events."""

    AGENT_HEARTBEAT = "agent_heartbeat"
    DECISION_BROADCAST = "decision_broadcast"
    COORDINATION_REQUEST = "coordination_request"
    RESOURCE_CONFLICT = "resource_conflict"
    PERFORMANCE_ALERT = "performance_alert"
    STATUS_UPDATE = "status_update"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


@dataclass
class CommunicationEvent:
    """Real-time communication event structure."""

    event_id: str
    event_type: CommunicationEventType
    source_agent: str
    target_agents: List[str]
    data: Dict[str, Any]
    timestamp: datetime
    priority: int = 1  # 1=highest, 5=lowest
    requires_response: bool = False
    timeout_ms: int = 100  # Default 100ms timeout


@dataclass
class AgentConnectionInfo:
    """Agent connection and performance information."""

    agent_id: str
    agent_type: str
    status: UnifiedAgentStatus
    websocket_endpoint: Optional[str]
    last_heartbeat: datetime
    performance_metrics: Dict[str, float]
    active_decisions: Set[str]
    communication_latency: float = 0.0


class RealTimeAgentCommunicationHub:
    """
    Ultra-fast agent-to-agent communication system.

    Provides sub-100ms communication between FlipSync agents with:
    - WebSocket-based real-time messaging
    - Event-driven coordination triggers
    - Live status broadcasting
    - Performance monitoring integration
    """

    def __init__(self, performance_target_ms: float = 50.0):
        """Initialize the real-time communication hub.

        Args:
            performance_target_ms: Target latency for agent communication (default: 50ms)
        """
        self.performance_target_ms = performance_target_ms

        # Agent registry and connections
        self.active_agents: Dict[str, AgentConnectionInfo] = {}
        self.communication_channels: Dict[str, asyncio.Queue] = {}
        self.event_subscribers: Dict[CommunicationEventType, Set[str]] = {}

        # Performance tracking
        self.communication_metrics: Dict[str, List[float]] = {}
        self.total_events_processed = 0
        self.failed_communications = 0

        # Event processing
        self.event_queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.is_running = False

        # Callbacks for external integration
        self.event_callbacks: Dict[CommunicationEventType, List[Callable]] = {}

        logger.info(
            f"🔄 RealTimeAgentCommunicationHub initialized with {performance_target_ms}ms target"
        )

    async def initialize(self) -> bool:
        """Initialize the communication hub and start processing."""
        try:
            # Start event processing task
            self.is_running = True
            self.processing_task = asyncio.create_task(self._process_events())

            # Initialize event subscriber registry
            for event_type in CommunicationEventType:
                self.event_subscribers[event_type] = set()

            logger.info("✅ RealTimeAgentCommunicationHub initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize communication hub: {e}")
            return False

    async def register_agent_for_realtime(
        self, agent_id: str, agent_type: str, websocket_endpoint: Optional[str] = None
    ) -> bool:
        """Register agent for real-time communication.

        Args:
            agent_id: Unique agent identifier
            agent_type: Type of agent (market, executive, content, logistics)
            websocket_endpoint: WebSocket endpoint for real-time communication

        Returns:
            True if registration successful, False otherwise
        """
        try:
            start_time = time.perf_counter()

            # Create agent connection info
            connection_info = AgentConnectionInfo(
                agent_id=agent_id,
                agent_type=agent_type,
                status=UnifiedAgentStatus.RUNNING,  # Use unified enum value
                websocket_endpoint=websocket_endpoint,
                last_heartbeat=datetime.now(timezone.utc),
                performance_metrics={
                    "avg_response_time": 0.0,
                    "decision_count": 0,
                    "error_rate": 0.0,
                },
                active_decisions=set(),
            )

            # Register agent
            self.active_agents[agent_id] = connection_info
            self.communication_channels[agent_id] = asyncio.Queue()
            self.communication_metrics[agent_id] = []

            # Subscribe to heartbeat events by default
            self.event_subscribers[CommunicationEventType.AGENT_HEARTBEAT].add(agent_id)

            registration_time = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"🔗 Agent {agent_id} ({agent_type}) registered for real-time communication "
                f"in {registration_time:.2f}ms"
            )

            # Broadcast agent registration
            await self.event_queue.put(
                CommunicationEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=CommunicationEventType.STATUS_UPDATE,
                    source_agent="communication_hub",
                    target_agents=list(self.active_agents.keys()),
                    data={
                        "agent_id": agent_id,
                        "agent_type": agent_type,
                        "status": "registered",
                        "registration_time_ms": registration_time,
                    },
                    timestamp=datetime.now(timezone.utc),
                    priority=2,
                )
            )

            return True

        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False

    async def broadcast_coordination_event(
        self,
        event_type: CommunicationEventType,
        data: Dict[str, Any],
        target_agents: List[str],
        source_agent: str = "system",
        priority: int = 1,
        requires_response: bool = False,
    ) -> Dict[str, Any]:
        """Broadcast coordination events to target agents in real-time.

        Args:
            event_type: Type of coordination event
            data: Event data payload
            target_agents: List of target agent IDs
            source_agent: Source agent ID
            priority: Event priority (1=highest, 5=lowest)
            requires_response: Whether event requires response

        Returns:
            Broadcast result with timing and delivery information
        """
        start_time = time.perf_counter()

        try:
            # Create coordination event
            event = CommunicationEvent(
                event_id=str(uuid.uuid4()),
                event_type=event_type,
                source_agent=source_agent,
                target_agents=target_agents,
                data=data,
                timestamp=datetime.now(timezone.utc),
                priority=priority,
                requires_response=requires_response,
                timeout_ms=self.performance_target_ms * 2,  # 2x target for safety
            )

            # Queue event for processing
            await self.event_queue.put(event)

            broadcast_time = (time.perf_counter() - start_time) * 1000

            # Track performance
            self.total_events_processed += 1

            result = {
                "event_id": event.event_id,
                "broadcast_time_ms": broadcast_time,
                "target_count": len(target_agents),
                "performance_target_met": broadcast_time < self.performance_target_ms,
                "timestamp": event.timestamp.isoformat(),
            }

            if broadcast_time > self.performance_target_ms:
                logger.warning(
                    f"⚠️ Coordination broadcast exceeded target: {broadcast_time:.2f}ms > {self.performance_target_ms}ms"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to broadcast coordination event: {e}")
            self.failed_communications += 1
            return {
                "error": str(e),
                "broadcast_time_ms": (time.perf_counter() - start_time) * 1000,
                "success": False,
            }

    async def send_direct_message(
        self,
        source_agent: str,
        target_agent: str,
        message_data: Dict[str, Any],
        priority: int = 1,
    ) -> Dict[str, Any]:
        """Send direct message between two agents with sub-100ms target.

        Args:
            source_agent: Source agent ID
            target_agent: Target agent ID
            message_data: Message payload
            priority: Message priority

        Returns:
            Message delivery result with timing
        """
        start_time = time.perf_counter()

        try:
            # Validate agents are registered
            if target_agent not in self.active_agents:
                raise ValueError(f"Target agent {target_agent} not registered")

            if source_agent not in self.active_agents and source_agent != "system":
                raise ValueError(f"Source agent {source_agent} not registered")

            # Create direct message event
            event = CommunicationEvent(
                event_id=str(uuid.uuid4()),
                event_type=CommunicationEventType.DECISION_BROADCAST,
                source_agent=source_agent,
                target_agents=[target_agent],
                data=message_data,
                timestamp=datetime.now(timezone.utc),
                priority=priority,
                requires_response=False,
            )

            # Direct delivery to target agent's queue
            if target_agent in self.communication_channels:
                await self.communication_channels[target_agent].put(event)

            delivery_time = (time.perf_counter() - start_time) * 1000

            # Update communication metrics
            if target_agent in self.communication_metrics:
                self.communication_metrics[target_agent].append(delivery_time)
                # Keep only last 100 measurements
                if len(self.communication_metrics[target_agent]) > 100:
                    self.communication_metrics[target_agent] = (
                        self.communication_metrics[target_agent][-100:]
                    )

            # Update agent performance metrics
            if target_agent in self.active_agents:
                self.active_agents[target_agent].communication_latency = delivery_time

            logger.debug(
                f"📨 Direct message {source_agent} → {target_agent} delivered in {delivery_time:.2f}ms"
            )

            return {
                "event_id": event.event_id,
                "delivery_time_ms": delivery_time,
                "target_agent": target_agent,
                "performance_target_met": delivery_time < self.performance_target_ms,
                "success": True,
            }

        except Exception as e:
            delivery_time = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Failed to send direct message {source_agent} → {target_agent}: {e}"
            )
            self.failed_communications += 1

            return {
                "error": str(e),
                "delivery_time_ms": delivery_time,
                "success": False,
            }

    async def _process_events(self):
        """Background task to process communication events."""
        logger.info("🔄 Starting real-time event processing")

        while self.is_running:
            try:
                # Get event with timeout to allow graceful shutdown
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)

                # Process event
                await self._handle_communication_event(event)

            except asyncio.TimeoutError:
                # Normal timeout, continue processing
                continue
            except Exception as e:
                logger.error(f"Error processing communication event: {e}")
                await asyncio.sleep(0.01)  # Brief pause on error

    async def _handle_communication_event(self, event: CommunicationEvent):
        """Handle individual communication event."""
        start_time = time.perf_counter()

        try:
            # Deliver to target agents
            for target_agent in event.target_agents:
                if target_agent in self.communication_channels:
                    await self.communication_channels[target_agent].put(event)

            # Execute callbacks
            if event.event_type in self.event_callbacks:
                for callback in self.event_callbacks[event.event_type]:
                    try:
                        await callback(event)
                    except Exception as callback_error:
                        logger.error(f"Event callback failed: {callback_error}")

            processing_time = (time.perf_counter() - start_time) * 1000

            if processing_time > self.performance_target_ms:
                logger.warning(
                    f"⚠️ Event processing exceeded target: {processing_time:.2f}ms > {self.performance_target_ms}ms"
                )

        except Exception as e:
            logger.error(f"Failed to handle communication event {event.event_id}: {e}")

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get real-time status of specific agent."""
        if agent_id not in self.active_agents:
            return None

        agent_info = self.active_agents[agent_id]

        # Calculate average communication latency
        avg_latency = 0.0
        if (
            agent_id in self.communication_metrics
            and self.communication_metrics[agent_id]
        ):
            avg_latency = sum(self.communication_metrics[agent_id]) / len(
                self.communication_metrics[agent_id]
            )

        return {
            "agent_id": agent_id,
            "agent_type": agent_info.agent_type,
            "status": agent_info.status.value,
            "last_heartbeat": agent_info.last_heartbeat.isoformat(),
            "communication_latency_ms": agent_info.communication_latency,
            "avg_communication_latency_ms": avg_latency,
            "active_decisions": len(agent_info.active_decisions),
            "performance_metrics": agent_info.performance_metrics,
            "websocket_connected": agent_info.websocket_endpoint is not None,
        }

    async def get_communication_metrics(self) -> Dict[str, Any]:
        """Get comprehensive communication performance metrics."""
        total_latencies = []
        for agent_latencies in self.communication_metrics.values():
            total_latencies.extend(agent_latencies)

        avg_latency = (
            sum(total_latencies) / len(total_latencies) if total_latencies else 0.0
        )

        return {
            "total_events_processed": self.total_events_processed,
            "failed_communications": self.failed_communications,
            "success_rate": (
                (self.total_events_processed - self.failed_communications)
                / self.total_events_processed
                if self.total_events_processed > 0
                else 0.0
            ),
            "average_latency_ms": avg_latency,
            "performance_target_ms": self.performance_target_ms,
            "target_compliance_rate": (
                sum(
                    1
                    for latency in total_latencies
                    if latency < self.performance_target_ms
                )
                / len(total_latencies)
                if total_latencies
                else 0.0
            ),
            "active_agents": len(self.active_agents),
            "active_channels": len(self.communication_channels),
        }

    async def shutdown(self):
        """Gracefully shutdown the communication hub."""
        logger.info("🔄 Shutting down RealTimeAgentCommunicationHub")

        self.is_running = False

        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass

        # Clear all data structures
        self.active_agents.clear()
        self.communication_channels.clear()
        self.event_subscribers.clear()
        self.communication_metrics.clear()

        logger.info("✅ RealTimeAgentCommunicationHub shutdown complete")
