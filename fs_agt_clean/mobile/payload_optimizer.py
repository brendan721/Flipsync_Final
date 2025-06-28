"""
Mobile payload optimization for efficient data transfer and processing.
Implements chunked data transfer and progressive loading for mobile clients.
"""

import json
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional, TypedDict, Union

from .battery_optimizer import BatteryOptimizer, PowerMode, PowerProfile


@dataclass
class ChunkConfig:
    """Configuration for chunked data transfer."""

    chunk_size: int = 1024 * 16  # 16KB default chunk size
    compression_level: int = 6  # Medium compression
    priority_fields: Optional[List[str]] = None  # Fields to prioritize in first chunk


@dataclass
class DeltaState:
    """Tracks state for delta updates."""

    last_modified: datetime = field(default_factory=datetime.now)
    previous_state: Dict[str, Any] = field(default_factory=dict)
    known_fields: set[str] = field(default_factory=set)


class ChunkResponse(TypedDict):
    """Type definition for chunk response."""

    type: str
    chunk_number: int
    total_chunks: int
    data: Dict[str, Any]
    compressed_size: int
    compression_ratio: float


class DeltaResponse(TypedDict):
    """Type definition for delta response."""

    type: str
    timestamp: str
    changes: Dict[str, Any]
    removed: List[str]
    added: List[str]


class MobilePayloadOptimizer:
    """Handles mobile-optimized payload processing with chunked transfer support."""

    def __init__(
        self,
        config: Optional[ChunkConfig] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
    ):
        self.config = config or ChunkConfig()
        self._compression_cache: Dict[str, bytes] = {}
        self._delta_state = DeltaState()
        self._battery_optimizer = battery_optimizer or BatteryOptimizer()

        # Register for power mode changes
        self._battery_optimizer.register_callback(
            "mode_change", self._handle_power_mode_change
        )

    def _handle_power_mode_change(self, mode: PowerMode, profile: PowerProfile) -> None:
        """Handle power mode changes by adjusting optimization parameters."""
        # Update chunk size based on power mode
        if mode == PowerMode.PERFORMANCE:
            self.config.chunk_size = 1024 * 32  # 32KB chunks
        elif mode == PowerMode.BALANCED:
            self.config.chunk_size = 1024 * 16  # 16KB chunks
        elif mode == PowerMode.POWER_SAVER:
            self.config.chunk_size = 1024 * 8  # 8KB chunks
        else:  # CRITICAL
            self.config.chunk_size = 1024 * 4  # 4KB chunks

        # Update compression level
        self.config.compression_level = profile.compression_level

        # Clear compression cache on mode change
        self._compression_cache.clear()

    async def optimize_payload(
        self, data: Dict[str, Any], mode: str = "delta"
    ) -> Union[DeltaResponse, AsyncIterator[ChunkResponse]]:
        """
        Optimize payload for mobile transfer.

        Args:
            data: The data to optimize
            mode: Either "delta" for incremental updates or "progressive" for chunked streaming

        Returns:
            Either a delta update dict or an async iterator of chunks
        """
        # Check if operation should be deferred
        if self._battery_optimizer.should_defer_operation("payload_optimization", 0.6):
            # Return minimal payload in critical mode
            if mode == "delta":
                return await self._create_minimal_delta(data)
            return self._create_minimal_stream(data)

        # Normal operation
        if mode == "delta":
            return await self._create_delta_update(data)
        return self._create_progressive_stream(data)

    async def _create_minimal_delta(self, data: Dict[str, Any]) -> DeltaResponse:
        """Create a minimal delta update for critical power mode."""
        delta: DeltaResponse = {
            "type": "delta",
            "timestamp": datetime.now().isoformat(),
            "changes": {},
            "removed": [],
            "added": [],
        }

        # Only include critical fields
        critical_fields = {"status", "error", "critical_update"}
        current_fields = set(data.keys())

        for field in current_fields & critical_fields:
            if (
                field not in self._delta_state.previous_state
                or data[field] != self._delta_state.previous_state[field]
            ):
                delta["changes"][field] = data[field]

        # Update state with only critical fields
        self._delta_state.previous_state = {
            k: v for k, v in data.items() if k in critical_fields
        }
        self._delta_state.known_fields = current_fields & critical_fields
        self._delta_state.last_modified = datetime.now()

        return delta

    async def _create_minimal_stream(
        self, data: Dict[str, Any]
    ) -> AsyncIterator[ChunkResponse]:
        """Create a minimal progressive stream for critical power mode."""
        # Only include critical fields
        critical_data = {
            k: v for k, v in data.items() if k in {"status", "error", "critical_update"}
        }

        if not critical_data:
            critical_data = {"status": "minimal"}

        compressed = await self.compress_chunk(critical_data)
        yield ChunkResponse(
            type="chunk",
            chunk_number=0,
            total_chunks=1,
            data=critical_data,
            compressed_size=len(compressed),
            compression_ratio=len(json.dumps(critical_data).encode()) / len(compressed),
        )

    async def _create_delta_update(self, data: Dict[str, Any]) -> DeltaResponse:
        """Create a delta update for incremental state changes."""
        delta: DeltaResponse = {
            "type": "delta",
            "timestamp": datetime.now().isoformat(),
            "changes": {},
            "removed": [],
            "added": [],
        }

        # Track new fields
        current_fields = set(data.keys())
        new_fields = current_fields - self._delta_state.known_fields
        removed_fields = self._delta_state.known_fields - current_fields

        # Handle new fields
        if new_fields:
            delta["added"] = list(new_fields)
            for field in new_fields:
                delta["changes"][field] = data[field]

        # Handle removed fields
        if removed_fields:
            delta["removed"] = list(removed_fields)

        # Calculate changes in existing fields
        for field in self._delta_state.known_fields & current_fields:
            if field in self._delta_state.previous_state:
                if data[field] != self._delta_state.previous_state[field]:
                    delta["changes"][field] = data[field]

        # Update state
        self._delta_state.previous_state = data.copy()
        self._delta_state.known_fields = current_fields
        self._delta_state.last_modified = datetime.now()

        return delta

    async def _create_progressive_stream(
        self, data: Dict[str, Any]
    ) -> AsyncIterator[ChunkResponse]:
        """Create a progressive stream of chunked data."""
        chunks = self._chunk_data(data)
        for chunk_num, chunk in enumerate(chunks):
            compressed = await self.compress_chunk(chunk)
            yield ChunkResponse(
                type="chunk",
                chunk_number=chunk_num,
                total_chunks=len(chunks),
                data=chunk,
                compressed_size=len(compressed),
                compression_ratio=len(json.dumps(chunk).encode()) / len(compressed),
            )

    def _chunk_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split data into optimized chunks."""
        serialized = json.dumps(data)
        chunks: List[Dict[str, Any]] = []

        # First chunk: Priority fields if specified
        if self.config.priority_fields:
            priority_data = {
                k: data[k] for k in self.config.priority_fields if k in data
            }
            chunks.append(priority_data)

            # Remove priority fields from main data
            for field in self.config.priority_fields:
                data.pop(field, None)
            serialized = json.dumps(data)

        # Split remaining data into chunks
        chunk_data = {}
        for i in range(0, len(serialized), self.config.chunk_size):
            chunk = serialized[i : i + self.config.chunk_size]
            try:
                chunk_data = json.loads(chunk) if i == 0 else {"partial": chunk}
            except json.JSONDecodeError:
                chunk_data = {"partial": chunk}
            chunks.append(chunk_data)

        return chunks

    async def compress_chunk(self, chunk: Dict[str, Any]) -> bytes:
        """Compress a chunk for efficient transfer."""
        chunk_key = json.dumps(chunk, sort_keys=True)

        if chunk_key in self._compression_cache:
            return self._compression_cache[chunk_key]

        try:
            serialized = json.dumps(chunk).encode()
            compressed = zlib.compress(serialized, level=self.config.compression_level)

            # Only cache if compression is beneficial
            if len(compressed) < len(serialized):
                self._compression_cache[chunk_key] = compressed
                return compressed
            return serialized

        except Exception:
            # Fallback to uncompressed on error
            return json.dumps(chunk).encode()

    @staticmethod
    async def validate_chunk(chunk: Union[ChunkResponse, Dict[str, Any]]) -> bool:
        """Validate chunk integrity."""
        try:
            required_fields = ["type", "chunk_number", "total_chunks", "data"]
            return all(field in chunk for field in required_fields)
        except Exception:
            return False

    def reset_delta_state(self) -> None:
        """Reset the delta state tracking."""
        self._delta_state = DeltaState()

    def clear_compression_cache(self) -> None:
        """Clear the compression cache."""
        self._compression_cache = {}
