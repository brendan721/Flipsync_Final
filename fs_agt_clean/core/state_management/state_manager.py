"""
State Management Module for FlipSync State Management Framework

This module implements state management capabilities for tracking and
managing application state.
"""

import datetime
import json
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached value with expiration."""

    value: Any
    expiry: float  # Expiration timestamp

    @property
    def is_expired(self) -> bool:
        """Check if the cache entry is expired."""
        return time.time() > self.expiry


class StateChangeType(Enum):
    """Types of state changes."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MIGRATE = "migrate"


class StateChange:
    """Represents a change to the application state."""

    def __init__(
        self,
        change_id: Optional[str] = None,
        change_type: StateChangeType = StateChangeType.UPDATE,
        entity_id: str = "",
        entity_type: str = "",
        previous_state: Optional[Dict[str, Any]] = None,
        new_state: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime.datetime] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.change_id = change_id or str(uuid.uuid4())
        self.change_type = change_type
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.previous_state = previous_state or {}
        self.new_state = new_state or {}
        self.timestamp = timestamp or datetime.datetime.now()
        self.user_id = user_id
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert state change to dictionary representation."""
        return {
            "change_id": self.change_id,
            "change_type": self.change_type.value,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StateChange":
        """Create state change from dictionary representation."""
        return cls(
            change_id=data["change_id"],
            change_type=StateChangeType(data["change_type"]),
            entity_id=data["entity_id"],
            entity_type=data["entity_type"],
            previous_state=data["previous_state"],
            new_state=data["new_state"],
            timestamp=datetime.datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            metadata=data.get("metadata", {}),
        )


class StateMigration:
    """Represents a migration between state versions."""

    def __init__(
        self,
        migration_id: Optional[str] = None,
        source_version: str = "",
        target_version: str = "",
        description: str = "",
        migration_function: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        created_at: Optional[datetime.datetime] = None,
    ):
        self.migration_id = migration_id or str(uuid.uuid4())
        self.source_version = source_version
        self.target_version = target_version
        self.description = description
        self.migration_function = migration_function
        self.created_at = created_at or datetime.datetime.now()
        self.applied_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_applied = None
        self.last_success = None
        self.last_failure = None

    def apply(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the migration to a state.

        Args:
            state: State to migrate

        Returns:
            Migrated state
        """
        self.applied_count += 1
        self.last_applied = datetime.datetime.now()

        try:
            if self.migration_function:
                result = self.migration_function(state)
                self.success_count += 1
                self.last_success = self.last_applied
                return result
            else:
                # No migration function, return state unchanged
                self.success_count += 1
                self.last_success = self.last_applied
                return state
        except Exception as e:
            self.failure_count += 1
            self.last_failure = self.last_applied
            logger.error("Migration failed: %s", e)
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert migration to dictionary representation."""
        return {
            "migration_id": self.migration_id,
            "source_version": self.source_version,
            "target_version": self.target_version,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "applied_count": self.applied_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_applied": (
                self.last_applied.isoformat() if self.last_applied else None
            ),
            "last_success": (
                self.last_success.isoformat() if self.last_success else None
            ),
            "last_failure": (
                self.last_failure.isoformat() if self.last_failure else None
            ),
        }


class StateManager:
    """Manages application state and state migrations."""

    def __init__(
        self,
        initial_state: Optional[Dict[str, Any]] = None,
        state_version: str = "1.0.0",
        storage_path: Optional[str] = None,
    ):
        self.state = initial_state or {}
        self.state_version = state_version
        self.storage_path = storage_path
        self.changes: List[StateChange] = []
        self.migrations: Dict[str, Dict[str, StateMigration]] = defaultdict(dict)
        self.listeners: Dict[str, List[Callable[[StateChange], None]]] = defaultdict(
            list
        )

    def get_state(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get the current state or state for a specific entity.

        Args:
            entity_id: Optional entity ID to get state for

        Returns:
            Current state or entity-specific state
        """
        if entity_id:
            return self.state.get(entity_id, {})
        return self.state.copy()

    async def set_state(self, entity_id: str, state: Dict[str, Any]) -> bool:
        """
        Set state for a specific entity.

        Args:
            entity_id: Entity ID to set state for
            state: State data to set

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use update_state to maintain consistency with change tracking
            self.update_state(
                updates={entity_id: state},
                entity_id=entity_id,
                entity_type="entity_state",
            )
            return True
        except Exception as e:
            logger.error(f"Error setting state for entity {entity_id}: {e}")
            return False

    async def delete_entity_state(self, entity_id: str) -> bool:
        """
        Delete state for a specific entity.

        Args:
            entity_id: Entity ID to delete state for

        Returns:
            True if successful, False otherwise
        """
        try:
            if entity_id in self.state:
                # Use the existing delete_state method with proper parameters
                self.delete_state(
                    keys=[entity_id], entity_id=entity_id, entity_type="entity_state"
                )
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting state for entity {entity_id}: {e}")
            return False

    async def list_states(self) -> Dict[str, Dict[str, Any]]:
        """
        List all entity states.

        Returns:
            Dictionary of entity states
        """
        try:
            # Return a copy of all states
            return {k: v for k, v in self.state.items() if isinstance(v, dict)}
        except Exception as e:
            logger.error(f"Error listing states: {e}")
            return {}

    def update_state(
        self,
        updates: Dict[str, Any],
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateChange:
        """
        Update the state.

        Args:
            updates: Updates to apply to the state
            entity_id: Optional ID of the entity being updated
            entity_type: Optional type of the entity being updated
            user_id: Optional ID of the user making the update
            metadata: Optional metadata for the update

        Returns:
            State change object
        """
        # Create a copy of the previous state
        previous_state = self.state.copy()

        # Apply updates
        for key, value in updates.items():
            if (
                isinstance(value, dict)
                and key in self.state
                and isinstance(self.state[key], dict)
            ):
                # Merge dictionaries
                self.state[key] = {**self.state[key], **value}
            else:
                # Replace value
                self.state[key] = value

        # Create state change
        change = StateChange(
            change_type=StateChangeType.UPDATE,
            entity_id=entity_id or "",
            entity_type=entity_type or "",
            previous_state=previous_state,
            new_state=self.state.copy(),
            user_id=user_id,
            metadata=metadata,
        )

        # Record change
        self.changes.append(change)

        # Notify listeners
        self._notify_listeners(change)

        # Save state if storage path is provided
        if self.storage_path:
            self._save_state()

        return change

    def delete_state(
        self,
        keys: List[str],
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateChange:
        """
        Delete keys from the state.

        Args:
            keys: Keys to delete
            entity_id: Optional ID of the entity being updated
            entity_type: Optional type of the entity being updated
            user_id: Optional ID of the user making the update
            metadata: Optional metadata for the update

        Returns:
            State change object
        """
        # Create a copy of the previous state
        previous_state = self.state.copy()

        # Delete keys
        for key in keys:
            if key in self.state:
                del self.state[key]

        # Create state change
        change = StateChange(
            change_type=StateChangeType.DELETE,
            entity_id=entity_id or "",
            entity_type=entity_type or "",
            previous_state=previous_state,
            new_state=self.state.copy(),
            user_id=user_id,
            metadata=metadata,
        )

        # Record change
        self.changes.append(change)

        # Notify listeners
        self._notify_listeners(change)

        # Save state if storage path is provided
        if self.storage_path:
            self._save_state()

        return change

    def reset_state(
        self,
        new_state: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> StateChange:
        """
        Reset the state to a new state.

        Args:
            new_state: New state (empty if None)
            user_id: Optional ID of the user making the update
            metadata: Optional metadata for the update

        Returns:
            State change object
        """
        # Create a copy of the previous state
        previous_state = self.state.copy()

        # Reset state
        self.state = new_state or {}

        # Create state change
        change = StateChange(
            change_type=StateChangeType.CREATE,
            previous_state=previous_state,
            new_state=self.state.copy(),
            user_id=user_id,
            metadata=metadata,
        )

        # Record change
        self.changes.append(change)

        # Notify listeners
        self._notify_listeners(change)

        # Save state if storage path is provided
        if self.storage_path:
            self._save_state()

        return change

    def register_migration(
        self,
        source_version: str,
        target_version: str,
        description: str,
        migration_function: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> StateMigration:
        """
        Register a state migration.

        Args:
            source_version: Source state version
            target_version: Target state version
            description: Description of the migration
            migration_function: Function to apply the migration

        Returns:
            Migration object
        """
        migration = StateMigration(
            source_version=source_version,
            target_version=target_version,
            description=description,
            migration_function=migration_function,
        )

        self.migrations[source_version][target_version] = migration
        return migration

    def migrate_state(
        self,
        target_version: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[StateChange]:
        """
        Migrate the state to a target version.

        Args:
            target_version: Target state version
            user_id: Optional ID of the user making the update
            metadata: Optional metadata for the update

        Returns:
            List of state changes
        """
        # Find migration path
        path = self._find_migration_path(self.state_version, target_version)
        if not path:
            raise ValueError(
                f"No migration path from {self.state_version} to {target_version}"
            )

        changes = []
        current_state = self.state.copy()
        current_version = self.state_version

        # Apply migrations
        for next_version in path:
            migration = self.migrations[current_version][next_version]
            previous_state = current_state.copy()

            try:
                # Apply migration
                current_state = migration.apply(current_state)

                # Create state change
                change = StateChange(
                    change_type=StateChangeType.MIGRATE,
                    previous_state=previous_state,
                    new_state=current_state.copy(),
                    user_id=user_id,
                    metadata={
                        **(metadata or {}),
                        "source_version": current_version,
                        "target_version": next_version,
                        "migration_id": migration.migration_id,
                    },
                )

                # Record change
                self.changes.append(change)
                changes.append(change)

                # Update current version
                current_version = next_version

                # Notify listeners
                self._notify_listeners(change)
            except Exception as e:
                logger.error("Migration failed: %s", e)
                raise

        # Update state and version
        self.state = current_state
        self.state_version = target_version

        # Save state if storage path is provided
        if self.storage_path:
            self._save_state()

        return changes

    def add_listener(
        self,
        listener: Callable[[StateChange], None],
        entity_type: Optional[str] = None,
    ) -> None:
        """
        Add a state change listener.

        Args:
            listener: Listener function
            entity_type: Optional entity type to filter changes
        """
        if entity_type:
            self.listeners[entity_type].append(listener)
        else:
            self.listeners["*"].append(listener)

    def remove_listener(
        self,
        listener: Callable[[StateChange], None],
        entity_type: Optional[str] = None,
    ) -> bool:
        """
        Remove a state change listener.

        Args:
            listener: Listener function
            entity_type: Optional entity type to filter changes

        Returns:
            True if the listener was removed, False otherwise
        """
        if entity_type:
            if listener in self.listeners[entity_type]:
                self.listeners[entity_type].remove(listener)
                return True
        else:
            for listeners in self.listeners.values():
                if listener in listeners:
                    listeners.remove(listener)
                    return True
        return False

    def _notify_listeners(self, change: StateChange) -> None:
        """
        Notify listeners of a state change.

        Args:
            change: State change
        """
        # Notify entity-specific listeners
        if change.entity_type:
            for listener in self.listeners[change.entity_type]:
                try:
                    listener(change)
                except Exception as e:
                    logger.error("Error in state change listener: %s", e)

        # Notify global listeners
        for listener in self.listeners["*"]:
            try:
                listener(change)
            except Exception as e:
                logger.error("Error in state change listener: %s", e)

    def _save_state(self) -> None:
        """Save the state to storage."""
        if not self.storage_path:
            return

        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

            # Save state
            with open(self.storage_path, "w") as f:
                json.dump(
                    {
                        "state": self.state,
                        "version": self.state_version,
                        "timestamp": datetime.datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error("Error saving state: %s", e)

    def _load_state(self) -> bool:
        """
        Load the state from storage.

        Returns:
            True if the state was loaded, False otherwise
        """
        if not self.storage_path or not os.path.exists(self.storage_path):
            return False

        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                self.state = data["state"]
                self.state_version = data["version"]
                return True
        except Exception as e:
            logger.error("Error loading state: %s", e)
            return False

    def _find_migration_path(
        self, source_version: str, target_version: str
    ) -> Optional[List[str]]:
        """
        Find a migration path between versions.

        Args:
            source_version: Source version
            target_version: Target version

        Returns:
            List of versions to migrate through, or None if no path exists
        """
        if source_version == target_version:
            return []

        # BFS to find shortest path
        visited = {source_version}
        queue = deque([(source_version, [])])

        while queue:
            current, path = queue.popleft()

            if current not in self.migrations:
                continue

            for next_version in self.migrations[current]:
                if next_version == target_version:
                    return path + [next_version]

                if next_version not in visited:
                    visited.add(next_version)
                    queue.append((next_version, path + [next_version]))

        return None

    def get_history(
        self,
        source_version: Optional[str] = None,
        target_version: Optional[str] = None,
        success_only: bool = False,
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get state change history.

        Args:
            source_version: Optional source version filter
            target_version: Optional target version filter
            success_only: Whether to include only successful changes
            entity_id: Optional entity ID filter
            entity_type: Optional entity type filter
            user_id: Optional user ID filter
            limit: Maximum number of changes to return

        Returns:
            List of state changes
        """
        # Filter changes
        filtered_changes = self.changes

        if source_version or target_version:
            filtered_changes = [
                c
                for c in filtered_changes
                if c.change_type == StateChangeType.MIGRATE
                and (
                    not source_version
                    or c.metadata.get("source_version") == source_version
                )
                and (
                    not target_version
                    or c.metadata.get("target_version") == target_version
                )
            ]

        if entity_id:
            filtered_changes = [c for c in filtered_changes if c.entity_id == entity_id]

        if entity_type:
            filtered_changes = [
                c for c in filtered_changes if c.entity_type == entity_type
            ]

        if user_id:
            filtered_changes = [c for c in filtered_changes if c.user_id == user_id]

        # Sort by timestamp (newest first)
        sorted_changes = sorted(
            filtered_changes, key=lambda c: c.timestamp, reverse=True
        )

        # Apply limit
        limited_changes = sorted_changes[:limit]

        # Convert to dictionaries
        return [c.to_dict() for c in limited_changes]
