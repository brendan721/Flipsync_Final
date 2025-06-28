"""Base market agent module for handling marketplace interactions."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, cast

from fs_agt_clean.core.auth.auth_manager import AuthManager
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.coordination.event_system.event_bus import EventBus
from fs_agt_clean.core.events.base import Event, EventType
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.core.monitoring.metrics.collector import MetricsCollector
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer
from fs_agt_clean.mobile.models import (
    Account,
    AccountStatus,
    ResourceQuota,
    ResourceType,
    ResourceUsage,
    UnifiedUserAccount,
    UnifiedUserRole,
)
from fs_agt_clean.mobile.update_prioritizer import (
    MarketUpdatePrioritizer,
    UpdateMetadata,
    UpdatePriority,
)

logger = logging.getLogger(__name__)


class AccountManager:
    """Manages seller accounts and their resources."""

    def __init__(
        self,
        event_bus: EventBus,
        auth_manager: AuthManager,
        metrics_collector: MetricsCollector,
    ):
        """Initialize account manager.

        Args:
            event_bus: Event bus for communication
            auth_manager: Auth manager for authentication
            metrics_collector: Metrics collector for monitoring
        """
        self.event_bus = event_bus
        self.auth_manager = auth_manager
        self.metrics_collector = metrics_collector
        self.seller_accounts: Dict[str, Account] = {}

    async def create_seller_account(
        self, name: str, initial_user: UnifiedUserAccount
    ) -> Account:
        """Create a new seller account.

        Args:
            name: Seller account name
            initial_user: Initial user account

        Returns:
            Created seller account
        """
        seller = Account(
            id=f"seller_{datetime.now().timestamp()}",
            email=initial_user.email,  # Use initial user's email
            name=name,
            status=AccountStatus.ACTIVE,
            users=[],  # Initialize empty list first
            quotas={
                str(ResourceType.API_CALLS.name): ResourceQuota(
                    resource_type=ResourceType.API_CALLS,
                    limit=1000,
                    used=0,
                    last_updated=datetime.now(),
                    alerts_enabled=True,
                    alert_threshold=0.8,
                ),
            },
            usage_metrics={str(ResourceType.API_CALLS.name): []},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            features_enabled={"basic_features"},
            performance_score=1.0,
        )
        seller.users.append(initial_user)  # Add user after initialization
        self.seller_accounts[seller.id] = seller
        return seller

    async def add_user(self, seller_id: str, email: str, role: UnifiedUserRole) -> UnifiedUserAccount:
        """Add a user to a seller account.

        Args:
            seller_id: Seller account ID
            email: UnifiedUser email
            role: UnifiedUser role

        Returns:
            Created user account
        """
        seller = self.seller_accounts.get(seller_id)
        if not seller:
            error_msg = f"Seller {seller_id} not found"
            await self._publish_error(error_msg)
            raise ValueError(error_msg)

        token_info = await self.auth_manager.generate_tokens(email, [role.name])
        user = UnifiedUserAccount(
            id=f"user_{datetime.now().timestamp()}",
            email=email,
            role=role,
            status=AccountStatus.ACTIVE,
            created_at=datetime.now(),
            last_login=datetime.now(),
            permissions={"basic_access"},
            api_key=token_info.token,
            quota_multiplier=1.0,
        )
        seller.users.append(user)
        return user

    async def update_quotas(
        self, seller_id: str, resource_type: ResourceType, new_limit: int
    ) -> ResourceQuota:
        """Update resource quotas for a seller.

        Args:
            seller_id: Seller account ID
            resource_type: Resource type to update
            new_limit: New resource limit

        Returns:
            Updated resource quota
        """
        seller = self.seller_accounts.get(seller_id)
        if not seller:
            raise ValueError(f"Seller {seller_id} not found")

        quota = seller.quotas.get(resource_type)
        if not quota:
            quota = ResourceQuota(
                resource_type=resource_type,
                limit=new_limit,
                used=0,
                last_updated=datetime.now(),
                alerts_enabled=True,
                alert_threshold=0.8,
            )
            seller.quotas[resource_type] = quota
        else:
            quota.limit = new_limit
            quota.last_updated = datetime.now()

        return quota

    async def track_resource_usage(
        self, seller_id: str, resource_type: ResourceType, amount: int
    ) -> ResourceUsage:
        """Track resource usage for a seller."""
        seller = self.seller_accounts.get(seller_id)
        if not seller:
            error_msg = f"Seller {seller_id} not found"
            await self._publish_error(error_msg)
            raise ValueError(error_msg)

        # Convert ResourceType to string key
        resource_key = str(resource_type.name)
        quota = seller.quotas.get(resource_key)
        if not quota:
            error_msg = f"No quota found for {resource_type}"
            await self._publish_error(error_msg)
            raise ValueError(error_msg)

        usage = ResourceUsage(
            seller_id=seller_id,
            resource_type=resource_type,
            amount=amount,
            timestamp=datetime.now(),
            success=quota.used + amount <= quota.limit,
        )

        if usage.success:
            quota.used += amount
            metrics = seller.usage_metrics.get(resource_key, [])
            metrics.append(usage)
            seller.usage_metrics[resource_key] = metrics

        return usage

    async def _publish_error(self, error_message: str) -> None:
        """Publish error event.

        Args:
            error_message: Error message to publish
        """
        if self.event_bus:
            await self.event_bus.publish(
                Event(
                    id=f"error_{datetime.now().timestamp()}",
                    type=EventType.ERROR_OCCURRED,
                    source="account_manager",
                    data={"error": error_message},
                    timestamp=datetime.now(),
                )
            )


class BaseMarketUnifiedAgent:
    """Base agent for marketplace operations."""

    def __init__(
        self,
        agent_id: str,
        marketplace: str,
        config_manager: ConfigManager,
        alert_manager: AlertManager,
        battery_optimizer: BatteryOptimizer,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.marketplace = marketplace
        self.config_manager = config_manager
        self.alert_manager = alert_manager
        self.config = config or {}
        self.metrics: Dict[str, int | float] = {
            "listings_created": 0,
            "orders_processed": 0,
            "revenue_generated": 0.0,
            "updates_processed": 0,
            "updates_deferred": 0,
        }

        # Initialize update prioritizer
        self.update_prioritizer = MarketUpdatePrioritizer(battery_optimizer)
        self._pending_operations: Set[str] = set()
        self._current_account: Optional[Account] = None

    def _get_required_config_fields(self) -> List[str]:
        """Get required configuration fields"""
        return ["api_key", "marketplace_id", "rate_limit", "timeout"]

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle marketplace events with prioritization."""
        event_type = cast(str, event.get("type"))
        event_id = str(event.get("id", f"event_{datetime.now().timestamp()}"))

        if not self._current_account:
            logger.warning("No account context for event handling")
            return

        try:
            # Add event to prioritization queue
            metadata = await self.update_prioritizer.add_update(
                event_id, event_type, event, self._current_account
            )

            # Process if immediate handling needed
            if metadata.priority in [UpdatePriority.CRITICAL, UpdatePriority.HIGH]:
                await self._process_prioritized_event(event_id, event_type, event)

        except Exception as e:
            logger.error("Error handling event %s: %s", event_id, str(e))
            await self.alert_manager.send_alert(
                f"Event handling error: {str(e)}", severity="ERROR"
            )

    async def _process_prioritized_event(
        self, event_id: str, event_type: str, event_data: Dict[str, Any]
    ) -> None:
        """Process a prioritized event."""
        try:
            if event_type == "listing":
                await self._handle_listing_event(event_data)
                self.metrics["listings_created"] += 1
            elif event_type == "order":
                await self._handle_order_event(event_data)
                self.metrics["orders_processed"] += 1

            self.metrics["updates_processed"] += 1
            self.update_prioritizer.remove_update(event_id)

        except Exception as e:
            logger.error("Error processing event %s: %s", event_id, str(e))
            self.metrics["updates_deferred"] += 1

    async def process_pending_updates(self) -> None:
        """Process pending updates based on priority and resources."""
        while True:
            # Get next update to process
            update_id = await self.update_prioritizer.get_next_update()
            if not update_id:
                break

            # Skip if already being processed
            if update_id in self._pending_operations:
                continue

            try:
                self._pending_operations.add(update_id)
                updates = self.update_prioritizer.get_pending_updates()
                update_data = updates.get(update_id)

                if update_data:
                    event_data = {
                        "type": str(update_id).split("_")[0],  # Extract type from ID
                        "data": update_data,
                    }
                    await self._process_prioritized_event(
                        update_id, cast(str, event_data["type"]), event_data
                    )

            finally:
                self._pending_operations.remove(update_id)

    async def set_account_context(self, account: Account) -> None:
        """Set the current account context for operations."""
        self._current_account = account

    async def cleanup_expired_updates(self) -> None:
        """Clean up expired updates."""
        expired = self.update_prioritizer.clear_expired_updates()
        if expired:
            logger.info("Cleared %s expired updates", len(expired))
            self.metrics["updates_deferred"] += len(expired)

    def get_metrics(self) -> Dict[str, Any]:
        """Get agent metrics including update statistics."""
        return {
            **self.metrics,
            "pending_updates": len(self.update_prioritizer.get_pending_updates()),
        }

    async def initialize(self) -> None:
        """Initialize marketplace connection"""
        required_fields = self._get_required_config_fields()
        if not all(field in self.config for field in required_fields):
            raise ValueError("Invalid market agent configuration")
        await self._setup_marketplace_client()

    async def _setup_marketplace_client(self) -> None:
        """Set up the marketplace client"""
        pass

    async def _handle_listing_event(self, event: Dict[str, Any]) -> None:
        """Handle listing-related events"""
        pass

    async def _handle_order_event(self, event: Dict[str, Any]) -> None:
        """Handle order-related events"""
        pass

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute marketplace tasks"""
        task_type = task.get("type")
        if task_type == "create_listing":
            return await self._create_listing(task)
        elif task_type == "update_inventory":
            return await self._update_inventory(task)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    async def _create_listing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new listing"""
        return {"status": "not_implemented"}

    async def _update_inventory(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Update inventory levels"""
        return {"status": "not_implemented"}

    async def shutdown(self) -> None:
        """Clean up marketplace resources"""
        await self._cleanup_marketplace_client()
        await self.stop()

    async def _cleanup_marketplace_client(self) -> None:
        """Clean up the marketplace client"""
        pass

    async def stop(self) -> None:
        """Stop the agent"""
        pass
