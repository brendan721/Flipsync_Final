"""
Mobile Service Coordinator for FlipSync Mobile Application.

This module coordinates between mobile backend services and the Flutter frontend,
providing a unified interface for mobile-specific functionality including:
- Battery optimization and power management
- Update prioritization and sync management
- Mobile-specific agent monitoring
- Cross-platform state reconciliation
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.mobile.battery_optimizer import (
    BatteryMetrics,
    BatteryOptimizer,
    PowerMode,
)
from fs_agt_clean.mobile.models import Account
from fs_agt_clean.mobile.payload_optimizer import MobilePayloadOptimizer
from fs_agt_clean.mobile.state_reconciler import MobileStateReconciler
from fs_agt_clean.mobile.update_prioritizer import (
    MarketUpdatePrioritizer,
    UpdatePriority,
)

logger = logging.getLogger(__name__)


class MobileServiceCoordinator:
    """Coordinates mobile backend services for Flutter frontend integration."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the mobile service coordinator."""
        self.config = config or {}

        # Initialize mobile services
        self.battery_optimizer = BatteryOptimizer()
        self.payload_optimizer = MobilePayloadOptimizer()
        self.state_reconciler = MobileStateReconciler()
        self.update_prioritizer = MarketUpdatePrioritizer(
            battery_optimizer=self.battery_optimizer,
            max_retry_count=self.config.get("max_retry_count", 3),
            expiry_threshold_seconds=self.config.get("expiry_threshold", 3600),
        )

        # Service state
        self.is_initialized = False
        self._sync_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize all mobile services."""
        try:
            logger.info("Initializing mobile service coordinator")

            # Initialize individual services
            await self._initialize_services()

            # Start background tasks
            await self._start_background_tasks()

            self.is_initialized = True
            logger.info("Mobile service coordinator initialized successfully")

        except Exception as e:
            logger.error("Failed to initialize mobile service coordinator: %s", str(e))
            raise

    async def _initialize_services(self) -> None:
        """Initialize individual mobile services."""
        # Battery optimizer is ready to use immediately
        # Payload optimizer is ready to use immediately
        # State reconciler is ready to use immediately
        # Update prioritizer is ready to use immediately
        pass

    async def _start_background_tasks(self) -> None:
        """Start background synchronization tasks."""
        self._sync_task = asyncio.create_task(self._sync_loop())

    async def _sync_loop(self) -> None:
        """Background sync loop for mobile services."""
        while True:
            try:
                await asyncio.sleep(30)  # Sync every 30 seconds

                # Process pending updates
                await self._process_pending_updates()

                # Clean up expired updates
                await self.update_prioritizer.clear_expired_updates_async()

            except Exception as e:
                logger.error("Error in mobile sync loop: %s", str(e))
                await asyncio.sleep(60)  # Wait longer on error

    async def _process_pending_updates(self) -> None:
        """Process pending updates based on priority and battery level."""
        try:
            next_update_id = await self.update_prioritizer.get_next_update()
            if next_update_id:
                update = await self.update_prioritizer.get_update(next_update_id)
                if update:
                    logger.debug("Processing update: %s", next_update_id)
                    # Process the update (implementation depends on update type)
                    self.update_prioritizer.remove_update(next_update_id)
        except Exception as e:
            logger.error("Error processing pending updates: %s", str(e))

    async def update_battery_status(
        self, battery_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update battery status and get optimized power profile."""
        try:
            metrics = BatteryMetrics(
                level=battery_data.get("level", 100.0),
                charging=battery_data.get("charging", False),
                temperature=battery_data.get("temperature", 25.0),
                voltage=battery_data.get("voltage", 3.7),
                current_draw=battery_data.get("current_draw", 0.0),
            )

            await self.battery_optimizer.update_battery_metrics(metrics)
            profile = self.battery_optimizer.get_current_profile()

            return {
                "power_mode": self.battery_optimizer._current_mode.value,
                "learning_rate": profile.learning_rate,
                "sync_interval": profile.sync_interval,
                "batch_size": profile.batch_size,
                "compression_level": profile.compression_level,
                "cache_size": profile.cache_size,
                "prefetch_enabled": profile.prefetch_enabled,
            }

        except Exception as e:
            logger.error("Failed to update battery status: %s", str(e))
            return {"error": str(e)}

    async def add_market_update(
        self,
        update_id: str,
        update_type: str,
        data: Dict[str, Any],
        account_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Add a market update to the prioritization queue."""
        try:
            account = Account(
                id=account_data.get("account_id", "default"),
                email=account_data.get("email", "test@example.com"),
                username=account_data.get("username", ""),
                name=account_data.get("name", ""),
                settings=account_data.get("settings", {}),
            )

            metadata = await self.update_prioritizer.add_update(
                update_id, update_type, data, account
            )

            return {
                "update_id": update_id,
                "priority": metadata.priority.value,
                "battery_cost": metadata.battery_cost,
                "network_cost": metadata.network_cost,
                "expiry": metadata.expiry.isoformat() if metadata.expiry else None,
            }

        except Exception as e:
            logger.error("Failed to add market update: %s", str(e))
            return {"error": str(e)}

    async def get_prioritized_updates(self) -> List[Dict[str, Any]]:
        """Get updates prioritized by importance and battery level."""
        try:
            return await self.update_prioritizer.get_prioritized_updates()
        except Exception as e:
            logger.error("Failed to get prioritized updates: %s", str(e))
            return []

    async def optimize_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize payload for mobile transmission."""
        try:
            # Get current power profile for optimization parameters
            profile = self.battery_optimizer.get_current_profile()

            optimized_result = await self.payload_optimizer.optimize_payload(
                data, mode="delta"
            )

            # Handle delta response
            if (
                isinstance(optimized_result, dict)
                and optimized_result.get("type") == "delta"
            ):
                optimized_data = optimized_result
            else:
                # Handle async iterator case (shouldn't happen with delta mode)
                optimized_data = {"type": "delta", "changes": data}

            return {
                "original_size": len(str(data)),
                "optimized_size": len(str(optimized_data)),
                "compression_ratio": (
                    len(str(optimized_data)) / len(str(data))
                    if len(str(data)) > 0
                    else 1.0
                ),
                "data": optimized_data,
            }

        except Exception as e:
            logger.error("Failed to optimize payload: %s", str(e))
            return {"error": str(e)}

    async def reconcile_state(
        self, local_state: Dict[str, Any], remote_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reconcile local and remote state for offline sync."""
        try:
            # Create metadata for state reconciliation
            from fs_agt_clean.mobile.state_reconciler import StateMetadata

            local_metadata = StateMetadata()
            remote_metadata = StateMetadata()

            result = await self.state_reconciler.reconcile_states(
                remote_state, local_state, remote_metadata, local_metadata
            )
            reconciled_state = result.resolved_state

            return {
                "reconciled_state": reconciled_state,
                "conflicts_resolved": len(reconciled_state.get("conflicts", [])),
                "sync_timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("Failed to reconcile state: %s", str(e))
            return {"error": str(e)}

    async def get_mobile_dashboard_data(self) -> Dict[str, Any]:
        """Get mobile dashboard data for agent monitoring."""
        try:
            # Get current power status
            profile = self.battery_optimizer.get_current_profile()

            # Get pending updates summary
            pending_updates = await self.update_prioritizer.get_pending_updates_async()

            # Get update priority distribution
            priority_counts = {}
            for update in pending_updates.values():
                priority = update.get("priority", "unknown")
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

            return {
                "power_status": {
                    "mode": self.battery_optimizer._current_mode.value,
                    "learning_rate": profile.learning_rate,
                    "sync_interval": profile.sync_interval,
                    "cache_size": profile.cache_size,
                },
                "update_queue": {
                    "total_pending": len(pending_updates),
                    "priority_distribution": priority_counts,
                },
                "service_status": {
                    "battery_optimizer": "active",
                    "update_prioritizer": "active",
                    "payload_optimizer": "active",
                    "state_reconciler": "active",
                },
                "last_updated": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("Failed to get mobile dashboard data: %s", str(e))
            return {"error": str(e)}

    async def cleanup(self) -> None:
        """Clean up mobile services and background tasks."""
        try:
            logger.info("Cleaning up mobile service coordinator")

            # Cancel background tasks
            if self._sync_task:
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass

            # Clear pending updates
            await self.update_prioritizer.clear_pending_updates_async()

            self.is_initialized = False
            logger.info("Mobile service coordinator cleaned up successfully")

        except Exception as e:
            logger.error("Error during mobile service coordinator cleanup: %s", str(e))

    def get_service_status(self) -> Dict[str, Any]:
        """Get current status of all mobile services."""
        return {
            "initialized": self.is_initialized,
            "battery_optimizer": {
                "current_mode": self.battery_optimizer._current_mode.value,
                "profile": {
                    "learning_rate": self.battery_optimizer.get_current_profile().learning_rate,
                    "sync_interval": self.battery_optimizer.get_current_profile().sync_interval,
                },
            },
            "update_prioritizer": {
                "pending_count": len(self.update_prioritizer.pending_updates),
                "max_retries": self.update_prioritizer.max_retry_count,
            },
            "background_tasks": {
                "sync_task_running": self._sync_task is not None
                and not self._sync_task.done()
            },
        }
