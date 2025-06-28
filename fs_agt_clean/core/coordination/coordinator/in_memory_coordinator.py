"""
In-memory implementation of the Coordinator interface.

This module provides an in-memory implementation of the Coordinator interface
that uses the UnifiedAgentRegistry, TaskDelegator, ResultAggregator, and ConflictResolver
components to provide a complete coordination solution.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from fs_agt_clean.core.coordination.coordinator.agent_registry import UnifiedAgentRegistry
from fs_agt_clean.core.coordination.coordinator.conflict_resolver import (
    Conflict,
    ConflictResolver,
    ConflictStatus,
    ConflictType,
    ResolutionStrategy,
)
from fs_agt_clean.core.coordination.coordinator.coordinator import (
    UnifiedAgentCapability,
    UnifiedAgentInfo,
    UnifiedAgentStatus,
    UnifiedAgentType,
    CoordinationError,
    Coordinator,
)
from fs_agt_clean.core.coordination.coordinator.result_aggregator import (
    AggregationStrategy,
    ResultAggregator,
)
from fs_agt_clean.core.coordination.coordinator.task_delegator import (
    Task,
    TaskDelegator,
    TaskPriority,
    TaskStatus,
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


class InMemoryCoordinator(Coordinator):
    """
    In-memory implementation of the Coordinator interface.

    This class provides a complete coordination solution using in-memory
    implementations of the UnifiedAgentRegistry, TaskDelegator, ResultAggregator,
    and ConflictResolver components.
    """

    def __init__(self, coordinator_id: str):
        """
        Initialize the in-memory coordinator.

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

        # Create component instances
        self.agent_registry = UnifiedAgentRegistry(registry_id=f"{coordinator_id}.registry")
        self.task_delegator = TaskDelegator(delegator_id=f"{coordinator_id}.delegator")
        self.result_aggregator = ResultAggregator(
            aggregator_id=f"{coordinator_id}.aggregator"
        )
        self.conflict_resolver = ConflictResolver(
            resolver_id=f"{coordinator_id}.resolver"
        )

        # Initialize subscription IDs
        self.subscription_ids: List[str] = []

    async def start(self) -> None:
        """
        Start the coordinator and all its components.
        """
        # Start components
        await self.agent_registry.start()
        await self.task_delegator.start()
        await self.result_aggregator.start()
        await self.conflict_resolver.start()

        # Subscribe to events
        await self._subscribe_to_events()

        self.logger.info(f"Coordinator started: {self.coordinator_id}")

    async def stop(self) -> None:
        """
        Stop the coordinator and all its components.
        """
        # Stop components
        await self.agent_registry.stop()
        await self.task_delegator.stop()
        await self.result_aggregator.stop()
        await self.conflict_resolver.stop()

        # Unsubscribe from events
        for subscription_id in self.subscription_ids:
            await self.subscriber.unsubscribe(subscription_id)

        self.subscription_ids = []

        self.logger.info(f"Coordinator stopped: {self.coordinator_id}")

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
        return await self.agent_registry.register_agent(agent_info)

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
        return await self.agent_registry.unregister_agent(agent_id)

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
        return await self.agent_registry.update_agent_status(agent_id, status)

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
        return await self.agent_registry.update_agent_capabilities(
            agent_id, capabilities
        )

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
        return await self.agent_registry.get_agent_info(agent_id)

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
        return await self.agent_registry.find_agents_by_type(agent_type)

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
        return await self.agent_registry.find_agents_by_capability(capability)

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
        return await self.agent_registry.find_agents_by_status(status)

    async def get_all_agents(self) -> List[UnifiedAgentInfo]:
        """
        Get all registered agents.

        Returns:
            List of all agents

        Raises:
            CoordinationError: If the retrieval fails
        """
        return await self.agent_registry.get_all_agents()

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
        return await self.agent_registry.check_agent_health(agent_id)

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
                target_agent_id = await self._select_agent_for_task(healthy_agents)

            else:
                raise CoordinationError(
                    "Either target_agent_id or required_capability must be specified",
                    task_id=task_id,
                )

            # Create the task
            task_priority = (
                TaskPriority(priority) if isinstance(priority, int) else priority
            )
            created_task_id = await self.task_delegator.create_task(
                task_type=task_type,
                parameters=parameters,
                agent_id=target_agent_id,
                priority=task_priority,
                deadline=deadline,
            )

            # Assign the task to the agent
            await self.task_delegator.assign_task(created_task_id, target_agent_id)

            # Register the task for result aggregation
            await self.result_aggregator.register_task(
                task_id=created_task_id, strategy=AggregationStrategy.COLLECT
            )

            self.logger.info(
                f"Task delegated: {created_task_id} ({task_type}) to agent {target_agent_id}"
            )

            return created_task_id
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
        task = await self.task_delegator.get_task(task_id)
        if not task:
            raise CoordinationError(f"Task not found: {task_id}", task_id=task_id)

        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "agent_id": task.agent_id,
            "status": task.status.value,
            "created_at": task.created_at,
            "deadline": task.deadline,
            "priority": task.priority.value,
        }

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
        return await self.task_delegator.cancel_task(task_id)

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
        # Get the task
        task = await self.task_delegator.get_task(task_id)
        if not task:
            raise CoordinationError(f"Task not found: {task_id}", task_id=task_id)

        if task.status != TaskStatus.COMPLETED:
            raise CoordinationError(
                f"Task not completed: {task_id} (status: {task.status.value})",
                task_id=task_id,
            )

        # Get the aggregated result
        result = await self.result_aggregator.aggregate_results(task_id)

        return {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "agent_id": task.agent_id,
            "result": result,
            "completed_at": task.completed_at,
        }

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
        tasks = await self.task_delegator.get_agent_tasks(agent_id)

        return [
            {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": task.status.value,
                "created_at": task.created_at,
                "deadline": task.deadline,
                "priority": task.priority.value,
            }
            for task in tasks
        ]

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: str,
        resolution_parameters: Dict[str, Any],
    ) -> bool:
        """
        Resolve a conflict between agents or tasks.

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
            # Convert strategy string to enum
            try:
                strategy = ResolutionStrategy(resolution_strategy)
            except ValueError:
                raise CoordinationError(
                    f"Invalid resolution strategy: {resolution_strategy}",
                    cause=ValueError(f"Invalid strategy: {resolution_strategy}"),
                )

            # Resolve the conflict
            return await self.conflict_resolver.resolve_conflict(
                conflict_id=conflict_id,
                strategy=strategy,
                resolution_params=resolution_parameters,
            )
        except CoordinationError:
            # Re-raise coordination errors
            raise
        except Exception as e:
            error_msg = f"Failed to resolve conflict {conflict_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def _select_agent_for_task(self, agents: List[UnifiedAgentInfo]) -> str:
        """
        Select an agent for a task from a list of candidates.

        This implementation uses a simple load balancing strategy.

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

    async def _subscribe_to_events(self) -> None:
        """
        Subscribe to coordination-related events.

        This method sets up subscriptions for agent registration,
        task delegation, and other coordination-related events.
        """
        # Subscribe to agent registration events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"agent_registration_request"}),
            handler=self._handle_agent_registration_request,
        )
        self.subscription_ids.append(subscription_id)

        # Subscribe to task delegation events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"task_delegation_request"}),
            handler=self._handle_task_delegation_request,
        )
        self.subscription_ids.append(subscription_id)

        # Subscribe to conflict detection events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"conflict_detection_request"}),
            handler=self._handle_conflict_detection_request,
        )
        self.subscription_ids.append(subscription_id)

    async def _handle_agent_registration_request(self, event: Event) -> None:
        """
        Handle an agent registration request event.

        Args:
            event: The registration request event
        """
        try:
            # Extract agent information from the event
            agent_id = event.data.get("agent_id")
            agent_type_str = event.data.get("agent_type")
            name = event.data.get("name")
            description = event.data.get("description")
            capabilities_data = event.data.get("capabilities", [])

            if not agent_id or not agent_type_str or not name:
                self.logger.warning(
                    "Received agent registration request with missing data"
                )
                return

            # Convert agent type string to enum
            try:
                agent_type = UnifiedAgentType(agent_type_str)
            except ValueError:
                self.logger.warning(f"Received invalid agent type: {agent_type_str}")
                return

            # Convert capability data to objects
            capabilities = [
                UnifiedAgentCapability.from_dict(cap_data) for cap_data in capabilities_data
            ]

            # Create agent info
            agent_info = UnifiedAgentInfo(
                agent_id=agent_id,
                agent_type=agent_type,
                name=name,
                description=description or "",
                capabilities=capabilities,
            )

            # Register the agent
            await self.register_agent(agent_info)
        except Exception as e:
            self.logger.error(
                f"Error handling agent registration request: {str(e)}", exc_info=True
            )

    async def _handle_task_delegation_request(self, event: Event) -> None:
        """
        Handle a task delegation request event.

        Args:
            event: The delegation request event
        """
        try:
            # Extract task information from the event
            task_id = event.data.get("task_id")
            task_type = event.data.get("task_type")
            parameters = event.data.get("parameters", {})
            target_agent_id = event.data.get("target_agent_id")
            required_capability_data = event.data.get("required_capability")
            priority = event.data.get("priority", 0)
            deadline_str = event.data.get("deadline")

            if not task_type:
                self.logger.warning(
                    "Received task delegation request without task_type"
                )
                return

            # Convert deadline string to datetime if provided
            deadline = None
            if deadline_str:
                try:
                    deadline = datetime.fromisoformat(deadline_str)
                except ValueError:
                    self.logger.warning(f"Received invalid deadline: {deadline_str}")

            # Convert required capability data to object if provided
            required_capability = None
            if required_capability_data:
                try:
                    required_capability = UnifiedAgentCapability.from_dict(
                        required_capability_data
                    )
                except Exception as e:
                    self.logger.warning(f"Received invalid capability data: {str(e)}")

            # Delegate the task
            await self.delegate_task(
                task_id=task_id or str(uuid.uuid4()),
                task_type=task_type,
                parameters=parameters,
                target_agent_id=target_agent_id,
                required_capability=required_capability,
                priority=priority,
                deadline=deadline,
            )
        except Exception as e:
            self.logger.error(
                f"Error handling task delegation request: {str(e)}", exc_info=True
            )

    async def _handle_conflict_detection_request(self, event: Event) -> None:
        """
        Handle a conflict detection request event.

        Args:
            event: The conflict detection request event
        """
        try:
            # Extract conflict information from the event
            conflict_type_str = event.data.get("conflict_type")
            entities = event.data.get("entities")
            description = event.data.get("description")
            metadata = event.data.get("metadata")

            if not conflict_type_str or not entities or not description:
                self.logger.warning(
                    "Received conflict detection request with missing data"
                )
                return

            # Convert conflict type string to enum
            try:
                conflict_type = ConflictType(conflict_type_str)
            except ValueError:
                self.logger.warning(
                    f"Received invalid conflict type: {conflict_type_str}"
                )
                return

            # Detect the conflict
            await self.conflict_resolver.detect_conflict(
                conflict_type=conflict_type,
                entities=entities,
                description=description,
                metadata=metadata,
            )
        except Exception as e:
            self.logger.error(
                f"Error handling conflict detection request: {str(e)}", exc_info=True
            )
