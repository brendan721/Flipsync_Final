"""
Mobile battery optimization system for managing power consumption.
Implements adaptive learning rates and power-saving modes based on battery state.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, TypedDict


class PowerMode(Enum):
    """Available power modes for battery optimization."""

    PERFORMANCE = "performance"  # Maximum performance, no power saving
    BALANCED = "balanced"  # Balance between performance and power saving
    POWER_SAVER = "power_saver"  # Maximum power saving
    CRITICAL = "critical"  # Critical battery level, minimal functionality


@dataclass
class BatteryMetrics:
    """Metrics for tracking battery usage."""

    level: float  # Current battery level (0-100)
    charging: bool  # Whether device is charging
    temperature: float  # Battery temperature
    voltage: float  # Current voltage
    current_draw: float  # Current power draw in mA
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PowerProfile:
    """Power consumption profile for different operations."""

    learning_rate: float  # Learning rate adjustment (0-1)
    sync_interval: int  # Sync interval in seconds
    batch_size: int  # Batch size for operations
    compression_level: int  # Compression level (0-9)
    cache_size: int  # Cache size in KB
    prefetch_enabled: bool  # Whether prefetching is enabled


class BatteryOptimizer:
    """Manages battery optimization and power profiles."""

    def __init__(self) -> None:
        self._current_mode = PowerMode.BALANCED
        self._power_profiles: Dict[PowerMode, PowerProfile] = {
            PowerMode.PERFORMANCE: PowerProfile(
                learning_rate=1.0,
                sync_interval=30,
                batch_size=100,
                compression_level=1,
                cache_size=1024 * 100,  # 100MB
                prefetch_enabled=True,
            ),
            PowerMode.BALANCED: PowerProfile(
                learning_rate=0.7,
                sync_interval=60,
                batch_size=50,
                compression_level=6,
                cache_size=1024 * 50,  # 50MB
                prefetch_enabled=True,
            ),
            PowerMode.POWER_SAVER: PowerProfile(
                learning_rate=0.3,
                sync_interval=300,
                batch_size=20,
                compression_level=9,
                cache_size=1024 * 10,  # 10MB
                prefetch_enabled=False,
            ),
            PowerMode.CRITICAL: PowerProfile(
                learning_rate=0.1,
                sync_interval=900,
                batch_size=5,
                compression_level=9,
                cache_size=1024 * 1,  # 1MB
                prefetch_enabled=False,
            ),
        }
        self._mode_thresholds = {
            PowerMode.PERFORMANCE: 80.0,  # Above 80%
            PowerMode.BALANCED: 40.0,  # 40-80%
            PowerMode.POWER_SAVER: 15.0,  # 15-40%
            PowerMode.CRITICAL: 0.0,  # Below 15%
        }
        self._callbacks: Dict[str, List[Callable[[PowerMode, PowerProfile], None]]] = {}

    async def update_battery_metrics(self, metrics: BatteryMetrics) -> None:
        """Update battery metrics and adjust power mode if needed."""
        new_mode = self._determine_power_mode(metrics)
        if new_mode != self._current_mode:
            await self._switch_power_mode(new_mode)

    def _determine_power_mode(self, metrics: BatteryMetrics) -> PowerMode:
        """Determine appropriate power mode based on battery metrics."""
        if metrics.charging:
            return PowerMode.PERFORMANCE

        for mode, threshold in sorted(
            self._mode_thresholds.items(), key=lambda x: x[1], reverse=True
        ):
            if metrics.level >= threshold:
                return mode

        return PowerMode.CRITICAL

    async def _switch_power_mode(self, new_mode: PowerMode) -> None:
        """Switch to a new power mode and notify subscribers."""
        old_mode = self._current_mode
        self._current_mode = new_mode

        profile = self._power_profiles[new_mode]
        await self._notify_subscribers("mode_change", new_mode, profile)

    def get_current_profile(self) -> PowerProfile:
        """Get the current power profile."""
        return self._power_profiles[self._current_mode]

    def register_callback(
        self, event: str, callback: Callable[[PowerMode, PowerProfile], None]
    ) -> None:
        """Register a callback for power mode changes."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    async def _notify_subscribers(
        self, event: str, mode: PowerMode, profile: PowerProfile
    ) -> None:
        """Notify subscribers of power mode changes."""
        if event in self._callbacks:
            for callback in self._callbacks[event]:
                callback(mode, profile)

    def customize_profile(
        self,
        mode: PowerMode,
        learning_rate: Optional[float] = None,
        sync_interval: Optional[int] = None,
        batch_size: Optional[int] = None,
        compression_level: Optional[int] = None,
        cache_size: Optional[int] = None,
        prefetch_enabled: Optional[bool] = None,
    ) -> None:
        """Customize a power profile for a specific mode."""
        profile = self._power_profiles[mode]

        if learning_rate is not None:
            profile.learning_rate = max(0.0, min(1.0, learning_rate))
        if sync_interval is not None:
            profile.sync_interval = max(30, sync_interval)
        if batch_size is not None:
            profile.batch_size = max(1, batch_size)
        if compression_level is not None:
            profile.compression_level = max(0, min(9, compression_level))
        if cache_size is not None:
            profile.cache_size = max(1024, cache_size)  # Minimum 1MB
        if prefetch_enabled is not None:
            profile.prefetch_enabled = prefetch_enabled

    def set_mode_threshold(self, mode: PowerMode, threshold: float) -> None:
        """Set the battery level threshold for a power mode."""
        self._mode_thresholds[mode] = max(0.0, min(100.0, threshold))

    async def optimize_operation(self, operation_type: str, base_cost: float) -> float:
        """
        Optimize an operation's resource usage based on current power mode.

        Args:
            operation_type: Type of operation (e.g., "learning", "sync", "processing")
            base_cost: Base power cost of the operation

        Returns:
            Adjusted cost based on current power profile
        """
        profile = self.get_current_profile()

        if operation_type == "learning":
            return base_cost * profile.learning_rate
        elif operation_type == "sync":
            return base_cost * (30 / profile.sync_interval)
        elif operation_type == "processing":
            return base_cost * (profile.batch_size / 100)

        return base_cost  # Default no optimization

    def should_defer_operation(self, operation_type: str, importance: float) -> bool:
        """Determine whether an operation should be deferred.

        Args:
            operation_type: Type of operation
            importance: Importance of the operation (0-1)

        Returns:
            Whether the operation should be deferred
        """
        if self._current_mode == PowerMode.CRITICAL:
            return bool(importance < 0.8)  # Only critical operations
        elif self._current_mode == PowerMode.POWER_SAVER:
            return importance < 0.5  # Important operations only
        elif self._current_mode == PowerMode.BALANCED:
            return importance < 0.2  # Most operations proceed

        return False  # Performance mode - no deferral
