"""
Base implementation of the Coordinator interface.

This module provides a base implementation of the Coordinator interface
with common functionality for agent registration, discovery, and task delegation.
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
    Coordinator,
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


class BaseCoordinator(Coordinator):
    """
    Base implementation of the Coordinator interface.

    This class provides common functionality for agent registration,
    discovery, and task delegation. It is designed to be extended by
    specific coordinator implementations.
    """

    def __init__(self, coordinator_id: str):
        """
        Initialize the base coordinator.

        Args:
            coordinator_id: Unique identifier for this coordinator
        """
        self.coordinator_id = coordinator_id
        self.logger = get_logger(f"coordinator.{coordinator_id}")

        # Create publisher and subscriber for event-based communication
        self.publisher = create_publisher(source_id=f"coordinator.{coordinator_id}")
        self.subscriber = create_subscriber(
            subscriber_id=f"coordinator.{coordinator_id}"
        )

        # Initialize agent registry
        self.agents: Dict[str, UnifiedAgentInfo] = {}

        # Initialize task registry
        self.tasks: Dict[str, Dict[str, Any]] = {}

        # Initialize conflict registry
        self.conflicts: Dict[str, Dict[str, Any]] = {}

        # Initialize locks for thread safety
        self.agent_lock = asyncio.Lock()
        self.task_lock = asyncio.Lock()
        self.conflict_lock = asyncio.Lock()

    async def register_agent(self, agent_info: UnifiedAgentInfo) -> bool:
        """
        Register an agent with the coordinator.

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
        Unregister an agent from the coordinator.

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

    async def delegate_task(
        self,
        task_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        target_agent_id: Optional[str] = None,
        required_capability: Optional[UnifiedAgentCapability] = None,
        priority: int = 0,
        deadline: Optional[datetime] = None,
    ) -> str:
        """
        Delegate a task to an agent.

        This base implementation handles task creation and assignment.
        Subclasses should override this method to implement specific
        delegation strategies.

        Args:
            task_id: ID of the task
            task_type: Type of the task
            parameters: Task parameters
            target_agent_id: ID of the target agent, or None to auto-select
            required_capability: Required capability for the task
            priority: Priority of the task (higher values = higher priority)
            deadline: Deadline for task completion

        Returns:
            ID of the assigned task

        Raises:
            CoordinationError: If delegation fails
        """
        try:
            # If no task_id is provided, generate one
            if not task_id:
                task_id = str(uuid.uuid4())

            # If a target agent is specified, verify it exists and is healthy
            if target_agent_id:
                agent_info = await self.get_agent_info(target_agent_id)
                if not agent_info:
                    raise CoordinationError(
                        f"Target agent not found: {target_agent_id}", task_id=task_id
                    )

                if not await self.check_agent_health(target_agent_id):
                    raise CoordinationError(
                        f"Target agent is not healthy: {target_agent_id}",
                        task_id=task_id,
                    )

                # If a capability is required, verify the agent has it
                if required_capability and not agent_info.has_capability(
                    required_capability
                ):
                    raise CoordinationError(
                        f"Target agent does not have required capability: {required_capability.name}",
                        agent_id=target_agent_id,
                        task_id=task_id,
                    )

            # If no target agent is specified but a capability is required,
            # find a suitable agent
            elif required_capability:
                agents = await self.find_agents_by_capability(required_capability)
                healthy_agents = [
                    agent
                    for agent in agents
                    if await self.check_agent_health(agent.agent_id)
                ]

                if not healthy_agents:
                    raise CoordinationError(
                        f"No healthy agents found with required capability: {required_capability.name}",
                        task_id=task_id,
                    )

                # Select the agent with the fewest tasks
                # This is a simple load balancing strategy
                # Subclasses may implement more sophisticated strategies
                target_agent_id = await self._select_agent_for_task(healthy_agents)

            else:
                raise CoordinationError(
                    "Either target_agent_id or required_capability must be specified",
                    task_id=task_id,
                )

            # Create the task
            task = {
                "task_id": task_id,
                "task_type": task_type,
                "parameters": parameters,
                "agent_id": target_agent_id,
                "status": "assigned",
                "priority": priority,
                "created_at": datetime.now(),
                "deadline": deadline,
                "result": None,
                "error": None,
            }

            # Store the task
            async with self.task_lock:
                self.tasks[task_id] = task

            # Publish task assignment event
            await self._publish_task_assignment_event(task)

            self.logger.info(
                f"Task delegated: {task_id} ({task_type}) to agent {target_agent_id}"
            )

            return task_id
        except CoordinationError:
            # Re-raise coordination errors
            raise
        except Exception as e:
            error_msg = f"Failed to delegate task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a task.

        Args:
            task_id: ID of the task

        Returns:
            Task status information

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.task_lock:
                if task_id not in self.tasks:
                    raise CoordinationError(
                        f"Task not found: {task_id}", task_id=task_id
                    )

                task = self.tasks[task_id]

                # Return a copy of the task status
                return {
                    "task_id": task["task_id"],
                    "task_type": task["task_type"],
                    "agent_id": task["agent_id"],
                    "status": task["status"],
                    "created_at": task["created_at"],
                    "deadline": task["deadline"],
                    "priority": task["priority"],
                }
        except CoordinationError:
            # Re-raise coordination errors
            raise
        except Exception as e:
            error_msg = f"Failed to get task status {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.

        Args:
            task_id: ID of the task

        Returns:
            True if cancellation was successful

        Raises:
            CoordinationError: If cancellation fails
        """
        try:
            async with self.task_lock:
                if task_id not in self.tasks:
                    self.logger.warning(f"Task not found for cancellation: {task_id}")
                    return False

                task = self.tasks[task_id]

                # Only cancel tasks that are not completed or failed
                if task["status"] in ("completed", "failed"):
                    self.logger.warning(
                        f"Cannot cancel task {task_id} with status {task['status']}"
                    )
                    return False

                # Update task status
                task["status"] = "cancelled"

                # Publish task cancellation event
                await self._publish_task_cancellation_event(task)

                self.logger.info(f"Task cancelled: {task_id}")

                return True
        except Exception as e:
            error_msg = f"Failed to cancel task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """
        Get the result of a completed task.

        Args:
            task_id: ID of the task

        Returns:
            Task result

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.task_lock:
                if task_id not in self.tasks:
                    raise CoordinationError(
                        f"Task not found: {task_id}", task_id=task_id
                    )

                task = self.tasks[task_id]

                if task["status"] != "completed":
                    raise CoordinationError(
                        f"Task not completed: {task_id} (status: {task['status']})",
                        task_id=task_id,
                    )

                # Return a copy of the task result
                return {
                    "task_id": task["task_id"],
                    "task_type": task["task_type"],
                    "agent_id": task["agent_id"],
                    "result": task["result"],
                    "completed_at": task.get("completed_at"),
                }
        except CoordinationError:
            # Re-raise coordination errors
            raise
        except Exception as e:
            error_msg = f"Failed to get task result {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def get_agent_tasks(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        Get tasks assigned to an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of tasks assigned to the agent

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.task_lock:
                # Find all tasks assigned to the agent
                agent_tasks = [
                    task for task in self.tasks.values() if task["agent_id"] == agent_id
                ]

                # Return copies of the tasks
                return [
                    {
                        "task_id": task["task_id"],
                        "task_type": task["task_type"],
                        "status": task["status"],
                        "created_at": task["created_at"],
                        "deadline": task["deadline"],
                        "priority": task["priority"],
                    }
                    for task in agent_tasks
                ]
        except Exception as e:
            error_msg = f"Failed to get agent tasks {agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_id, cause=e)

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: str,
        resolution_parameters: Dict[str, Any],
    ) -> bool:
        """
        Resolve a conflict between agents or tasks.

        This base implementation provides a framework for conflict resolution.
        Subclasses should override this method to implement specific
        resolution strategies.

        Args:
            conflict_id: ID of the conflict
            resolution_strategy: Strategy to use for resolution
            resolution_parameters: Parameters for the resolution strategy

        Returns:
            True if resolution was successful

        Raises:
            CoordinationError: If resolution fails
        """
        try:
            async with self.conflict_lock:
                if conflict_id not in self.conflicts:
                    self.logger.warning(
                        f"Conflict not found for resolution: {conflict_id}"
                    )
                    return False

                conflict = self.conflicts[conflict_id]

                # Only resolve active conflicts
                if conflict["status"] != "active":
                    self.logger.warning(
                        f"Cannot resolve conflict {conflict_id} with status {conflict['status']}"
                    )
                    return False

                # Update conflict status
                conflict["status"] = "resolved"
                conflict["resolution_strategy"] = resolution_strategy
                conflict["resolution_parameters"] = resolution_parameters
                conflict["resolved_at"] = datetime.now()

                # Publish conflict resolution event
                await self._publish_conflict_resolution_event(conflict)

                self.logger.info(
                    f"Conflict resolved: {conflict_id} using strategy {resolution_strategy}"
                )

                return True
        except Exception as e:
            error_msg = f"Failed to resolve conflict {conflict_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def _select_agent_for_task(self, agents: List[UnifiedAgentInfo]) -> str:
        """
        Select an agent for a task from a list of candidates.

        This base implementation uses a simple load balancing strategy.
        Subclasses may override this method to implement more sophisticated
        selection strategies.

        Args:
            agents: List of candidate agents

        Returns:
            ID of the selected agent
        """
        # If there's only one agent, select it
        if len(agents) == 1:
            return agents[0].agent_id

        # Get the number of tasks for each agent
        agent_task_counts = {}
        for agent in agents:
            tasks = await self.get_agent_tasks(agent.agent_id)
            active_tasks = [
                task for task in tasks if task["status"] in ("assigned", "processing")
            ]
            agent_task_counts[agent.agent_id] = len(active_tasks)

        # Select the agent with the fewest active tasks
        return min(agent_task_counts.items(), key=lambda x: x[1])[0]

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

    async def _publish_task_assignment_event(self, task: Dict[str, Any]) -> None:
        """
        Publish a task assignment event.

        Args:
            task: Information about the assigned task
        """
        await self.publisher.publish_command(
            command_name="execute_task",
            parameters={
                "task_id": task["task_id"],
                "task_type": task["task_type"],
                "parameters": task["parameters"],
                "priority": task["priority"],
                "deadline": task["deadline"].isoformat() if task["deadline"] else None,
            },
            target=task["agent_id"],
        )

    async def _publish_task_cancellation_event(self, task: Dict[str, Any]) -> None:
        """
        Publish a task cancellation event.

        Args:
            task: Information about the cancelled task
        """
        await self.publisher.publish_command(
            command_name="cancel_task",
            parameters={"task_id": task["task_id"]},
            target=task["agent_id"],
        )

    async def _publish_conflict_resolution_event(
        self, conflict: Dict[str, Any]
    ) -> None:
        """
        Publish a conflict resolution event.

        Args:
            conflict: Information about the resolved conflict
        """
        await self.publisher.publish_notification(
            notification_name="conflict_resolved",
            data={
                "conflict_id": conflict["conflict_id"],
                "resolution_strategy": conflict["resolution_strategy"],
                "resolved_at": conflict["resolved_at"].isoformat(),
            },
        )
