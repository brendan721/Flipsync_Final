"""
Mobile state reconciliation system for handling offline state conflicts.
Implements conflict detection, resolution rules, and state recovery.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, TypedDict


class ConflictType(Enum):
    """Types of state conflicts that can occur."""

    VALUE_MISMATCH = "value_mismatch"
    FIELD_DELETED = "field_deleted"
    CONCURRENT_MODIFICATION = "concurrent_modification"
    TYPE_MISMATCH = "type_mismatch"
    STRUCTURAL_CONFLICT = "structural_conflict"


class ResolutionStrategy(Enum):
    """Available strategies for resolving conflicts."""

    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    LAST_WRITE_WINS = "last_write_wins"
    MERGE_FIELDS = "merge_fields"
    KEEP_BOTH = "keep_both"


@dataclass
class StateMetadata:
    """Metadata for tracking state changes."""

    last_modified: datetime = field(default_factory=datetime.now)
    version: int = 0
    sync_marker: str = ""
    modified_fields: Set[str] = field(default_factory=set)
    deleted_fields: Set[str] = field(default_factory=set)


class Conflict(TypedDict):
    """Represents a detected conflict between states."""

    type: ConflictType
    field: str
    server_value: Any
    client_value: Any
    timestamp: str
    resolution_strategy: ResolutionStrategy


@dataclass
class ReconciliationResult:
    """Result of state reconciliation process."""

    resolved_state: Dict[str, Any]
    applied_resolutions: List[Conflict]
    unresolved_conflicts: List[Conflict]
    sync_marker: str
    version: int


class MobileStateReconciler:
    """Handles state reconciliation between client and server states."""

    def __init__(
        self, default_strategy: ResolutionStrategy = ResolutionStrategy.LAST_WRITE_WINS
    ):
        self.default_strategy = default_strategy
        self._field_strategies: Dict[str, ResolutionStrategy] = {}
        self._type_strategies: Dict[type, ResolutionStrategy] = {}

    async def reconcile_states(
        self,
        server_state: Dict[str, Any],
        client_state: Dict[str, Any],
        server_metadata: StateMetadata,
        client_metadata: StateMetadata,
    ) -> ReconciliationResult:
        """
        Reconcile differences between server and client states.

        Args:
            server_state: The current server state
            client_state: The client's local state
            server_metadata: Server state metadata
            client_metadata: Client state metadata

        Returns:
            ReconciliationResult with resolved state and conflict information
        """
        conflicts = await self._detect_conflicts(
            server_state, client_state, server_metadata, client_metadata
        )

        if not conflicts:
            # No conflicts, use newer state
            if server_metadata.last_modified > client_metadata.last_modified:
                final_state = server_state.copy()
            else:
                final_state = client_state.copy()

            return ReconciliationResult(
                resolved_state=final_state,
                applied_resolutions=[],
                unresolved_conflicts=[],
                sync_marker=server_metadata.sync_marker,
                version=server_metadata.version,
            )

        resolved_state = server_state.copy()
        applied_resolutions = []
        unresolved_conflicts = []

        for conflict in conflicts:
            resolution = await self._resolve_conflict(conflict)
            if resolution is not None:
                resolved_state = await self._apply_resolution(
                    resolved_state, resolution
                )
                applied_resolutions.append(resolution)
            else:
                unresolved_conflicts.append(conflict)

        return ReconciliationResult(
            resolved_state=resolved_state,
            applied_resolutions=applied_resolutions,
            unresolved_conflicts=unresolved_conflicts,
            sync_marker=server_metadata.sync_marker,
            version=server_metadata.version + 1,
        )

    async def _detect_conflicts(
        self,
        server_state: Dict[str, Any],
        client_state: Dict[str, Any],
        server_metadata: StateMetadata,
        client_metadata: StateMetadata,
    ) -> List[Conflict]:
        """Detect conflicts between server and client states."""
        conflicts: List[Conflict] = []
        all_fields = set(server_state.keys()) | set(client_state.keys())

        for field in all_fields:
            if field in server_state and field in client_state:
                # Check for value conflicts
                if server_state[field] != client_state[field]:
                    if isinstance(server_state[field], type(client_state[field])):
                        conflict_type = ConflictType.VALUE_MISMATCH
                    else:
                        conflict_type = ConflictType.TYPE_MISMATCH

                    conflicts.append(
                        Conflict(
                            type=conflict_type,
                            field=field,
                            server_value=server_state[field],
                            client_value=client_state[field],
                            timestamp=datetime.now().isoformat(),
                            resolution_strategy=self._get_resolution_strategy(
                                field, server_state[field]
                            ),
                        )
                    )
            elif field in server_state:
                # Field deleted in client
                if field in client_metadata.deleted_fields:
                    conflicts.append(
                        Conflict(
                            type=ConflictType.FIELD_DELETED,
                            field=field,
                            server_value=server_state[field],
                            client_value=None,
                            timestamp=datetime.now().isoformat(),
                            resolution_strategy=self._get_resolution_strategy(
                                field, server_state[field]
                            ),
                        )
                    )
            else:
                # Field deleted in server
                if field in server_metadata.deleted_fields:
                    conflicts.append(
                        Conflict(
                            type=ConflictType.FIELD_DELETED,
                            field=field,
                            server_value=None,
                            client_value=client_state[field],
                            timestamp=datetime.now().isoformat(),
                            resolution_strategy=self._get_resolution_strategy(
                                field, client_state[field]
                            ),
                        )
                    )

        return conflicts

    async def _resolve_conflict(self, conflict: Conflict) -> Optional[Conflict]:
        """Resolve a single conflict using the appropriate strategy."""
        strategy = conflict["resolution_strategy"]

        if strategy == ResolutionStrategy.SERVER_WINS:
            if conflict["server_value"] is not None:
                return conflict
            return None

        elif strategy == ResolutionStrategy.CLIENT_WINS:
            if conflict["client_value"] is not None:
                conflict["server_value"] = conflict["client_value"]
                return conflict
            return None

        elif strategy == ResolutionStrategy.LAST_WRITE_WINS:
            # In this implementation, we're using the server value
            # In a full implementation, we'd compare timestamps
            if conflict["server_value"] is not None:
                return conflict
            return None

        elif strategy == ResolutionStrategy.MERGE_FIELDS:
            if isinstance(conflict["server_value"], dict) and isinstance(
                conflict["client_value"], dict
            ):
                merged = {**conflict["client_value"], **conflict["server_value"]}
                conflict["server_value"] = merged
                return conflict
            return None

        elif strategy == ResolutionStrategy.KEEP_BOTH:
            if conflict["field"].endswith("_conflict"):
                return None

            new_field = f"{conflict['field']}_conflict"
            conflict["field"] = new_field
            return conflict

        return None

    async def _apply_resolution(
        self, state: Dict[str, Any], resolution: Conflict
    ) -> Dict[str, Any]:
        """Apply a resolved conflict to the state."""
        if resolution["type"] == ConflictType.FIELD_DELETED:
            if resolution["server_value"] is None:
                state.pop(resolution["field"], None)
        else:
            state[resolution["field"]] = resolution["server_value"]
        return state

    def _get_resolution_strategy(self, field: str, value: Any) -> ResolutionStrategy:
        """Get the appropriate resolution strategy for a field."""
        if field in self._field_strategies:
            return self._field_strategies[field]

        if type(value) in self._type_strategies:
            return self._type_strategies[type(value)]

        return self.default_strategy

    def set_field_strategy(self, field: str, strategy: ResolutionStrategy) -> None:
        """Set a resolution strategy for a specific field."""
        self._field_strategies[field] = strategy

    def set_type_strategy(self, type_: type, strategy: ResolutionStrategy) -> None:
        """Set a resolution strategy for a specific type."""
        self._type_strategies[type_] = strategy
