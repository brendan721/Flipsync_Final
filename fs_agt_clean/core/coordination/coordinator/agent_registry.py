"""
UnifiedAgent Registry component for the FlipSync application.

This module provides the UnifiedAgentRegistry component, which manages agent
registration, discovery, and health monitoring. It is a core component
of the Coordinator, enabling agent coordination and task delegation.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from fs_agt_clean.core.coordination.coordinator.coordinator import (
    UnifiedAgentCapability,
    UnifiedAgentInfo,
    UnifiedAgentStatus,
    UnifiedAgentType,
    CoordinationError,
)
from fs_agt_clean.core.coordination.event_system import (
    CompositeFilter,
    Event,
    EventNameFilter,
    EventPriority,
    EventType,
    EventTypeFilter,
    create_publisher,
    create_subscriber,
)
from fs_agt_clean.core.monitoring import get_logger


class UnifiedAgentRegistry:
    """
    Registry for managing agents in the system.

    The UnifiedAgentRegistry manages agent registration, discovery, and health monitoring.
    It provides methods for registering agents, updating their status and capabilities,
    and finding agents based on various criteria.
    """

    def __init__(self, registry_id: str):
        """
        Initialize the agent registry.

        Args:
            registry_id: Unique identifier for this registry
        """
        self.registry_id = registry_id
        self.logger = get_logger(f"coordinator.registry.{registry_id}")

        # Create publisher and subscriber for event-based communication
        self.publisher = create_publisher(
            source_id=f"coordinator.registry.{registry_id}"
        )
        self.subscriber = create_subscriber(
            subscriber_id=f"coordinator.registry.{registry_id}"
        )

        # Initialize agent registry
        self.agents: Dict[str, UnifiedAgentInfo] = {}

        # Initialize lock for thread safety
        self.agent_lock = asyncio.Lock()

        # Initialize health check task
        self.health_check_task = None
        self.health_check_interval = timedelta(minutes=1)
        self.health_check_running = False

    async def start(self) -> None:
        """
        Start the agent registry.

        This method starts the health check task and subscribes to agent events.
        """
        # Start health check task
        if not self.health_check_running:
            self.health_check_running = True
            self.health_check_task = asyncio.create_task(self._health_check_loop())

        # Subscribe to agent events
        await self._subscribe_to_events()

        self.logger.info(f"UnifiedAgent registry started: {self.registry_id}")

    async def stop(self) -> None:
        """
        Stop the agent registry.

        This method stops the health check task and unsubscribes from agent events.
        """
        # Stop health check task
        if self.health_check_running:
            self.health_check_running = False
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass

        # Unsubscribe from agent events
        # (Subscription IDs would be stored when subscribing)

        self.logger.info(f"UnifiedAgent registry stopped: {self.registry_id}")

    async def register_agent(self, agent_info: UnifiedAgentInfo) -> bool:
        """
        Register an agent with the registry.

        Args:
            agent_info: Information about the agent

        Returns:
            True if registration was successful

        Raises:
            CoordinationError: If registration fails
        """
        try:
            async with self.agent_lock:
                # Update status and last seen
                agent_info.update_status(UnifiedAgentStatus.ACTIVE)

                # Store agent info
                self.agents[agent_info.agent_id] = agent_info

                self.logger.info(
                    f"UnifiedAgent registered: {agent_info.agent_id} ({agent_info.name})"
                )

                # Publish agent registration event
                await self._publish_agent_registration_event(agent_info)

                return True
        except Exception as e:
            error_msg = f"Failed to register agent {agent_info.agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_info.agent_id, cause=e)

    async def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the registry.

        Args:
            agent_id: ID of the agent to unregister

        Returns:
            True if unregistration was successful

        Raises:
            CoordinationError: If unregistration fails
        """
        try:
            async with self.agent_lock:
                if agent_id not in self.agents:
                    self.logger.warning(
                        f"UnifiedAgent not found for unregistration: {agent_id}"
                    )
                    return False

                # Get agent info before removal
                agent_info = self.agents[agent_id]

                # Remove agent
                del self.agents[agent_id]

                self.logger.info(f"UnifiedAgent unregistered: {agent_id}")

                # Publish agent unregistration event
                await self._publish_agent_unregistration_event(agent_info)

                return True
        except Exception as e:
            error_msg = f"Failed to unregister agent {agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_id, cause=e)

    async def update_agent_status(self, agent_id: str, status: UnifiedAgentStatus) -> bool:
        """
        Update an agent's status.

        Args:
            agent_id: ID of the agent
            status: New status of the agent

        Returns:
            True if the update was successful

        Raises:
            CoordinationError: If the update fails
        """
        try:
            async with self.agent_lock:
                if agent_id not in self.agents:
                    self.logger.warning(
                        f"UnifiedAgent not found for status update: {agent_id}"
                    )
                    return False

                # Update status
                old_status = self.agents[agent_id].status
                self.agents[agent_id].update_status(status)

                self.logger.info(
                    f"UnifiedAgent status updated: {agent_id} {old_status.value} -> {status.value}"
                )

                # Publish agent status update event
                await self._publish_agent_status_event(self.agents[agent_id])

                return True
        except Exception as e:
            error_msg = f"Failed to update agent status {agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_id, cause=e)

    async def update_agent_capabilities(
        self, agent_id: str, capabilities: List[UnifiedAgentCapability]
    ) -> bool:
        """
        Update an agent's capabilities.

        Args:
            agent_id: ID of the agent
            capabilities: New capabilities of the agent

        Returns:
            True if the update was successful

        Raises:
            CoordinationError: If the update fails
        """
        try:
            async with self.agent_lock:
                if agent_id not in self.agents:
                    self.logger.warning(
                        f"UnifiedAgent not found for capability update: {agent_id}"
                    )
                    return False

                # Update capabilities
                self.agents[agent_id].capabilities = capabilities
                self.agents[agent_id].update_last_seen()

                self.logger.info(
                    f"UnifiedAgent capabilities updated: {agent_id} ({len(capabilities)} capabilities)"
                )

                # Publish agent capability update event
                await self._publish_agent_capability_event(self.agents[agent_id])

                return True
        except Exception as e:
            error_msg = f"Failed to update agent capabilities {agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_id, cause=e)

    async def get_agent_info(self, agent_id: str) -> Optional[UnifiedAgentInfo]:
        """
        Get information about an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            UnifiedAgent information, or None if not found

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.agent_lock:
                return self.agents.get(agent_id)
        except Exception as e:
            error_msg = f"Failed to get agent info {agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_id, cause=e)

    async def find_agents_by_type(self, agent_type: UnifiedAgentType) -> List[UnifiedAgentInfo]:
        """
        Find agents by type.

        Args:
            agent_type: Type of agents to find

        Returns:
            List of matching agents

        Raises:
            CoordinationError: If the search fails
        """
        try:
            async with self.agent_lock:
                return [
                    agent
                    for agent in self.agents.values()
                    if agent.agent_type == agent_type
                ]
        except Exception as e:
            error_msg = f"Failed to find agents by type {agent_type.value}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def find_agents_by_capability(
        self, capability: UnifiedAgentCapability
    ) -> List[UnifiedAgentInfo]:
        """
        Find agents by capability.

        Args:
            capability: Capability to search for

        Returns:
            List of agents with the capability

        Raises:
            CoordinationError: If the search fails
        """
        try:
            async with self.agent_lock:
                return [
                    agent
                    for agent in self.agents.values()
                    if agent.has_capability(capability)
                ]
        except Exception as e:
            error_msg = (
                f"Failed to find agents by capability {capability.name}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def find_agents_by_status(self, status: UnifiedAgentStatus) -> List[UnifiedAgentInfo]:
        """
        Find agents by status.

        Args:
            status: Status to search for

        Returns:
            List of agents with the status

        Raises:
            CoordinationError: If the search fails
        """
        try:
            async with self.agent_lock:
                return [
                    agent for agent in self.agents.values() if agent.status == status
                ]
        except Exception as e:
            error_msg = f"Failed to find agents by status {status.value}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def get_all_agents(self) -> List[UnifiedAgentInfo]:
        """
        Get all registered agents.

        Returns:
            List of all agents

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.agent_lock:
                return list(self.agents.values())
        except Exception as e:
            error_msg = f"Failed to get all agents: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def check_agent_health(self, agent_id: str) -> bool:
        """
        Check if an agent is healthy.

        Args:
            agent_id: ID of the agent

        Returns:
            True if the agent is healthy

        Raises:
            CoordinationError: If the health check fails
        """
        try:
            async with self.agent_lock:
                if agent_id not in self.agents:
                    return False

                agent = self.agents[agent_id]

                # Check if the agent is active
                if not agent.is_active():
                    return False

                # Check if the agent has been seen recently
                if agent.last_seen is None:
                    return False

                # Consider an agent unhealthy if not seen in the last 5 minutes
                max_age = timedelta(minutes=5)
                if datetime.now() - agent.last_seen > max_age:
                    return False

                return True
        except Exception as e:
            error_msg = f"Failed to check agent health {agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_id, cause=e)

    async def ping_agent(self, agent_id: str) -> bool:
        """
        Ping an agent to check if it's responsive.

        Args:
            agent_id: ID of the agent

        Returns:
            True if the agent responded to the ping

        Raises:
            CoordinationError: If the ping fails
        """
        try:
            # Create a future to wait for the response
            response_future = asyncio.Future()

            # Create a correlation ID for this ping
            correlation_id = str(uuid.uuid4())

            # Store the future with the correlation ID
            # In a real implementation, this would be stored in a dictionary
            # and cleaned up after a timeout

            # Send a ping command to the agent
            await self.publisher.publish_command(
                command_name="ping",
                parameters={},
                target=agent_id,
                correlation_id=correlation_id,
            )

            # Wait for the response with a timeout
            try:
                await asyncio.wait_for(response_future, timeout=5.0)
                return True
            except asyncio.TimeoutError:
                self.logger.warning(f"Ping timeout for agent {agent_id}")
                return False
        except Exception as e:
            error_msg = f"Failed to ping agent {agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_id, cause=e)

    async def _health_check_loop(self) -> None:
        """
        Periodic health check loop for all agents.

        This method runs in the background and periodically checks
        the health of all registered agents.
        """
        try:
            while self.health_check_running:
                self.logger.debug("Running agent health check")

                try:
                    # Get all agents
                    agents = await self.get_all_agents()

                    # Check each agent's health
                    for agent in agents:
                        try:
                            # Skip agents that are already known to be inactive
                            if agent.status in (
                                UnifiedAgentStatus.INACTIVE,
                                UnifiedAgentStatus.DISCONNECTED,
                                UnifiedAgentStatus.ERROR,
                            ):
                                continue

                            # Check if the agent has been seen recently
                            if agent.last_seen is None:
                                await self.update_agent_status(
                                    agent.agent_id, UnifiedAgentStatus.UNKNOWN
                                )
                                continue

                            # Consider an agent unhealthy if not seen in the last 5 minutes
                            max_age = timedelta(minutes=5)
                            if datetime.now() - agent.last_seen > max_age:
                                self.logger.warning(
                                    f"UnifiedAgent {agent.agent_id} has not been seen recently, marking as disconnected"
                                )
                                await self.update_agent_status(
                                    agent.agent_id, UnifiedAgentStatus.DISCONNECTED
                                )
                                continue

                            # For agents that are active but haven't been seen very recently,
                            # ping them to check if they're still responsive
                            recent_threshold = timedelta(minutes=1)
                            if datetime.now() - agent.last_seen > recent_threshold:
                                is_responsive = await self.ping_agent(agent.agent_id)
                                if not is_responsive:
                                    self.logger.warning(
                                        f"UnifiedAgent {agent.agent_id} is not responsive, marking as disconnected"
                                    )
                                    await self.update_agent_status(
                                        agent.agent_id, UnifiedAgentStatus.DISCONNECTED
                                    )
                        except Exception as e:
                            self.logger.error(
                                f"Error checking health of agent {agent.agent_id}: {str(e)}",
                                exc_info=True,
                            )
                except Exception as e:
                    self.logger.error(
                        f"Error in health check loop: {str(e)}", exc_info=True
                    )

                # Wait for the next health check interval
                await asyncio.sleep(self.health_check_interval.total_seconds())
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            self.logger.info("Health check loop cancelled")
        except Exception as e:
            self.logger.error(f"Health check loop failed: {str(e)}", exc_info=True)

    async def _subscribe_to_events(self) -> None:
        """
        Subscribe to agent-related events.

        This method sets up subscriptions for agent registration,
        status updates, and other agent-related events.
        """
        # Subscribe to agent heartbeat events
        await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"agent_heartbeat"}),
            handler=self._handle_agent_heartbeat,
        )

        # Subscribe to agent status update events
        await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"agent_status_update"}),
            handler=self._handle_agent_status_update,
        )

        # Subscribe to agent capability update events
        await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"agent_capability_update"}),
            handler=self._handle_agent_capability_update,
        )

        # Subscribe to ping responses
        await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"ping_response"}),
            handler=self._handle_ping_response,
        )

    async def _handle_agent_heartbeat(self, event: Event) -> None:
        """
        Handle an agent heartbeat event.

        Args:
            event: The heartbeat event
        """
        try:
            # Extract agent ID from the event
            agent_id = event.payload.get("data", {}).get("agent_id")
            if not agent_id:
                self.logger.warning("Received heartbeat event without agent_id")
                return

            # Update the agent's last seen timestamp
            async with self.agent_lock:
                if agent_id in self.agents:
                    self.agents[agent_id].update_last_seen()

                    # If the agent was disconnected, mark it as active
                    if self.agents[agent_id].status == UnifiedAgentStatus.DISCONNECTED:
                        await self.update_agent_status(agent_id, UnifiedAgentStatus.ACTIVE)
        except Exception as e:
            self.logger.error(
                f"Error handling agent heartbeat: {str(e)}", exc_info=True
            )

    async def _handle_agent_status_update(self, event: Event) -> None:
        """
        Handle an agent status update event.

        Args:
            event: The status update event
        """
        try:
            # Extract agent ID and status from the event
            data = event.payload.get("data", {})
            agent_id = data.get("agent_id")
            status_str = data.get("status")

            if not agent_id or not status_str:
                self.logger.warning("Received status update event with missing data")
                return

            # Convert status string to enum
            try:
                status = UnifiedAgentStatus(status_str)
            except ValueError:
                self.logger.warning(f"Received invalid status: {status_str}")
                return

            # Update the agent's status
            await self.update_agent_status(agent_id, status)
        except Exception as e:
            self.logger.error(
                f"Error handling agent status update: {str(e)}", exc_info=True
            )

    async def _handle_agent_capability_update(self, event: Event) -> None:
        """
        Handle an agent capability update event.

        Args:
            event: The capability update event
        """
        try:
            # Extract agent ID and capabilities from the event
            data = event.payload.get("data", {})
            agent_id = data.get("agent_id")
            capabilities_data = data.get("capabilities", [])

            if not agent_id:
                self.logger.warning("Received capability update event without agent_id")
                return

            # Convert capability data to objects
            capabilities = [
                UnifiedAgentCapability.from_dict(cap_data) for cap_data in capabilities_data
            ]

            # Update the agent's capabilities
            await self.update_agent_capabilities(agent_id, capabilities)
        except Exception as e:
            self.logger.error(
                f"Error handling agent capability update: {str(e)}", exc_info=True
            )

    async def _handle_ping_response(self, event: Event) -> None:
        """
        Handle a ping response event.

        Args:
            event: The ping response event
        """
        try:
            # Extract agent ID and correlation ID from the event
            data = event.payload.get("data", {})
            agent_id = data.get("agent_id")
            correlation_id = event.correlation_id

            if not agent_id:
                self.logger.warning("Received ping response without agent_id")
                return

            # Update the agent's last seen timestamp
            async with self.agent_lock:
                if agent_id in self.agents:
                    self.agents[agent_id].update_last_seen()

            # In a real implementation, we would resolve the future
            # associated with this correlation ID
        except Exception as e:
            self.logger.error(f"Error handling ping response: {str(e)}", exc_info=True)

    async def _publish_agent_registration_event(self, agent_info: UnifiedAgentInfo) -> None:
        """
        Publish an agent registration event.

        Args:
            agent_info: Information about the registered agent
        """
        await self.publisher.publish_notification(
            notification_name="agent_registered",
            data={
                "agent_id": agent_info.agent_id,
                "agent_type": agent_info.agent_type.value,
                "name": agent_info.name,
                "capabilities": [cap.to_dict() for cap in agent_info.capabilities],
            },
        )

    async def _publish_agent_unregistration_event(self, agent_info: UnifiedAgentInfo) -> None:
        """
        Publish an agent unregistration event.

        Args:
            agent_info: Information about the unregistered agent
        """
        await self.publisher.publish_notification(
            notification_name="agent_unregistered",
            data={
                "agent_id": agent_info.agent_id,
                "agent_type": agent_info.agent_type.value,
                "name": agent_info.name,
            },
        )

    async def _publish_agent_status_event(self, agent_info: UnifiedAgentInfo) -> None:
        """
        Publish an agent status update event.

        Args:
            agent_info: Information about the agent with updated status
        """
        await self.publisher.publish_notification(
            notification_name="agent_status_updated",
            data={
                "agent_id": agent_info.agent_id,
                "status": agent_info.status.value,
                "last_seen": (
                    agent_info.last_seen.isoformat() if agent_info.last_seen else None
                ),
            },
        )

    async def _publish_agent_capability_event(self, agent_info: UnifiedAgentInfo) -> None:
        """
        Publish an agent capability update event.

        Args:
            agent_info: Information about the agent with updated capabilities
        """
        await self.publisher.publish_notification(
            notification_name="agent_capabilities_updated",
            data={
                "agent_id": agent_info.agent_id,
                "capabilities": [cap.to_dict() for cap in agent_info.capabilities],
            },
        )
