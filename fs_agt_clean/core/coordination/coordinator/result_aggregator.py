"""
Result Aggregator component for the FlipSync application.

This module provides the ResultAggregator component, which manages result
collection, validation, and aggregation. It is a core component of the
Coordinator, enabling the aggregation of results from multiple agents.
"""

import asyncio
import enum
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union

from fs_agt_clean.core.coordination.coordinator.coordinator import (
    UnifiedAgentCapability,
    UnifiedAgentInfo,
    UnifiedAgentStatus,
    UnifiedAgentType,
    CoordinationError,
)
from fs_agt_clean.core.coordination.coordinator.task_delegator import (
    Task,
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


class AggregationStrategy(enum.Enum):
    """
    Strategy for aggregating results from multiple sources.
    """

    COLLECT = "collect"  # Simply collect all results
    MAJORITY = "majority"  # Use the majority result
    WEIGHTED = "weighted"  # Weight results by source
    FIRST = "first"  # Use the first result
    LAST = "last"  # Use the last result
    CUSTOM = "custom"  # Use a custom aggregation function


class ResultAggregator:
    """
    Component for aggregating results from multiple agents.

    The ResultAggregator manages result collection, validation, and aggregation.
    It provides methods for collecting results from multiple agents and
    aggregating them into a single result.
    """

    def __init__(self, aggregator_id: str):
        """
        Initialize the result aggregator.

        Args:
            aggregator_id: Unique identifier for this aggregator
        """
        self.aggregator_id = aggregator_id
        self.logger = get_logger(f"coordinator.aggregator.{aggregator_id}")

        # Create publisher and subscriber for event-based communication
        self.publisher = create_publisher(
            source_id=f"coordinator.aggregator.{aggregator_id}"
        )
        self.subscriber = create_subscriber(
            subscriber_id=f"coordinator.aggregator.{aggregator_id}"
        )

        # Initialize result registry
        # Maps task IDs to lists of results
        self.results: Dict[str, List[Dict[str, Any]]] = {}

        # Initialize aggregation strategies
        # Maps task IDs to aggregation strategies
        self.strategies: Dict[str, AggregationStrategy] = {}

        # Initialize custom aggregation functions
        # Maps task IDs to custom aggregation functions
        self.custom_aggregators: Dict[str, Callable] = {}

        # Initialize locks for thread safety
        self.result_lock = asyncio.Lock()

        # Initialize subscription IDs
        self.subscription_ids: List[str] = []

    async def start(self) -> None:
        """
        Start the result aggregator.

        This method subscribes to result events.
        """
        # Subscribe to result events
        await self._subscribe_to_events()

        self.logger.info(f"Result aggregator started: {self.aggregator_id}")

    async def stop(self) -> None:
        """
        Stop the result aggregator.

        This method unsubscribes from result events.
        """
        # Unsubscribe from result events
        for subscription_id in self.subscription_ids:
            await self.subscriber.unsubscribe(subscription_id)

        self.subscription_ids = []

        self.logger.info(f"Result aggregator stopped: {self.aggregator_id}")

    async def register_task(
        self,
        task_id: str,
        strategy: AggregationStrategy = AggregationStrategy.COLLECT,
        custom_aggregator: Optional[Callable] = None,
    ) -> bool:
        """
        Register a task for result aggregation.

        Args:
            task_id: ID of the task
            strategy: Aggregation strategy to use
            custom_aggregator: Custom aggregation function, if strategy is CUSTOM

        Returns:
            True if registration was successful

        Raises:
            CoordinationError: If registration fails
        """
        try:
            async with self.result_lock:
                # Initialize result list for the task
                if task_id not in self.results:
                    self.results[task_id] = []

                # Set aggregation strategy
                self.strategies[task_id] = strategy

                # Set custom aggregator if provided
                if strategy == AggregationStrategy.CUSTOM:
                    if custom_aggregator is None:
                        raise CoordinationError(
                            "Custom aggregator function must be provided for CUSTOM strategy",
                            task_id=task_id,
                        )
                    self.custom_aggregators[task_id] = custom_aggregator

                self.logger.info(
                    f"Task registered for aggregation: {task_id} with strategy {strategy.value}"
                )

                return True
        except CoordinationError:
            # Re-raise coordination errors
            raise
        except Exception as e:
            error_msg = f"Failed to register task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def add_result(
        self, task_id: str, agent_id: str, result: Any, metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Add a result for a task.

        Args:
            task_id: ID of the task
            agent_id: ID of the agent that produced the result
            result: The result data
            metadata: Additional metadata for the result

        Returns:
            True if the result was added successfully

        Raises:
            CoordinationError: If adding the result fails
        """
        try:
            async with self.result_lock:
                # Initialize result list for the task if needed
                if task_id not in self.results:
                    self.results[task_id] = []

                # Create result entry
                result_entry = {
                    "agent_id": agent_id,
                    "result": result,
                    "timestamp": datetime.now(),
                    "metadata": metadata or {},
                }

                # Add result to the list
                self.results[task_id].append(result_entry)

                self.logger.info(
                    f"Result added for task {task_id} from agent {agent_id}"
                )

                # Publish result added event
                await self._publish_result_added_event(task_id, agent_id, result)

                return True
        except Exception as e:
            error_msg = f"Failed to add result for task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def get_results(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all results for a task.

        Args:
            task_id: ID of the task

        Returns:
            List of result entries

        Raises:
            CoordinationError: If getting the results fails
        """
        try:
            async with self.result_lock:
                return self.results.get(task_id, [])
        except Exception as e:
            error_msg = f"Failed to get results for task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def aggregate_results(self, task_id: str) -> Any:
        """
        Aggregate results for a task.

        Args:
            task_id: ID of the task

        Returns:
            Aggregated result

        Raises:
            CoordinationError: If aggregation fails
        """
        try:
            # Get all results for the task
            results = await self.get_results(task_id)

            if not results:
                self.logger.warning(f"No results to aggregate for task {task_id}")
                return None

            # Get aggregation strategy
            strategy = self.strategies.get(task_id, AggregationStrategy.COLLECT)

            # Aggregate results based on strategy
            if strategy == AggregationStrategy.COLLECT:
                # Simply collect all results
                aggregated_result = {
                    result["agent_id"]: result["result"] for result in results
                }
            elif strategy == AggregationStrategy.MAJORITY:
                # Use the majority result
                # This assumes results are comparable
                result_counts = {}
                for result_entry in results:
                    result_value = str(
                        result_entry["result"]
                    )  # Convert to string for counting
                    if result_value not in result_counts:
                        result_counts[result_value] = 0
                    result_counts[result_value] += 1

                # Find the majority result
                majority_result = max(result_counts.items(), key=lambda x: x[1])[0]
                aggregated_result = majority_result
            elif strategy == AggregationStrategy.WEIGHTED:
                # Weight results by source
                # This assumes results are numeric and weights are in metadata
                weighted_sum = 0
                total_weight = 0

                for result_entry in results:
                    weight = result_entry["metadata"].get("weight", 1.0)
                    weighted_sum += result_entry["result"] * weight
                    total_weight += weight

                if total_weight > 0:
                    aggregated_result = weighted_sum / total_weight
                else:
                    aggregated_result = None
            elif strategy == AggregationStrategy.FIRST:
                # Use the first result
                aggregated_result = results[0]["result"]
            elif strategy == AggregationStrategy.LAST:
                # Use the last result
                aggregated_result = results[-1]["result"]
            elif strategy == AggregationStrategy.CUSTOM:
                # Use a custom aggregation function
                custom_aggregator = self.custom_aggregators.get(task_id)
                if custom_aggregator:
                    aggregated_result = custom_aggregator(results)
                else:
                    raise CoordinationError(
                        "Custom aggregator function not found for task", task_id=task_id
                    )
            else:
                raise CoordinationError(
                    f"Unknown aggregation strategy: {strategy}", task_id=task_id
                )

            self.logger.info(
                f"Results aggregated for task {task_id} using strategy {strategy.value}"
            )

            # Publish result aggregated event
            await self._publish_result_aggregated_event(
                task_id, aggregated_result, strategy
            )

            return aggregated_result
        except CoordinationError:
            # Re-raise coordination errors
            raise
        except Exception as e:
            error_msg = f"Failed to aggregate results for task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def clear_results(self, task_id: str) -> bool:
        """
        Clear all results for a task.

        Args:
            task_id: ID of the task

        Returns:
            True if the results were cleared successfully

        Raises:
            CoordinationError: If clearing the results fails
        """
        try:
            async with self.result_lock:
                if task_id in self.results:
                    del self.results[task_id]

                if task_id in self.strategies:
                    del self.strategies[task_id]

                if task_id in self.custom_aggregators:
                    del self.custom_aggregators[task_id]

                self.logger.info(f"Results cleared for task {task_id}")

                return True
        except Exception as e:
            error_msg = f"Failed to clear results for task {task_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, task_id=task_id, cause=e)

    async def _subscribe_to_events(self) -> None:
        """
        Subscribe to result-related events.

        This method sets up subscriptions for result events.
        """
        # Subscribe to task result events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"task_result"}),
            handler=self._handle_task_result,
        )
        self.subscription_ids.append(subscription_id)

        # Subscribe to task completed events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"task_completed"}),
            handler=self._handle_task_completed,
        )
        self.subscription_ids.append(subscription_id)

    async def _handle_task_result(self, event: Event) -> None:
        """
        Handle a task result event.

        Args:
            event: The result event
        """
        try:
            # Extract task ID, agent ID, and result from the event
            task_id = event.data.get("task_id")
            agent_id = event.data.get("agent_id")
            result = event.data.get("result")
            metadata = event.data.get("metadata")

            if not task_id or not agent_id:
                self.logger.warning("Received task result event with missing data")
                return

            # Add the result
            await self.add_result(task_id, agent_id, result, metadata)
        except Exception as e:
            self.logger.error(f"Error handling task result: {str(e)}", exc_info=True)

    async def _handle_task_completed(self, event: Event) -> None:
        """
        Handle a task completed event.

        Args:
            event: The completion event
        """
        try:
            # Extract task ID from the event
            task_id = event.data.get("task_id")

            if not task_id:
                self.logger.warning("Received task completed event without task_id")
                return

            # Check if we have results for this task
            results = await self.get_results(task_id)
            if not results:
                self.logger.warning(f"No results found for completed task {task_id}")
                return

            # Aggregate the results
            aggregated_result = await self.aggregate_results(task_id)

            # Publish the aggregated result
            await self._publish_final_result_event(task_id, aggregated_result)
        except Exception as e:
            self.logger.error(
                f"Error handling task completion: {str(e)}", exc_info=True
            )

    async def _publish_result_added_event(
        self, task_id: str, agent_id: str, result: Any
    ) -> None:
        """
        Publish a result added event.

        Args:
            task_id: ID of the task
            agent_id: ID of the agent that produced the result
            result: The result data
        """
        await self.publisher.publish_notification(
            notification_name="result_added",
            data={
                "task_id": task_id,
                "agent_id": agent_id,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _publish_result_aggregated_event(
        self, task_id: str, aggregated_result: Any, strategy: AggregationStrategy
    ) -> None:
        """
        Publish a result aggregated event.

        Args:
            task_id: ID of the task
            aggregated_result: The aggregated result
            strategy: The aggregation strategy used
        """
        await self.publisher.publish_notification(
            notification_name="result_aggregated",
            data={
                "task_id": task_id,
                "strategy": strategy.value,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def _publish_final_result_event(
        self, task_id: str, final_result: Any
    ) -> None:
        """
        Publish a final result event.

        Args:
            task_id: ID of the task
            final_result: The final aggregated result
        """
        await self.publisher.publish_notification(
            notification_name="final_result",
            data={
                "task_id": task_id,
                "result": final_result,
                "timestamp": datetime.now().isoformat(),
            },
        )
