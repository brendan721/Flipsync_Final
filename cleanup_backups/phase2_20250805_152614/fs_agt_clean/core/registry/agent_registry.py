"""
Agent Registry System for FlipSync 4+1 Architecture
==================================================

This module provides a centralized registry for tracking and managing
the 4 autonomous agents + 1 conversational interface in the FlipSync system.

Key Features:
- Real-time agent instance tracking
- Performance metrics collection
- Health monitoring and status updates
- Database-backed persistence
- Thread-safe operations
- Automatic cleanup and lifecycle management

AGENT_CONTEXT: Central registry for 4+1 architecture agent management
AGENT_PRIORITY: Real-time tracking of autonomous agent instances
AGENT_PATTERN: Singleton registry with database persistence and metrics
"""

import asyncio
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from contextlib import asynccontextmanager

from fs_agt_clean.core.enums.agent_status import (
    UnifiedAgentStatus,
    AgentType,
    AgentPriority,
    validate_status_transition,
    is_operational,
)
from fs_agt_clean.core.db.database import get_database

logger = logging.getLogger(__name__)


@dataclass
class AgentMetrics:
    """Performance metrics for an agent instance."""

    total_decisions: int = 0
    total_execution_time: float = 0.0
    average_decision_time: float = 0.0
    success_rate: float = 1.0
    error_count: int = 0
    last_activity: Optional[str] = None
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0


@dataclass
class RegisteredAgent:
    """Information about a registered agent instance."""

    agent_id: str
    agent_type: AgentType
    status: UnifiedAgentStatus
    priority: AgentPriority
    instance: Optional[Any] = None  # Reference to actual agent instance
    metrics: AgentMetrics = None
    registered_at: datetime = None
    last_heartbeat: datetime = None
    capabilities: List[str] = None
    configuration: Dict[str, Any] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = AgentMetrics()
        if self.registered_at is None:
            self.registered_at = datetime.now(timezone.utc)
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.now(timezone.utc)
        if self.capabilities is None:
            self.capabilities = []
        if self.configuration is None:
            self.configuration = {}


class AgentRegistry:
    """
    Centralized registry for tracking autonomous agent instances.

    This singleton class manages the lifecycle and monitoring of all agents
    in the FlipSync 4+1 architecture.
    """

    _instance: Optional["AgentRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "AgentRegistry":
        """Ensure singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the agent registry."""
        if hasattr(self, "_initialized"):
            return

        self._agents: Dict[str, RegisteredAgent] = {}
        self._agents_by_type: Dict[AgentType, Set[str]] = {}
        self._registry_lock = threading.RLock()
        self._database = None
        self._monitoring_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        self._initialized = True

        logger.info("🚀 Agent Registry initialized for 4+1 architecture")

    async def initialize_async(self):
        """Initialize async components."""
        try:
            self._database = get_database()
            await self._database.initialize()

            # Start monitoring task
            if self._monitoring_task is None:
                self._monitoring_task = asyncio.create_task(self._monitoring_loop())

            logger.info("✅ Agent Registry async initialization complete")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Agent Registry: {e}")
            raise

    async def register_agent(
        self,
        agent_id: str,
        agent_type: AgentType,
        instance: Any,
        priority: AgentPriority = AgentPriority.MEDIUM,
        capabilities: Optional[List[str]] = None,
        configuration: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register a new agent instance.

        Args:
            agent_id: Unique identifier for the agent
            agent_type: Type of agent (market, content, executive, logistics, strategic_chat)
            instance: Reference to the actual agent instance
            priority: Agent priority level
            capabilities: List of agent capabilities
            configuration: Agent configuration dictionary

        Returns:
            True if registration successful, False otherwise
        """
        try:
            with self._registry_lock:
                # Check if agent already registered
                if agent_id in self._agents:
                    logger.warning(f"Agent {agent_id} already registered, updating...")
                    return await self._update_agent_instance(agent_id, instance)

                # Create registered agent record
                registered_agent = RegisteredAgent(
                    agent_id=agent_id,
                    agent_type=agent_type,
                    status=UnifiedAgentStatus.INITIALIZING,
                    priority=priority,
                    instance=instance,
                    capabilities=capabilities or [],
                    configuration=configuration or {},
                )

                # Add to registry
                self._agents[agent_id] = registered_agent

                # Update type mapping
                if agent_type not in self._agents_by_type:
                    self._agents_by_type[agent_type] = set()
                self._agents_by_type[agent_type].add(agent_id)

                # Persist to database
                await self._persist_agent_registration(registered_agent)

                logger.info(f"✅ Registered agent: {agent_id} ({agent_type.value})")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to register agent {agent_id}: {e}")
            return False

    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent instance.

        Args:
            agent_id: ID of agent to unregister

        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            with self._registry_lock:
                if agent_id not in self._agents:
                    logger.warning(f"Agent {agent_id} not found for unregistration")
                    return False

                agent = self._agents[agent_id]

                # Update status to stopped
                await self.update_agent_status(agent_id, UnifiedAgentStatus.STOPPED)

                # Remove from type mapping
                if agent.agent_type in self._agents_by_type:
                    self._agents_by_type[agent.agent_type].discard(agent_id)
                    if not self._agents_by_type[agent.agent_type]:
                        del self._agents_by_type[agent.agent_type]

                # Remove from registry
                del self._agents[agent_id]

                # Persist to database
                await self._persist_agent_unregistration(agent_id)

                logger.info(f"✅ Unregistered agent: {agent_id}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to unregister agent {agent_id}: {e}")
            return False

    async def update_agent_status(
        self, agent_id: str, new_status: UnifiedAgentStatus
    ) -> bool:
        """
        Update an agent's status with validation.

        Args:
            agent_id: ID of agent to update
            new_status: New status to set

        Returns:
            True if update successful, False otherwise
        """
        try:
            with self._registry_lock:
                if agent_id not in self._agents:
                    logger.warning(f"Agent {agent_id} not found for status update")
                    return False

                agent = self._agents[agent_id]
                current_status = agent.status

                # Validate status transition
                if not validate_status_transition(current_status, new_status):
                    logger.warning(
                        f"Invalid status transition for {agent_id}: "
                        f"{current_status.value} -> {new_status.value}"
                    )
                    return False

                # Update status and heartbeat
                agent.status = new_status
                agent.last_heartbeat = datetime.now(timezone.utc)

                # Persist to database
                await self._persist_agent_status_update(agent_id, new_status)

                logger.debug(f"Updated agent {agent_id} status: {new_status.value}")
                return True

        except Exception as e:
            logger.error(f"❌ Failed to update agent {agent_id} status: {e}")
            return False

    def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get agent information by ID."""
        with self._registry_lock:
            return self._agents.get(agent_id)

    def get_agents_by_type(self, agent_type: AgentType) -> List[RegisteredAgent]:
        """Get all agents of a specific type."""
        with self._registry_lock:
            agent_ids = self._agents_by_type.get(agent_type, set())
            return [
                self._agents[agent_id]
                for agent_id in agent_ids
                if agent_id in self._agents
            ]

    def get_all_agents(self) -> List[RegisteredAgent]:
        """Get all registered agents."""
        with self._registry_lock:
            return list(self._agents.values())

    def get_operational_agents(self) -> List[RegisteredAgent]:
        """Get all agents in operational status."""
        with self._registry_lock:
            return [
                agent for agent in self._agents.values() if is_operational(agent.status)
            ]

    async def update_agent_metrics(
        self, agent_id: str, metrics: Dict[str, Any]
    ) -> bool:
        """Update agent performance metrics."""
        try:
            with self._registry_lock:
                if agent_id not in self._agents:
                    return False

                agent = self._agents[agent_id]

                # Update metrics
                for key, value in metrics.items():
                    if hasattr(agent.metrics, key):
                        setattr(agent.metrics, key, value)

                agent.last_heartbeat = datetime.now(timezone.utc)

                # Persist to database
                await self._persist_agent_metrics(agent_id, agent.metrics)

                return True

        except Exception as e:
            logger.error(f"❌ Failed to update metrics for agent {agent_id}: {e}")
            return False

    async def _monitoring_loop(self):
        """Background monitoring loop for agent health."""
        logger.info("🔍 Starting agent monitoring loop")

        while not self._shutdown_event.is_set():
            try:
                await self._check_agent_health()
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _check_agent_health(self):
        """Check health of all registered agents."""
        current_time = datetime.now(timezone.utc)

        with self._registry_lock:
            for agent_id, agent in self._agents.items():
                # Check for stale heartbeats (5 minutes)
                if agent.last_heartbeat:
                    time_since_heartbeat = (
                        current_time - agent.last_heartbeat
                    ).total_seconds()

                    if (
                        time_since_heartbeat > 300
                        and agent.status != UnifiedAgentStatus.STOPPED
                    ):
                        logger.warning(
                            f"Agent {agent_id} heartbeat stale ({time_since_heartbeat}s)"
                        )
                        await self.update_agent_status(
                            agent_id, UnifiedAgentStatus.DISCONNECTED
                        )

    async def _persist_agent_registration(self, agent: RegisteredAgent):
        """Persist agent registration to database."""
        # Implementation would save to unified_agents table
        pass

    async def _persist_agent_unregistration(self, agent_id: str):
        """Persist agent unregistration to database."""
        # Implementation would update unified_agents table
        pass

    async def _persist_agent_status_update(
        self, agent_id: str, status: UnifiedAgentStatus
    ):
        """Persist agent status update to database."""
        # Implementation would update unified_agents table
        pass

    async def _persist_agent_metrics(self, agent_id: str, metrics: AgentMetrics):
        """Persist agent metrics to database."""
        # Implementation would save to agent_performance_metrics table
        pass

    async def _update_agent_instance(self, agent_id: str, instance: Any) -> bool:
        """Update existing agent instance reference."""
        with self._registry_lock:
            if agent_id in self._agents:
                self._agents[agent_id].instance = instance
                self._agents[agent_id].last_heartbeat = datetime.now(timezone.utc)
                return True
        return False

    async def shutdown(self):
        """Shutdown the agent registry."""
        logger.info("🛑 Shutting down Agent Registry")

        self._shutdown_event.set()

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Update all agents to stopped status
        with self._registry_lock:
            for agent_id in list(self._agents.keys()):
                await self.update_agent_status(agent_id, UnifiedAgentStatus.STOPPED)


# Global registry instance
_global_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get the global agent registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = AgentRegistry()
    return _global_registry


@asynccontextmanager
async def agent_registry_context():
    """Context manager for agent registry lifecycle."""
    registry = get_agent_registry()
    try:
        await registry.initialize_async()
        yield registry
    finally:
        await registry.shutdown()
