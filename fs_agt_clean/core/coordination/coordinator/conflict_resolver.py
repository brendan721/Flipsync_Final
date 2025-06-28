"""
Conflict Resolver component for the FlipSync application.

This module provides the ConflictResolver component, which manages conflict
detection, classification, and resolution. It is a core component of the
Coordinator, enabling harmonious operation of the agent ecosystem.
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


class ConflictType(enum.Enum):
    """
    Type of conflict in the system.
    """

    RESOURCE = "resource"  # Conflict over a resource
    TASK = "task"  # Conflict between tasks
    AGENT = "agent"  # Conflict between agents
    PRIORITY = "priority"  # Conflict over priority
    AUTHORITY = "authority"  # Conflict over authority
    CAPABILITY = "capability"  # Conflict over capability
    DATA = "data"  # Conflict over data
    OTHER = "other"  # Other type of conflict


class ConflictStatus(enum.Enum):
    """
    Status of a conflict in the system.
    """

    DETECTED = "detected"  # Conflict has been detected
    ANALYZING = "analyzing"  # Conflict is being analyzed
    RESOLVING = "resolving"  # Conflict is being resolved
    RESOLVED = "resolved"  # Conflict has been resolved
    UNRESOLVABLE = "unresolvable"  # Conflict cannot be resolved
    IGNORED = "ignored"  # Conflict has been ignored


class ResolutionStrategy(enum.Enum):
    """
    Strategy for resolving conflicts.
    """

    PRIORITY = "priority"  # Resolve based on priority
    AUTHORITY = "authority"  # Resolve based on authority
    CONSENSUS = "consensus"  # Resolve based on consensus
    FIRST = "first"  # Resolve in favor of the first entity
    LAST = "last"  # Resolve in favor of the last entity
    MERGE = "merge"  # Merge conflicting entities
    CANCEL = "cancel"  # Cancel conflicting entities
    DELEGATE = "delegate"  # Delegate to a higher authority
    CUSTOM = "custom"  # Use a custom resolution strategy


class Conflict:
    """
    Conflict between entities in the system.

    Conflicts represent situations where multiple entities (agents, tasks, etc.)
    are in conflict with each other. They have a lifecycle from detection to
    resolution.
    """

    def __init__(
        self,
        conflict_id: str,
        conflict_type: ConflictType,
        entities: List[Dict[str, Any]],
        description: str,
        metadata: Dict[str, Any] = None,
    ):
        """
        Initialize a conflict.

        Args:
            conflict_id: Unique identifier for the conflict
            conflict_type: Type of the conflict
            entities: List of entities involved in the conflict
            description: Description of the conflict
            metadata: Additional metadata for the conflict
        """
        self.conflict_id = conflict_id
        self.conflict_type = conflict_type
        self.entities = entities
        self.description = description
        self.metadata = metadata or {}

        # Conflict lifecycle information
        self.status = ConflictStatus.DETECTED
        self.detected_at = datetime.now()
        self.resolved_at = None

        # Resolution information
        self.resolution_strategy = None
        self.resolution_description = None
        self.resolution_result = None

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the conflict to a dictionary.

        Returns:
            Dictionary representation of the conflict
        """
        return {
            "conflict_id": self.conflict_id,
            "conflict_type": self.conflict_type.value,
            "entities": self.entities,
            "description": self.description,
            "metadata": self.metadata,
            "status": self.status.value,
            "detected_at": self.detected_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_strategy": (
                self.resolution_strategy.value if self.resolution_strategy else None
            ),
            "resolution_description": self.resolution_description,
            "resolution_result": self.resolution_result,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conflict":
        """
        Create a conflict from a dictionary.

        Args:
            data: Dictionary containing conflict data

        Returns:
            Conflict instance
        """
        # Create the conflict with basic information
        conflict = cls(
            conflict_id=data["conflict_id"],
            conflict_type=ConflictType(data["conflict_type"]),
            entities=data["entities"],
            description=data["description"],
            metadata=data.get("metadata", {}),
        )

        # Set conflict lifecycle information
        conflict.status = ConflictStatus(
            data.get("status", ConflictStatus.DETECTED.value)
        )
        conflict.detected_at = datetime.fromisoformat(data["detected_at"])

        if data.get("resolved_at"):
            conflict.resolved_at = datetime.fromisoformat(data["resolved_at"])

        # Set resolution information
        if data.get("resolution_strategy"):
            conflict.resolution_strategy = ResolutionStrategy(
                data["resolution_strategy"]
            )

        conflict.resolution_description = data.get("resolution_description")
        conflict.resolution_result = data.get("resolution_result")

        return conflict

    def update_status(self, status: ConflictStatus) -> None:
        """
        Update the conflict's status.

        Args:
            status: New status of the conflict
        """
        self.status = status

        # Update timestamp if resolved
        if status == ConflictStatus.RESOLVED and not self.resolved_at:
            self.resolved_at = datetime.now()

    def resolve(
        self, strategy: ResolutionStrategy, description: str, result: Any
    ) -> None:
        """
        Resolve the conflict.

        Args:
            strategy: Resolution strategy used
            description: Description of the resolution
            result: Result of the resolution
        """
        self.resolution_strategy = strategy
        self.resolution_description = description
        self.resolution_result = result
        self.update_status(ConflictStatus.RESOLVED)

    def is_resolved(self) -> bool:
        """
        Check if the conflict is resolved.

        Returns:
            True if the conflict is resolved
        """
        return self.status == ConflictStatus.RESOLVED

    def is_unresolvable(self) -> bool:
        """
        Check if the conflict is unresolvable.

        Returns:
            True if the conflict is unresolvable
        """
        return self.status == ConflictStatus.UNRESOLVABLE

    def is_active(self) -> bool:
        """
        Check if the conflict is active.

        Returns:
            True if the conflict is active
        """
        return self.status in (
            ConflictStatus.DETECTED,
            ConflictStatus.ANALYZING,
            ConflictStatus.RESOLVING,
        )

    def __str__(self) -> str:
        """
        Get string representation of the conflict.

        Returns:
            String representation
        """
        return f"Conflict({self.conflict_id}, {self.conflict_type.value}, {self.status.value})"


class ConflictResolver:
    """
    Component for resolving conflicts between entities.

    The ConflictResolver manages conflict detection, classification, and resolution.
    It provides methods for detecting conflicts, analyzing them, and applying
    resolution strategies.
    """

    def __init__(self, resolver_id: str):
        """
        Initialize the conflict resolver.

        Args:
            resolver_id: Unique identifier for this resolver
        """
        self.resolver_id = resolver_id
        self.logger = get_logger(f"coordinator.resolver.{resolver_id}")

        # Create publisher and subscriber for event-based communication
        self.publisher = create_publisher(
            source_id=f"coordinator.resolver.{resolver_id}"
        )
        self.subscriber = create_subscriber(
            subscriber_id=f"coordinator.resolver.{resolver_id}"
        )

        # Initialize conflict registry
        self.conflicts: Dict[str, Conflict] = {}

        # Initialize resolution strategies
        self.resolution_strategies: Dict[ConflictType, ResolutionStrategy] = {}

        # Initialize custom resolution functions
        self.custom_resolvers: Dict[str, Callable] = {}

        # Initialize locks for thread safety
        self.conflict_lock = asyncio.Lock()

        # Initialize subscription IDs
        self.subscription_ids: List[str] = []

        # Set default resolution strategies
        self._set_default_resolution_strategies()

    async def start(self) -> None:
        """
        Start the conflict resolver.

        This method subscribes to conflict-related events.
        """
        # Subscribe to conflict events
        await self._subscribe_to_events()

        self.logger.info(f"Conflict resolver started: {self.resolver_id}")

    async def stop(self) -> None:
        """
        Stop the conflict resolver.

        This method unsubscribes from conflict-related events.
        """
        # Unsubscribe from conflict events
        for subscription_id in self.subscription_ids:
            await self.subscriber.unsubscribe(subscription_id)

        self.subscription_ids = []

        self.logger.info(f"Conflict resolver stopped: {self.resolver_id}")

    def _set_default_resolution_strategies(self) -> None:
        """
        Set default resolution strategies for different conflict types.
        """
        self.resolution_strategies[ConflictType.RESOURCE] = ResolutionStrategy.PRIORITY
        self.resolution_strategies[ConflictType.TASK] = ResolutionStrategy.PRIORITY
        self.resolution_strategies[ConflictType.AGENT] = ResolutionStrategy.AUTHORITY
        self.resolution_strategies[ConflictType.PRIORITY] = ResolutionStrategy.AUTHORITY
        self.resolution_strategies[ConflictType.AUTHORITY] = (
            ResolutionStrategy.AUTHORITY
        )
        self.resolution_strategies[ConflictType.CAPABILITY] = (
            ResolutionStrategy.AUTHORITY
        )
        self.resolution_strategies[ConflictType.DATA] = ResolutionStrategy.LAST
        self.resolution_strategies[ConflictType.OTHER] = ResolutionStrategy.PRIORITY

    async def set_resolution_strategy(
        self, conflict_type: ConflictType, strategy: ResolutionStrategy
    ) -> None:
        """
        Set the resolution strategy for a conflict type.

        Args:
            conflict_type: Type of conflict
            strategy: Resolution strategy to use
        """
        self.resolution_strategies[conflict_type] = strategy

        self.logger.info(
            f"Resolution strategy set: {conflict_type.value} -> {strategy.value}"
        )

    async def register_custom_resolver(
        self, conflict_type: ConflictType, resolver_func: Callable
    ) -> None:
        """
        Register a custom resolver function for a conflict type.

        Args:
            conflict_type: Type of conflict
            resolver_func: Custom resolver function
        """
        self.custom_resolvers[conflict_type.value] = resolver_func

        # Set strategy to CUSTOM for this conflict type
        await self.set_resolution_strategy(conflict_type, ResolutionStrategy.CUSTOM)

        self.logger.info(
            f"Custom resolver registered for conflict type: {conflict_type.value}"
        )

    async def detect_conflict(
        self,
        conflict_type: ConflictType,
        entities: List[Dict[str, Any]],
        description: str,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Detect and register a new conflict.

        Args:
            conflict_type: Type of conflict
            entities: List of entities involved in the conflict
            description: Description of the conflict
            metadata: Additional metadata for the conflict

        Returns:
            ID of the detected conflict

        Raises:
            CoordinationError: If detection fails
        """
        try:
            # Generate a conflict ID
            conflict_id = str(uuid.uuid4())

            # Create the conflict
            conflict = Conflict(
                conflict_id=conflict_id,
                conflict_type=conflict_type,
                entities=entities,
                description=description,
                metadata=metadata,
            )

            # Store the conflict
            async with self.conflict_lock:
                self.conflicts[conflict_id] = conflict

            # Publish conflict detected event
            await self._publish_conflict_detected_event(conflict)

            self.logger.info(
                f"Conflict detected: {conflict_id} ({conflict_type.value})"
            )

            return conflict_id
        except Exception as e:
            error_msg = f"Failed to detect conflict: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def get_conflict(self, conflict_id: str) -> Optional[Conflict]:
        """
        Get a conflict by ID.

        Args:
            conflict_id: ID of the conflict

        Returns:
            Conflict, or None if not found

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.conflict_lock:
                return self.conflicts.get(conflict_id)
        except Exception as e:
            error_msg = f"Failed to get conflict {conflict_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def get_active_conflicts(self) -> List[Conflict]:
        """
        Get all active conflicts.

        Returns:
            List of active conflicts

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.conflict_lock:
                return [
                    conflict
                    for conflict in self.conflicts.values()
                    if conflict.is_active()
                ]
        except Exception as e:
            error_msg = f"Failed to get active conflicts: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def get_conflicts_by_type(
        self, conflict_type: ConflictType
    ) -> List[Conflict]:
        """
        Get conflicts by type.

        Args:
            conflict_type: Type of conflicts to get

        Returns:
            List of conflicts of the specified type

        Raises:
            CoordinationError: If the retrieval fails
        """
        try:
            async with self.conflict_lock:
                return [
                    conflict
                    for conflict in self.conflicts.values()
                    if conflict.conflict_type == conflict_type
                ]
        except Exception as e:
            error_msg = (
                f"Failed to get conflicts by type {conflict_type.value}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def resolve_conflict(
        self,
        conflict_id: str,
        strategy: Optional[ResolutionStrategy] = None,
        resolution_params: Dict[str, Any] = None,
    ) -> bool:
        """
        Resolve a conflict.

        Args:
            conflict_id: ID of the conflict
            strategy: Resolution strategy to use, or None to use the default
            resolution_params: Parameters for the resolution strategy

        Returns:
            True if resolution was successful

        Raises:
            CoordinationError: If resolution fails
        """
        try:
            # Get the conflict
            conflict = await self.get_conflict(conflict_id)
            if not conflict:
                self.logger.warning(f"Conflict not found for resolution: {conflict_id}")
                return False

            # Skip if the conflict is already resolved
            if not conflict.is_active():
                self.logger.warning(
                    f"Cannot resolve conflict {conflict_id} with status {conflict.status.value}"
                )
                return False

            # Update conflict status to resolving
            conflict.update_status(ConflictStatus.RESOLVING)

            # Get the resolution strategy
            if strategy is None:
                strategy = self.resolution_strategies.get(
                    conflict.conflict_type,
                    ResolutionStrategy.PRIORITY,  # Default strategy
                )

            # Apply the resolution strategy
            resolution_params = resolution_params or {}
            resolution_result = await self._apply_resolution_strategy(
                conflict, strategy, resolution_params
            )

            # Update conflict with resolution information
            conflict.resolve(
                strategy=strategy,
                description=f"Resolved using {strategy.value} strategy",
                result=resolution_result,
            )

            # Publish conflict resolved event
            await self._publish_conflict_resolved_event(conflict)

            self.logger.info(
                f"Conflict resolved: {conflict_id} using {strategy.value} strategy"
            )

            return True
        except Exception as e:
            error_msg = f"Failed to resolve conflict {conflict_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def mark_conflict_unresolvable(self, conflict_id: str, reason: str) -> bool:
        """
        Mark a conflict as unresolvable.

        Args:
            conflict_id: ID of the conflict
            reason: Reason why the conflict is unresolvable

        Returns:
            True if the operation was successful

        Raises:
            CoordinationError: If the operation fails
        """
        try:
            # Get the conflict
            conflict = await self.get_conflict(conflict_id)
            if not conflict:
                self.logger.warning(f"Conflict not found: {conflict_id}")
                return False

            # Skip if the conflict is already resolved or unresolvable
            if not conflict.is_active():
                self.logger.warning(
                    f"Cannot mark conflict {conflict_id} with status {conflict.status.value}"
                )
                return False

            # Update conflict status
            conflict.update_status(ConflictStatus.UNRESOLVABLE)

            # Update conflict metadata
            conflict.metadata["unresolvable_reason"] = reason

            # Publish conflict unresolvable event
            await self._publish_conflict_unresolvable_event(conflict)

            self.logger.info(
                f"Conflict marked as unresolvable: {conflict_id} - {reason}"
            )

            return True
        except Exception as e:
            error_msg = (
                f"Failed to mark conflict as unresolvable {conflict_id}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def ignore_conflict(self, conflict_id: str, reason: str) -> bool:
        """
        Ignore a conflict.

        Args:
            conflict_id: ID of the conflict
            reason: Reason why the conflict is being ignored

        Returns:
            True if the operation was successful

        Raises:
            CoordinationError: If the operation fails
        """
        try:
            # Get the conflict
            conflict = await self.get_conflict(conflict_id)
            if not conflict:
                self.logger.warning(f"Conflict not found: {conflict_id}")
                return False

            # Skip if the conflict is already resolved or ignored
            if not conflict.is_active():
                self.logger.warning(
                    f"Cannot ignore conflict {conflict_id} with status {conflict.status.value}"
                )
                return False

            # Update conflict status
            conflict.update_status(ConflictStatus.IGNORED)

            # Update conflict metadata
            conflict.metadata["ignore_reason"] = reason

            # Publish conflict ignored event
            await self._publish_conflict_ignored_event(conflict)

            self.logger.info(f"Conflict ignored: {conflict_id} - {reason}")

            return True
        except Exception as e:
            error_msg = f"Failed to ignore conflict {conflict_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def _apply_resolution_strategy(
        self, conflict: Conflict, strategy: ResolutionStrategy, params: Dict[str, Any]
    ) -> Any:
        """
        Apply a resolution strategy to a conflict.

        Args:
            conflict: The conflict to resolve
            strategy: The resolution strategy to apply
            params: Parameters for the resolution strategy

        Returns:
            Result of the resolution

        Raises:
            CoordinationError: If the resolution fails
        """
        try:
            if strategy == ResolutionStrategy.PRIORITY:
                # Resolve based on priority
                # Find the entity with the highest priority
                entities = conflict.entities
                if not entities:
                    raise CoordinationError(
                        "No entities to resolve",
                        cause=ValueError("Empty entities list"),
                    )

                # Get priority field name from params or use default
                priority_field = params.get("priority_field", "priority")

                # Sort entities by priority (higher values first)
                sorted_entities = sorted(
                    entities, key=lambda e: e.get(priority_field, 0), reverse=True
                )

                # Return the highest priority entity
                return sorted_entities[0]

            elif strategy == ResolutionStrategy.AUTHORITY:
                # Resolve based on authority
                # Find the entity with the highest authority
                entities = conflict.entities
                if not entities:
                    raise CoordinationError(
                        "No entities to resolve",
                        cause=ValueError("Empty entities list"),
                    )

                # Get authority field name from params or use default
                authority_field = params.get("authority_field", "authority")

                # Sort entities by authority (higher values first)
                sorted_entities = sorted(
                    entities, key=lambda e: e.get(authority_field, 0), reverse=True
                )

                # Return the highest authority entity
                return sorted_entities[0]

            elif strategy == ResolutionStrategy.CONSENSUS:
                # Resolve based on consensus
                # Find the most common value
                entities = conflict.entities
                if not entities:
                    raise CoordinationError(
                        "No entities to resolve",
                        cause=ValueError("Empty entities list"),
                    )

                # Get value field name from params or use default
                value_field = params.get("value_field", "value")

                # Count occurrences of each value
                value_counts = {}
                for entity in entities:
                    value = entity.get(value_field)
                    if value is not None:
                        value_str = str(value)  # Convert to string for counting
                        if value_str not in value_counts:
                            value_counts[value_str] = 0
                        value_counts[value_str] += 1

                if not value_counts:
                    raise CoordinationError(
                        f"No values found in field '{value_field}'",
                        cause=ValueError(f"No values in field '{value_field}'"),
                    )

                # Find the most common value
                most_common_value = max(value_counts.items(), key=lambda x: x[1])[0]

                # Return the most common value
                return most_common_value

            elif strategy == ResolutionStrategy.FIRST:
                # Resolve in favor of the first entity
                entities = conflict.entities
                if not entities:
                    raise CoordinationError(
                        "No entities to resolve",
                        cause=ValueError("Empty entities list"),
                    )

                # Return the first entity
                return entities[0]

            elif strategy == ResolutionStrategy.LAST:
                # Resolve in favor of the last entity
                entities = conflict.entities
                if not entities:
                    raise CoordinationError(
                        "No entities to resolve",
                        cause=ValueError("Empty entities list"),
                    )

                # Return the last entity
                return entities[-1]

            elif strategy == ResolutionStrategy.MERGE:
                # Merge conflicting entities
                entities = conflict.entities
                if not entities:
                    raise CoordinationError(
                        "No entities to resolve",
                        cause=ValueError("Empty entities list"),
                    )

                # Get merge fields from params or use all fields
                merge_fields = params.get("merge_fields")

                # Create a merged entity
                merged_entity = {}

                # If merge fields are specified, only merge those fields
                if merge_fields:
                    for field in merge_fields:
                        # Use the last non-None value for each field
                        for entity in reversed(entities):
                            if field in entity and entity[field] is not None:
                                merged_entity[field] = entity[field]
                                break
                else:
                    # Merge all fields from all entities
                    # Later entities override earlier ones
                    for entity in entities:
                        merged_entity.update(entity)

                # Return the merged entity
                return merged_entity

            elif strategy == ResolutionStrategy.CANCEL:
                # Cancel conflicting entities
                # This strategy doesn't produce a result
                # It's expected that the caller will handle the cancellation
                return None

            elif strategy == ResolutionStrategy.DELEGATE:
                # Delegate to a higher authority
                # This strategy doesn't produce a result
                # It's expected that the caller will handle the delegation
                return None

            elif strategy == ResolutionStrategy.CUSTOM:
                # Use a custom resolution strategy
                custom_resolver = self.custom_resolvers.get(
                    conflict.conflict_type.value
                )
                if not custom_resolver:
                    raise CoordinationError(
                        f"Custom resolver not found for conflict type {conflict.conflict_type.value}",
                        cause=ValueError(
                            f"No custom resolver for {conflict.conflict_type.value}"
                        ),
                    )

                # Call the custom resolver
                return await custom_resolver(conflict, params)

            else:
                raise CoordinationError(
                    f"Unknown resolution strategy: {strategy}",
                    cause=ValueError(f"Unknown strategy: {strategy}"),
                )
        except CoordinationError:
            # Re-raise coordination errors
            raise
        except Exception as e:
            error_msg = (
                f"Failed to apply resolution strategy {strategy.value}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise CoordinationError(error_msg, cause=e)

    async def _subscribe_to_events(self) -> None:
        """
        Subscribe to conflict-related events.

        This method sets up subscriptions for conflict detection,
        resolution, and other conflict-related events.
        """
        # Subscribe to conflict detection events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"conflict_detected"}),
            handler=self._handle_conflict_detected,
        )
        self.subscription_ids.append(subscription_id)

        # Subscribe to conflict resolution events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"conflict_resolution_request"}),
            handler=self._handle_conflict_resolution_request,
        )
        self.subscription_ids.append(subscription_id)

    async def _handle_conflict_detected(self, event: Event) -> None:
        """
        Handle a conflict detected event.

        Args:
            event: The conflict detected event
        """
        try:
            # Extract conflict information from the event
            conflict_type_str = event.data.get("conflict_type")
            entities = event.data.get("entities")
            description = event.data.get("description")
            metadata = event.data.get("metadata")

            if not conflict_type_str or not entities or not description:
                self.logger.warning(
                    "Received conflict detected event with missing data"
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
            await self.detect_conflict(
                conflict_type=conflict_type,
                entities=entities,
                description=description,
                metadata=metadata,
            )
        except Exception as e:
            self.logger.error(
                f"Error handling conflict detected event: {str(e)}", exc_info=True
            )

    async def _handle_conflict_resolution_request(self, event: Event) -> None:
        """
        Handle a conflict resolution request event.

        Args:
            event: The conflict resolution request event
        """
        try:
            # Extract conflict information from the event
            conflict_id = event.data.get("conflict_id")
            strategy_str = event.data.get("strategy")
            resolution_params = event.data.get("resolution_params")

            if not conflict_id:
                self.logger.warning(
                    "Received conflict resolution request without conflict_id"
                )
                return

            # Convert strategy string to enum if provided
            strategy = None
            if strategy_str:
                try:
                    strategy = ResolutionStrategy(strategy_str)
                except ValueError:
                    self.logger.warning(
                        f"Received invalid resolution strategy: {strategy_str}"
                    )
                    return

            # Resolve the conflict
            await self.resolve_conflict(
                conflict_id=conflict_id,
                strategy=strategy,
                resolution_params=resolution_params,
            )
        except Exception as e:
            self.logger.error(
                f"Error handling conflict resolution request: {str(e)}", exc_info=True
            )

    async def _publish_conflict_detected_event(self, conflict: Conflict) -> None:
        """
        Publish a conflict detected event.

        Args:
            conflict: The detected conflict
        """
        await self.publisher.publish_notification(
            notification_name="conflict_detected",
            data={
                "conflict_id": conflict.conflict_id,
                "conflict_type": conflict.conflict_type.value,
                "description": conflict.description,
                "entity_count": len(conflict.entities),
                "detected_at": conflict.detected_at.isoformat(),
            },
        )

    async def _publish_conflict_resolved_event(self, conflict: Conflict) -> None:
        """
        Publish a conflict resolved event.

        Args:
            conflict: The resolved conflict
        """
        await self.publisher.publish_notification(
            notification_name="conflict_resolved",
            data={
                "conflict_id": conflict.conflict_id,
                "conflict_type": conflict.conflict_type.value,
                "resolution_strategy": conflict.resolution_strategy.value,
                "description": conflict.resolution_description,
                "resolved_at": (
                    conflict.resolved_at.isoformat() if conflict.resolved_at else None
                ),
            },
        )

    async def _publish_conflict_unresolvable_event(self, conflict: Conflict) -> None:
        """
        Publish a conflict unresolvable event.

        Args:
            conflict: The unresolvable conflict
        """
        await self.publisher.publish_notification(
            notification_name="conflict_unresolvable",
            data={
                "conflict_id": conflict.conflict_id,
                "conflict_type": conflict.conflict_type.value,
                "reason": conflict.metadata.get(
                    "unresolvable_reason", "Unknown reason"
                ),
            },
        )

    async def _publish_conflict_ignored_event(self, conflict: Conflict) -> None:
        """
        Publish a conflict ignored event.

        Args:
            conflict: The ignored conflict
        """
        await self.publisher.publish_notification(
            notification_name="conflict_ignored",
            data={
                "conflict_id": conflict.conflict_id,
                "conflict_type": conflict.conflict_type.value,
                "reason": conflict.metadata.get("ignore_reason", "Unknown reason"),
            },
        )
