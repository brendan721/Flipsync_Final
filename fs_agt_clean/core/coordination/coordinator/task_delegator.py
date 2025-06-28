"""
Task Delegator component for the FlipSync application.

This module provides the TaskDelegator component, which manages task
delegation, tracking, and lifecycle management. It is a core component
of the Coordinator, enabling task assignment and execution.
"""

import asyncio
import enum
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


class TaskStatus(enum.Enum):
    """
    Status of a task in the system.
    """

    CREATED = "created"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(enum.IntEnum):
    """
    Priority of a task in the system.

    Higher values indicate higher priority.
    """

    LOW = 0
    NORMAL = 50
    HIGH = 100
    CRITICAL = 200


class Task:
    """
    Task that can be delegated to an agent.

    Tasks represent units of work that can be assigned to agents for execution.
    They have a lifecycle from creation to completion or failure.
    """

    def __init__(
        self,
        task_id: str,
        task_type: str,
        parameters: Dict[str, Any],
        agent_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        deadline: Optional[datetime] = None,
        metadata: Dict[str, Any] = None,
    ):
        """
        Initialize a task.

        Args:
            task_id: Unique identifier for the task
            task_type: Type of the task
            parameters: Parameters for the task
            agent_id: ID of the agent assigned to the task
            parent_task_id: ID of the parent task, if this is a subtask
            priority: Priority of the task
            deadline: Deadline for task completion
            metadata: Additional metadata for the task
        """
        self.task_id = task_id
        self.task_type = task_type
        self.parameters = parameters
        self.agent_id = agent_id
        self.parent_task_id = parent_task_id
        self.priority = priority
        self.deadline = deadline
        self.metadata = metadata or {}

        # Task lifecycle information
        self.status = TaskStatus.CREATED
        self.created_at = datetime.now()
        self.assigned_at = None
        self.accepted_at = None
        self.processing_at = None
        self.completed_at = None
        self.failed_at = None
        self.cancelled_at = None

        # Task result information
        self.result = None
        self.error = None

        # Subtask information
        self.subtasks: List[str] = []
        self.completed_subtasks: List[str] = []

        # Mobile optimization information
        self.battery_intensive = self.metadata.get("battery_intensive", False)
        self.network_intensive = self.metadata.get("network_intensive", False)
        self.storage_intensive = self.metadata.get("storage_intensive", False)
        self.cpu_intensive = self.metadata.get("cpu_intensive", False)
        self.memory_intensive = self.metadata.get("memory_intensive", False)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the task to a dictionary.

        Returns:
            Dictionary representation of the task
        """
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "parameters": self.parameters,
            "agent_id": self.agent_id,
            "parent_task_id": self.parent_task_id,
            "priority": self.priority.value,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "metadata": self.metadata,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "processing_at": (
                self.processing_at.isoformat() if self.processing_at else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "failed_at": self.failed_at.isoformat() if self.failed_at else None,
            "cancelled_at": (
                self.cancelled_at.isoformat() if self.cancelled_at else None
            ),
            "result": self.result,
            "error": self.error,
            "subtasks": self.subtasks,
            "completed_subtasks": self.completed_subtasks,
            "battery_intensive": self.battery_intensive,
            "network_intensive": self.network_intensive,
            "storage_intensive": self.storage_intensive,
            "cpu_intensive": self.cpu_intensive,
            "memory_intensive": self.memory_intensive,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """
        Create a task from a dictionary.

        Args:
            data: Dictionary containing task data

        Returns:
            Task instance
        """
        # Create the task with basic information
        deadline = None
        if data.get("deadline"):
            deadline = datetime.fromisoformat(data["deadline"])

        task = cls(
            task_id=data["task_id"],
            task_type=data["task_type"],
            parameters=data["parameters"],
            agent_id=data.get("agent_id"),
            parent_task_id=data.get("parent_task_id"),
            priority=TaskPriority(data.get("priority", TaskPriority.NORMAL.value)),
            deadline=deadline,
            metadata=data.get("metadata", {}),
        )

        # Set task lifecycle information
        task.status = TaskStatus(data.get("status", TaskStatus.CREATED.value))
        task.created_at = datetime.fromisoformat(data["created_at"])

        if data.get("assigned_at"):
            task.assigned_at = datetime.fromisoformat(data["assigned_at"])

        if data.get("accepted_at"):
            task.accepted_at = datetime.fromisoformat(data["accepted_at"])

        if data.get("processing_at"):
            task.processing_at = datetime.fromisoformat(data["processing_at"])

        if data.get("completed_at"):
            task.completed_at = datetime.fromisoformat(data["completed_at"])

        if data.get("failed_at"):
            task.failed_at = datetime.fromisoformat(data["failed_at"])

        if data.get("cancelled_at"):
            task.cancelled_at = datetime.fromisoformat(data["cancelled_at"])

        # Set task result information
        task.result = data.get("result")
        task.error = data.get("error")

        # Set subtask information
        task.subtasks = data.get("subtasks", [])
        task.completed_subtasks = data.get("completed_subtasks", [])

        # Set mobile optimization information
        task.battery_intensive = data.get("battery_intensive", False)
        task.network_intensive = data.get("network_intensive", False)
        task.storage_intensive = data.get("storage_intensive", False)
        task.cpu_intensive = data.get("cpu_intensive", False)
        task.memory_intensive = data.get("memory_intensive", False)

        return task

    def update_status(self, status: TaskStatus) -> None:
        """
        Update the task's status.

        Args:
            status: New status of the task
        """
        old_status = self.status
        self.status = status

        # Update timestamp based on the new status
        now = datetime.now()
        if status == TaskStatus.ASSIGNED and not self.assigned_at:
            self.assigned_at = now
        elif status == TaskStatus.ACCEPTED and not self.accepted_at:
            self.accepted_at = now
        elif status == TaskStatus.PROCESSING and not self.processing_at:
            self.processing_at = now
        elif status == TaskStatus.COMPLETED and not self.completed_at:
            self.completed_at = now
        elif status == TaskStatus.FAILED and not self.failed_at:
            self.failed_at = now
        elif status == TaskStatus.CANCELLED and not self.cancelled_at:
            self.cancelled_at = now

    def add_subtask(self, subtask_id: str) -> None:
        """
        Add a subtask to this task.

        Args:
            subtask_id: ID of the subtask
        """
        if subtask_id not in self.subtasks:
            self.subtasks.append(subtask_id)

    def complete_subtask(self, subtask_id: str) -> None:
        """
        Mark a subtask as completed.

        Args:
            subtask_id: ID of the completed subtask
        """
        if subtask_id in self.subtasks and subtask_id not in self.completed_subtasks:
            self.completed_subtasks.append(subtask_id)

    def is_complete(self) -> bool:
        """
        Check if the task is complete.

        Returns:
            True if the task is complete
        """
        return self.status == TaskStatus.COMPLETED

    def is_failed(self) -> bool:
        """
        Check if the task has failed.

        Returns:
            True if the task has failed
        """
        return self.status in (TaskStatus.FAILED, TaskStatus.TIMEOUT)

    def is_cancelled(self) -> bool:
        """
        Check if the task has been cancelled.

        Returns:
            True if the task has been cancelled
        """
        return self.status == TaskStatus.CANCELLED

    def is_active(self) -> bool:
        """
        Check if the task is active.

        Returns:
            True if the task is active
        """
        return self.status in (
            TaskStatus.CREATED,
            TaskStatus.ASSIGNED,
            TaskStatus.ACCEPTED,
            TaskStatus.PROCESSING,
        )

    def is_overdue(self) -> bool:
        """
        Check if the task is overdue.

        Returns:
            True if the task is overdue
        """
        if not self.deadline:
            return False

        return datetime.now() > self.deadline

    def all_subtasks_completed(self) -> bool:
        """
        Check if all subtasks are completed.

        Returns:
            True if all subtasks are completed
        """
        return len(self.subtasks) > 0 and len(self.subtasks) == len(
            self.completed_subtasks
        )

    def __str__(self) -> str:
        """
        Get string representation of the task.

        Returns:
            String representation
        """
        return f"Task({self.task_id}, {self.task_type}, {self.status.value})"


class TaskDelegator:
    """
    Component for delegating tasks to agents.

    The TaskDelegator manages task delegation, tracking, and lifecycle management.
    It provides methods for creating tasks, assigning them to agents, and tracking
    their status and results.
    """

    def __init__(self, delegator_id: str):
        """
        Initialize the task delegator.

        Args:
            delegator_id: Unique identifier for this delegator
        """
        self.delegator_id = delegator_id
        self.logger = get_logger(f"coordinator.delegator.{delegator_id}")

        # Create publisher and subscriber for event-based communication
        self.publisher = create_publisher(
            source_id=f"coordinator.delegator.{delegator_id}"
        )
        self.subscriber = create_subscriber(
            subscriber_id=f"coordinator.delegator.{delegator_id}"
        )

        # Initialize task registry
        self.tasks: Dict[str, Task] = {}

        # Initialize task dependency graph
        # Maps task IDs to lists of dependent task IDs
        self.task_dependencies: Dict[str, List[str]] = {}

        # Initialize locks for thread safety
        self.task_lock = asyncio.Lock()

        # Initialize task monitoring task
        self.task_monitor_task = None
        self.task_monitor_interval = timedelta(seconds=30)
        self.task_monitor_running = False

        # Initialize subscription IDs
        self.subscription_ids: List[str] = []

    async def start(self) -> None:
        """
        Start the task delegator.

        This method starts the task monitoring task and subscribes to task events.
        """
        # Start task monitoring task
        if not self.task_monitor_running:
            self.task_monitor_running = True
            self.task_monitor_task = asyncio.create_task(self._task_monitor_loop())

        # Subscribe to task events
        await self._subscribe_to_events()

        self.logger.info(f"Task delegator started: {self.delegator_id}")

    async def stop(self) -> None:
        """
        Stop the task delegator.

        This method stops the task monitoring task and unsubscribes from task events.
        """
        # Stop task monitoring task
        if self.task_monitor_running:
            self.task_monitor_running = False
            if self.task_monitor_task:
                self.task_monitor_task.cancel()
                try:
                    await self.task_monitor_task
                except asyncio.CancelledError:
                    pass

        # Unsubscribe from task events
        for subscription_id in self.subscription_ids:
            await self.subscriber.unsubscribe(subscription_id)

        self.subscription_ids = []

        self.logger.info(f"Task delegator stopped: {self.delegator_id}")

    async def create_task(
        self,
        task_type: str,
        parameters: Dict[str, Any],
        agent_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        deadline: Optional[datetime] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Create a new task.

        Args:
            task_type: Type of the task
            parameters: Parameters for the task
            agent_id: ID of the agent to assign the task to
            parent_task_id: ID of the parent task, if this is a subtask
            priority: Priority of the task
            deadline: Deadline for task completion
            metadata: Additional metadata for the task

        Returns:
            ID of the created task

        Raises:
            CoordinationError: If task creation fails
        """
        try:
            # Generate a task ID
            task_id = str(uuid.uuid4())

            # Create the task
            task = Task(
                task_id=task_id,
                task_type=task_type,
                parameters=parameters,
                agent_id=agent_id,
                parent_task_id=parent_task_id,
                priority=priority,
                deadline=deadline,
                metadata=metadata,
            )

            # Store the task
            async with self.task_lock:
                self.tasks[task_id] = task

                # If this is a subtask, update the parent task
                if parent_task_id and parent_task_id in self.tasks:
                    self.tasks[parent_task_id].add_subtask(task_id)

                    # Add to dependency graph
                    if parent_task_id not in self.task_dependencies:
                        self.task_dependencies[parent_task_id] = []

                    self.task_dependencies[parent_task_id].append(task_id)

            # Publish task created event
            await self._publish_task_created_event(task)

            self.logger.info(
                f"Task created: {task_id} ({task_type})"
                f"{' for agent ' + agent_id if agent_id else ''}"
                f"{' as subtask of ' + parent_task_id if parent_task_id else ''}"
            )

            return task_id
        except Exception as e:
            error_msg = f"Failed to create task: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def assign_task(self, task_id: str, agent_id: str) -> bool:
        """
        Assign a task to an agent.

        Args:
            task_id: ID of the task
            agent_id: ID of the agent

        Returns:
            True if assignment was successful

        Raises:
            CoordinationError: If assignment fails
        """
        try:
            async with self.task_lock:
                if task_id not in self.tasks:
                    self.logger.warning(f"Task not found for assignment: {task_id}")
                    return False

                task = self.tasks[task_id]

                # Only assign tasks that are in the CREATED state
                if task.status != TaskStatus.CREATED:
                    self.logger.warning(
                        f"Cannot assign task {task_id} with status {task.status.value}"
                    )
                    return False

                # Update task agent and status
                task.agent_id = agent_id
                task.update_status(TaskStatus.ASSIGNED)

            # Publish task assignment event
            await self._publish_task_assignment_event(task)

            self.logger.info(f"Task assigned: {task_id} to agent {agent_id}")

            return True
        except Exception as e:
            error_msg = f"Failed to assign task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def update_task_status(
        self, task_id: str, status: TaskStatus, result: Any = None, error: str = None
    ) -> bool:
        """
        Update a task's status.

        Args:
            task_id: ID of the task
            status: New status of the task
            result: Task result, if completed
            error: Error message, if failed

        Returns:
            True if the update was successful

        Raises:
            CoordinationError: If the update fails
        """
        try:
            async with self.task_lock:
                if task_id not in self.tasks:
                    self.logger.warning(f"Task not found for status update: {task_id}")
                    return False

                task = self.tasks[task_id]
                old_status = task.status

                # Update task status
                task.update_status(status)

                # Update result or error if provided
                if status == TaskStatus.COMPLETED and result is not None:
                    task.result = result
                    # Publish task result event
                    await self._publish_task_result_event(task, result)

                if status == TaskStatus.FAILED and error is not None:
                    task.error = error

            # Publish task status update event
            await self._publish_task_status_event(task)

            self.logger.info(
                f"Task status updated: {task_id} {old_status.value} -> {status.value}"
            )

            # If the task is completed or failed, check if it has a parent task
            # and update the parent task if all subtasks are completed
            if (
                status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
                and task.parent_task_id
            ):
                await self._check_parent_task_completion(task.parent_task_id)

            return True
        except Exception as e:
            error_msg = f"Failed to update task status {task_id}: {str(e)}"
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

                # Only cancel tasks that are not completed, failed, or already cancelled
                if task.status in (
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                ):
                    self.logger.warning(
                        f"Cannot cancel task {task_id} with status {task.status.value}"
                    )
                    return False

                # Update task status
                task.update_status(TaskStatus.CANCELLED)

            # Publish task cancellation event
            await self._publish_task_cancellation_event(task)

            self.logger.info(f"Task cancelled: {task_id}")

            # Cancel all subtasks
            await self._cancel_subtasks(task_id)

            return True
        except Exception as e:
            error_msg = f"Failed to cancel task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get a task by ID.

        Args:
            task_id: ID of the task

        Returns:
            Task, or None if not found

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.task_lock:
                return self.tasks.get(task_id)
        except Exception as e:
            error_msg = f"Failed to get task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def get_agent_tasks(
        self, agent_id: str, status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """
        Get tasks assigned to an agent.

        Args:
            agent_id: ID of the agent
            status: Filter by task status

        Returns:
            List of tasks assigned to the agent

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.task_lock:
                if status:
                    return [
                        task
                        for task in self.tasks.values()
                        if task.agent_id == agent_id and task.status == status
                    ]
                else:
                    return [
                        task
                        for task in self.tasks.values()
                        if task.agent_id == agent_id
                    ]
        except Exception as e:
            error_msg = f"Failed to get agent tasks {agent_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, agent_id=agent_id, cause=e)

    async def get_subtasks(self, task_id: str) -> List[Task]:
        """
        Get subtasks of a task.

        Args:
            task_id: ID of the parent task

        Returns:
            List of subtasks

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.task_lock:
                if task_id not in self.tasks:
                    return []

                parent_task = self.tasks[task_id]

                return [
                    self.tasks[subtask_id]
                    for subtask_id in parent_task.subtasks
                    if subtask_id in self.tasks
                ]
        except Exception as e:
            error_msg = f"Failed to get subtasks {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def decompose_task(
        self, task_id: str, subtask_definitions: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Decompose a task into subtasks.

        Args:
            task_id: ID of the parent task
            subtask_definitions: List of subtask definitions

        Returns:
            List of subtask IDs

        Raises:
            CoordinationError: If decomposition fails
        """
        try:
            # Check if the parent task exists
            parent_task = await self.get_task(task_id)
            if not parent_task:
                raise CoordinationError(
                    f"Parent task not found: {task_id}", task_id=task_id
                )

            # Create subtasks
            subtask_ids = []
            for subtask_def in subtask_definitions:
                subtask_id = await self.create_task(
                    task_type=subtask_def["task_type"],
                    parameters=subtask_def["parameters"],
                    agent_id=subtask_def.get("agent_id"),
                    parent_task_id=task_id,
                    priority=subtask_def.get("priority", parent_task.priority),
                    deadline=subtask_def.get("deadline"),
                    metadata=subtask_def.get("metadata"),
                )
                subtask_ids.append(subtask_id)

            self.logger.info(
                f"Task decomposed: {task_id} into {len(subtask_ids)} subtasks"
            )

            return subtask_ids
        except CoordinationError:
            # Re-raise coordination errors
            raise
        except Exception as e:
            error_msg = f"Failed to decompose task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def _check_parent_task_completion(self, parent_task_id: str) -> None:
        """
        Check if a parent task can be completed based on its subtasks.

        Args:
            parent_task_id: ID of the parent task
        """
        try:
            async with self.task_lock:
                if parent_task_id not in self.tasks:
                    return

                parent_task = self.tasks[parent_task_id]

                # Skip if the parent task is already completed, failed, or cancelled
                if not parent_task.is_active():
                    return

                # Get all subtasks
                subtasks = await self.get_subtasks(parent_task_id)

                # Check if all subtasks are completed or failed
                all_completed = all(
                    subtask.is_complete()
                    or subtask.is_failed()
                    or subtask.is_cancelled()
                    for subtask in subtasks
                )

                if all_completed:
                    # Check if any subtasks failed
                    any_failed = any(subtask.is_failed() for subtask in subtasks)

                    if any_failed:
                        # If any subtasks failed, mark the parent task as failed
                        await self.update_task_status(
                            parent_task_id,
                            TaskStatus.FAILED,
                            error="One or more subtasks failed",
                        )
                    else:
                        # If all subtasks completed successfully, mark the parent task as completed
                        # Aggregate results from subtasks
                        results = {
                            subtask.task_id: subtask.result
                            for subtask in subtasks
                            if subtask.is_complete()
                        }

                        await self.update_task_status(
                            parent_task_id, TaskStatus.COMPLETED, result=results
                        )
        except Exception as e:
            self.logger.error(
                f"Error checking parent task completion {parent_task_id}: {str(e)}",
                exc_info=True,
            )

    async def _cancel_subtasks(self, parent_task_id: str) -> None:
        """
        Cancel all subtasks of a parent task.

        Args:
            parent_task_id: ID of the parent task
        """
        try:
            # Get all subtasks
            subtasks = await self.get_subtasks(parent_task_id)

            # Cancel each subtask
            for subtask in subtasks:
                await self.cancel_task(subtask.task_id)
        except Exception as e:
            self.logger.error(
                f"Error cancelling subtasks of {parent_task_id}: {str(e)}",
                exc_info=True,
            )

    async def _task_monitor_loop(self) -> None:
        """
        Periodic task monitoring loop.

        This method runs in the background and periodically checks
        for overdue tasks and updates their status.
        """
        try:
            while self.task_monitor_running:
                self.logger.debug("Running task monitor")

                try:
                    # Get all active tasks
                    async with self.task_lock:
                        active_tasks = [
                            task for task in self.tasks.values() if task.is_active()
                        ]

                    # Check each task for overdue deadline
                    for task in active_tasks:
                        try:
                            if task.is_overdue():
                                self.logger.warning(
                                    f"Task {task.task_id} is overdue, marking as timeout"
                                )
                                await self.update_task_status(
                                    task.task_id,
                                    TaskStatus.TIMEOUT,
                                    error="Task exceeded deadline",
                                )
                        except Exception as e:
                            self.logger.error(
                                f"Error checking task {task.task_id}: {str(e)}",
                                exc_info=True,
                            )
                except Exception as e:
                    self.logger.error(
                        f"Error in task monitor loop: {str(e)}", exc_info=True
                    )

                # Wait for the next monitoring interval
                await asyncio.sleep(self.task_monitor_interval.total_seconds())
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            self.logger.info("Task monitor loop cancelled")
        except Exception as e:
            self.logger.error(f"Task monitor loop failed: {str(e)}", exc_info=True)

    async def _subscribe_to_events(self) -> None:
        """
        Subscribe to task-related events.

        This method sets up subscriptions for task status updates,
        task completion, and other task-related events.
        """
        # Subscribe to task status update events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"task_status_update"}),
            handler=self._handle_task_status_update,
        )
        self.subscription_ids.append(subscription_id)

        # Subscribe to task completion events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"task_completed"}),
            handler=self._handle_task_completed,
        )
        self.subscription_ids.append(subscription_id)

        # Subscribe to task failure events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"task_failed"}),
            handler=self._handle_task_failed,
        )
        self.subscription_ids.append(subscription_id)

    async def _handle_task_status_update(self, event: Event) -> None:
        """
        Handle a task status update event.

        Args:
            event: The status update event
        """
        try:
            # Extract task ID and status from the event
            task_id = event.data.get("task_id")
            status_str = event.data.get("status")

            if not task_id or not status_str:
                self.logger.warning(
                    "Received task status update event with missing data"
                )
                return

            # Convert status string to enum
            try:
                status = TaskStatus(status_str)
            except ValueError:
                self.logger.warning(f"Received invalid task status: {status_str}")
                return

            # Update the task status
            await self.update_task_status(
                task_id,
                status,
                result=event.data.get("result"),
                error=event.data.get("error"),
            )
        except Exception as e:
            self.logger.error(
                f"Error handling task status update: {str(e)}", exc_info=True
            )

    async def _handle_task_completed(self, event: Event) -> None:
        """
        Handle a task completion event.

        Args:
            event: The completion event
        """
        try:
            # Extract task ID and result from the event
            task_id = event.data.get("task_id")
            result = event.data.get("result")

            if not task_id:
                self.logger.warning("Received task completion event without task_id")
                return

            # Update the task status
            await self.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
        except Exception as e:
            self.logger.error(
                f"Error handling task completion: {str(e)}", exc_info=True
            )

    async def _handle_task_failed(self, event: Event) -> None:
        """
        Handle a task failure event.

        Args:
            event: The failure event
        """
        try:
            # Extract task ID and error from the event
            task_id = event.data.get("task_id")
            error = event.data.get("error")

            if not task_id:
                self.logger.warning("Received task failure event without task_id")
                return

            # Update the task status
            await self.update_task_status(task_id, TaskStatus.FAILED, error=error)
        except Exception as e:
            self.logger.error(f"Error handling task failure: {str(e)}", exc_info=True)

    async def _publish_task_created_event(self, task: Task) -> None:
        """
        Publish a task created event.

        Args:
            task: The created task
        """
        await self.publisher.publish_notification(
            notification_name="task_created",
            data={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "agent_id": task.agent_id,
                "parent_task_id": task.parent_task_id,
                "priority": task.priority.value,
                "deadline": task.deadline.isoformat() if task.deadline else None,
            },
        )

    async def _publish_task_assignment_event(self, task: Task) -> None:
        """
        Publish a task assignment event.

        Args:
            task: The assigned task
        """
        await self.publisher.publish_command(
            command_name="execute_task",
            parameters={
                "task_id": task.task_id,
                "task_type": task.task_type,
                "parameters": task.parameters,
                "priority": task.priority.value,
                "deadline": task.deadline.isoformat() if task.deadline else None,
            },
            target=task.agent_id,
        )

    async def _publish_task_result_event(self, task: Task, result: Any) -> None:
        """
        Publish a task result event.

        Args:
            task: The task with the result
            result: The task result
        """
        await self.publisher.publish_notification(
            notification_name="task_result",
            data={"task_id": task.task_id, "agent_id": task.agent_id, "result": result},
        )

    async def _publish_task_status_event(self, task: Task) -> None:
        """
        Publish a task status update event.

        Args:
            task: The updated task
        """
        await self.publisher.publish_notification(
            notification_name="task_status_updated",
            data={
                "task_id": task.task_id,
                "status": task.status.value,
                "agent_id": task.agent_id,
                "result": task.result if task.is_complete() else None,
                "error": task.error if task.is_failed() else None,
            },
        )

    async def _publish_task_cancellation_event(self, task: Task) -> None:
        """
        Publish a task cancellation event.

        Args:
            task: The cancelled task
        """
        await self.publisher.publish_command(
            command_name="cancel_task",
            parameters={"task_id": task.task_id},
            target=task.agent_id,
        )
