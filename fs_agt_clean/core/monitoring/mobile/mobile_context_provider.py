"""
Mobile context provider for FlipSync.

This module provides mobile context awareness for the monitoring system, including:
- Device state monitoring (battery, network, memory)
- Adaptive logging based on device context
- Network-aware metrics collection
- Offline support with synchronization

It enables the monitoring system to adapt to mobile device conditions,
supporting FlipSync's vision of a mobile-first approach.
"""

import asyncio
import json
import logging
import os
import threading
import time
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.monitoring.logger import (
    LogManager,
    get_log_manager,
    get_logger,
)
from fs_agt_clean.core.monitoring.models import (
    BatteryState,
    MobileContext,
    NetworkType,
)


class MobileContextProvider:
    """
    Provides mobile context awareness for the monitoring system.

    This class monitors mobile device state and provides context information
    that allows the monitoring system to adapt to different conditions, including:
    - Battery level and state
    - Network type and signal strength
    - Memory and storage usage
    - Device mode (low power, airplane)

    It supports FlipSync's vision of a mobile-first approach by enabling
    adaptive behavior based on device conditions.
    """

    _instance = None
    _lock = threading.RLock()
    _initialized = False
    _context_history: List[MobileContext] = []
    _max_history_size = 100

    def __new__(cls, *args, **kwargs):
        """Create a singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MobileContextProvider, cls).__new__(cls)
            return cls._instance

    def __init__(
        self,
        storage_path: Optional[Union[str, Path]] = None,
        update_interval: float = 60.0,
        enable_battery_optimization: bool = True,
        enable_network_optimization: bool = True,
        offline_support: bool = True,
    ):
        """
        Initialize the mobile context provider.

        Args:
            storage_path: Path to store context data
            update_interval: Interval between context updates in seconds
            enable_battery_optimization: Whether to enable battery optimizations
            enable_network_optimization: Whether to enable network optimizations
            offline_support: Whether to enable offline support
        """
        with self._lock:
            if self._initialized:
                return

            # Set up logger
            self.logger = get_logger("mobile_context")

            # Set up storage
            self.storage_path = (
                Path(storage_path) if storage_path else Path("logs/mobile_context")
            )
            self.storage_path.mkdir(parents=True, exist_ok=True)

            # Store configuration
            self.update_interval = update_interval
            self.enable_battery_optimization = enable_battery_optimization
            self.enable_network_optimization = enable_network_optimization
            self.offline_support = offline_support

            # Initialize current context
            self._current_context = None
            self._offline_queue = []

            # Start background tasks
            self._is_running = True
            self._update_task = asyncio.create_task(self._update_loop())

            self._initialized = True
            self.logger.info("Mobile context provider initialized")

    async def get_current_context(self) -> Optional[MobileContext]:
        """
        Get the current mobile context.

        Returns:
            Current mobile context or None if not available
        """
        if self._current_context is None:
            # Update context if not available
            await self._update_context()

        return self._current_context

    async def get_context_history(
        self, limit: int = 10, device_id: Optional[str] = None
    ) -> List[MobileContext]:
        """
        Get context history.

        Args:
            limit: Maximum number of context entries to return
            device_id: Optional device ID to filter by

        Returns:
            List of context entries
        """
        history = self._context_history.copy()

        # Filter by device ID if provided
        if device_id:
            history = [ctx for ctx in history if ctx.device_id == device_id]

        # Return limited history (most recent first)
        return sorted(history, key=lambda ctx: ctx.timestamp, reverse=True)[:limit]

    async def should_log(
        self, level: int, component: str, size_bytes: Optional[int] = None
    ) -> bool:
        """
        Determine if logging should occur based on mobile context.

        Args:
            level: Log level
            component: Component name
            size_bytes: Optional size of log entry in bytes

        Returns:
            Whether logging should occur
        """
        if not self.enable_battery_optimization:
            return True

        context = await self.get_current_context()
        if not context:
            return True

        # Always log errors and critical messages
        if level >= logging.ERROR:
            return True

        # Check battery state
        if context.battery_state == BatteryState.CRITICAL:
            # Only log errors and critical messages when battery is critical
            return level >= logging.ERROR

        if context.battery_state == BatteryState.LOW:
            # Only log warnings and above when battery is low
            return level >= logging.WARNING

        if context.is_low_power_mode:
            # Only log warnings and above in low power mode
            return level >= logging.WARNING

        # Check size if provided
        if size_bytes and size_bytes > 1024 and context.battery_level < 0.2:
            # Avoid large logs when battery is below 20%
            return False

        # Default to allowing logs
        return True

    async def should_collect_metrics(
        self, category: str, size_bytes: Optional[int] = None
    ) -> bool:
        """
        Determine if metrics should be collected based on mobile context.

        Args:
            category: Metric category
            size_bytes: Optional size of metrics data in bytes

        Returns:
            Whether metrics should be collected
        """
        if not self.enable_battery_optimization:
            return True

        context = await self.get_current_context()
        if not context:
            return True

        # Always collect critical metrics
        if category.lower() in ["critical", "error", "security"]:
            return True

        # Check battery state
        if context.battery_state == BatteryState.CRITICAL:
            # Only collect critical metrics when battery is critical
            return category.lower() in ["critical", "error", "security"]

        if context.battery_state == BatteryState.LOW:
            # Only collect important metrics when battery is low
            return category.lower() in ["critical", "error", "security", "performance"]

        if context.is_low_power_mode:
            # Reduce metrics collection in low power mode
            return category.lower() in ["critical", "error", "security", "performance"]

        # Check size if provided
        if size_bytes and size_bytes > 5120 and context.battery_level < 0.2:
            # Avoid large metric collections when battery is below 20%
            return False

        # Default to allowing metric collection
        return True

    async def should_send_data(self, size_bytes: int, priority: str = "normal") -> bool:
        """
        Determine if data should be sent based on mobile context.

        Args:
            size_bytes: Size of data in bytes
            priority: Priority of data (critical, high, normal, low)

        Returns:
            Whether data should be sent
        """
        if not self.enable_network_optimization:
            return True

        context = await self.get_current_context()
        if not context:
            return True

        # Always send critical data
        if priority.lower() == "critical":
            return True

        # Check network state
        if context.network_type == NetworkType.NONE:
            # Queue data for later if offline support is enabled
            if self.offline_support and priority.lower() != "low":
                self._queue_offline_data(size_bytes, priority)
            return False

        if context.network_type == NetworkType.CELLULAR and size_bytes > 50 * 1024:
            # Avoid sending large data over cellular unless high priority
            return priority.lower() in ["critical", "high"]

        if context.network_type == NetworkType.CELLULAR_2G and size_bytes > 10 * 1024:
            # Very limited data over 2G
            return priority.lower() in ["critical", "high"]

        if context.signal_strength and context.signal_strength < 0.3:
            # Poor signal, limit data unless high priority
            return priority.lower() in ["critical", "high"] or size_bytes < 5 * 1024

        # Default to allowing data transmission
        return True

    async def get_storage_policy(self) -> Dict[str, Any]:
        """
        Get storage policy based on mobile context.

        Returns:
            Storage policy with retention periods and size limits
        """
        context = await self.get_current_context()

        # Default policy
        policy = {
            "log_retention_days": 7,
            "metrics_retention_days": 14,
            "max_log_size_mb": 50,
            "max_metrics_size_mb": 100,
            "compress_logs": True,
            "compress_metrics": True,
        }

        if not context:
            return policy

        # Adjust based on storage usage
        if context.storage_usage:
            if context.storage_usage > 0.9:  # >90% full
                # Severely restrict storage when device is almost full
                policy["log_retention_days"] = 1
                policy["metrics_retention_days"] = 3
                policy["max_log_size_mb"] = 10
                policy["max_metrics_size_mb"] = 20
            elif context.storage_usage > 0.7:  # >70% full
                # Restrict storage when device is getting full
                policy["log_retention_days"] = 3
                policy["metrics_retention_days"] = 7
                policy["max_log_size_mb"] = 25
                policy["max_metrics_size_mb"] = 50

        return policy

    async def _update_loop(self) -> None:
        """Background task for updating mobile context."""
        while self._is_running:
            try:
                # Update context
                await self._update_context()

                # Process offline queue if online
                if (
                    self.offline_support
                    and self._current_context
                    and self._current_context.network_type != NetworkType.NONE
                ):
                    await self._process_offline_queue()

                # Store context
                await self._store_context()
            except Exception as e:
                self.logger.error(f"Error updating mobile context: {e}")

            # Wait for next update interval
            await asyncio.sleep(self.update_interval)

    async def _update_context(self) -> None:
        """Update the current mobile context."""
        try:
            # In a real implementation, this would use platform-specific APIs
            # to get actual device information. For now, we'll use mock data.

            # Generate a device ID (in real implementation, this would be persistent)
            device_id = "mock-device-001"

            # Mock battery information
            battery_level = 0.75  # 75%
            battery_state = BatteryState.NORMAL
            if battery_level < 0.15:
                battery_state = BatteryState.CRITICAL
            elif battery_level < 0.3:
                battery_state = BatteryState.LOW

            # Mock network information
            network_type = NetworkType.WIFI
            signal_strength = 0.8  # 80%

            # Mock memory and storage
            memory_usage = 0.5  # 50%
            storage_usage = 0.6  # 60%

            # Mock device modes
            is_low_power_mode = False
            is_airplane_mode = False

            # Create context
            context = MobileContext(
                device_id=device_id,
                battery_level=battery_level,
                battery_state=battery_state,
                network_type=network_type,
                signal_strength=signal_strength,
                memory_usage=memory_usage,
                storage_usage=storage_usage,
                is_low_power_mode=is_low_power_mode,
                is_airplane_mode=is_airplane_mode,
                timestamp=datetime.now(timezone.utc),
            )

            # Update current context
            self._current_context = context

            # Add to history
            self._context_history.append(context)

            # Trim history if needed
            if len(self._context_history) > self._max_history_size:
                self._context_history = self._context_history[-self._max_history_size :]

            self.logger.debug(
                f"Updated mobile context: battery={battery_level:.0%}, network={network_type.name}"
            )
        except Exception as e:
            self.logger.error(f"Error updating context: {e}")

    async def _store_context(self) -> None:
        """Store context to disk."""
        if not self._current_context:
            return

        try:
            # Create context file
            timestamp = self._current_context.timestamp.strftime("%Y%m%d_%H%M%S")
            context_file = self.storage_path / f"context_{timestamp}.json"

            # Write context to file
            with open(context_file, "w") as f:
                json.dump(self._current_context.to_dict(), f, indent=2)

            # Write latest context
            latest_file = self.storage_path / "latest_context.json"
            with open(latest_file, "w") as f:
                json.dump(self._current_context.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error storing context: {e}")

    def _queue_offline_data(self, size_bytes: int, priority: str) -> None:
        """Queue data for sending when online."""
        if not self.offline_support:
            return

        self._offline_queue.append(
            {
                "size_bytes": size_bytes,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        self.logger.debug(
            f"Queued {size_bytes} bytes of {priority} data for offline sending"
        )

    async def _process_offline_queue(self) -> None:
        """Process the offline data queue."""
        if not self._offline_queue:
            return

        self.logger.info(
            f"Processing offline queue with {len(self._offline_queue)} items"
        )

        # Process queue in priority order
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        sorted_queue = sorted(
            self._offline_queue,
            key=lambda x: priority_order.get(x["priority"].lower(), 999),
        )

        # Process items
        remaining_queue = []
        for item in sorted_queue:
            # Check if we can send this item now
            can_send = await self.should_send_data(
                item["size_bytes"],
                item["priority"],
            )

            if can_send:
                # In a real implementation, this would trigger the actual sending
                self.logger.debug(
                    f"Sending queued data: {item['size_bytes']} bytes, {item['priority']} priority"
                )
            else:
                # Keep in queue
                remaining_queue.append(item)

        # Update queue
        self._offline_queue = remaining_queue

        if remaining_queue:
            self.logger.info(f"{len(remaining_queue)} items remain in offline queue")
        else:
            self.logger.info("Offline queue processed successfully")

    async def close(self) -> None:
        """Close the provider and clean up resources."""
        self._is_running = False
        if hasattr(self, "_update_task") and self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass


# Singleton instance
_mobile_context_provider_instance = None


def get_mobile_context_provider() -> MobileContextProvider:
    """
    Get the mobile context provider instance.

    Returns:
        MobileContextProvider instance
    """
    global _mobile_context_provider_instance
    if _mobile_context_provider_instance is None:
        _mobile_context_provider_instance = MobileContextProvider()
    return _mobile_context_provider_instance


async def get_current_mobile_context() -> Optional[MobileContext]:
    """
    Get the current mobile context.

    Returns:
        Current mobile context or None if not available
    """
    return await get_mobile_context_provider().get_current_context()


async def should_log_in_mobile_context(
    level: int, component: str, size_bytes: Optional[int] = None
) -> bool:
    """
    Determine if logging should occur based on mobile context.

    Args:
        level: Log level
        component: Component name
        size_bytes: Optional size of log entry in bytes

    Returns:
        Whether logging should occur
    """
    return await get_mobile_context_provider().should_log(level, component, size_bytes)


async def should_collect_metrics_in_mobile_context(
    category: str, size_bytes: Optional[int] = None
) -> bool:
    """
    Determine if metrics should be collected based on mobile context.

    Args:
        category: Metric category
        size_bytes: Optional size of metrics data in bytes

    Returns:
        Whether metrics should be collected
    """
    return await get_mobile_context_provider().should_collect_metrics(
        category, size_bytes
    )


async def should_send_data_in_mobile_context(
    size_bytes: int, priority: str = "normal"
) -> bool:
    """
    Determine if data should be sent based on mobile context.

    Args:
        size_bytes: Size of data in bytes
        priority: Priority of data (critical, high, normal, low)

    Returns:
        Whether data should be sent
    """
    return await get_mobile_context_provider().should_send_data(size_bytes, priority)
