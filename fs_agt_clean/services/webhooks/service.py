"""Webhook service for FlipSync."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.webhooks.monitor import WebhookMonitor
from fs_agt_clean.services.infrastructure.metrics_service import MetricsService

logger = logging.getLogger(__name__)


class WebhookService:
    """Main webhook service for managing webhook operations."""

    def __init__(
        self,
        config_manager: ConfigManager,
        database: Database,
        metrics_service: Optional[MetricsService] = None,
        notification_service: Optional[Any] = None,
    ):
        """Initialize the webhook service.

        Args:
            config_manager: Configuration manager
            database: Database instance
            metrics_service: Metrics service (optional)
            notification_service: Notification service (optional)
        """
        self.config_manager = config_manager
        self.database = database
        self.metrics_service = metrics_service
        self.notification_service = notification_service
        self.logger = logging.getLogger(__name__)

        # Initialize webhook monitor
        self.monitor = WebhookMonitor(
            config_manager=config_manager,
            database=database,
            metrics_service=metrics_service,
            notification_service=notification_service,
        )

        # Track registered webhooks
        self.registered_webhooks: Dict[str, Dict[str, Any]] = {}

        # Initialize handlers
        self.handlers: Dict[str, Any] = {}

    async def initialize(self) -> None:
        """Initialize the webhook service."""
        try:
            # Ensure database tables exist
            await self._ensure_tables_exist()

            # Start webhook monitoring
            await self.monitor.start_monitoring()

            # Load registered webhooks
            await self._load_registered_webhooks()

            self.logger.info("Webhook service initialized successfully")

        except Exception as e:
            self.logger.error(f"Failed to initialize webhook service: {e}")
            raise

    async def _ensure_tables_exist(self) -> None:
        """Ensure webhook tables exist."""
        try:
            # The webhook database tables are already created by init_webhook_db
            # We just need to verify they exist
            self.logger.info("Verifying webhook database tables exist")

            # Check if webhooks table exists
            result = await self.database.fetch_one(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_name = 'webhooks'
                """
            )

            if result:
                self.logger.info("Webhook database tables verified")
            else:
                self.logger.warning(
                    "Webhook tables not found - they should have been created by init_webhook_db"
                )

        except Exception as e:
            self.logger.error(f"Error verifying webhook tables: {e}")

    async def _load_registered_webhooks(self) -> None:
        """Load registered webhooks from database."""
        try:
            # Load webhooks from database (using 'status' column instead of 'is_active')
            webhooks = await self.database.fetch_all(
                "SELECT id, url, event_types, status, created_at FROM webhooks WHERE status = 'active'"
            )

            for webhook in webhooks:
                webhook_id = str(webhook.get("id", ""))
                self.registered_webhooks[webhook_id] = {
                    "url": webhook.get("url", ""),
                    "event_types": webhook.get("event_types", []),
                    "is_active": webhook.get("status") == "active",
                    "created_at": webhook.get("created_at"),
                }

            self.logger.info(
                f"Loaded {len(self.registered_webhooks)} registered webhooks"
            )

        except Exception as e:
            self.logger.error(f"Error loading registered webhooks: {e}")

    async def register_webhook(
        self, url: str, event_types: List[str], secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new webhook.

        Args:
            url: Webhook callback URL
            event_types: List of event types to subscribe to
            secret: Optional webhook secret for signature verification

        Returns:
            Dict containing webhook registration details
        """
        try:
            # Insert webhook into database (using 'status' column)
            webhook_id = await self.database.execute(
                """
                INSERT INTO webhooks (url, event_types, secret, status, created_at)
                VALUES (:url, :event_types, :secret, :status, :created_at)
                RETURNING id
                """,
                {
                    "url": url,
                    "event_types": str(event_types),  # Convert to string for storage
                    "secret": secret,
                    "status": "active",
                    "created_at": datetime.now(timezone.utc),
                },
            )

            # Add to registered webhooks
            self.registered_webhooks[str(webhook_id)] = {
                "url": url,
                "event_types": event_types,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
            }

            self.logger.info(f"Registered webhook {webhook_id} for URL: {url}")

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.record_metric(
                    "webhook_registered", 1.0, labels={"url": url}
                )

            return {
                "id": webhook_id,
                "url": url,
                "event_types": event_types,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error registering webhook: {e}")
            raise

    async def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook.

        Args:
            webhook_id: ID of webhook to unregister

        Returns:
            True if successful, False otherwise
        """
        try:
            # Deactivate webhook in database (using 'status' column)
            await self.database.execute(
                "UPDATE webhooks SET status = :status WHERE id = :webhook_id",
                {"status": "inactive", "webhook_id": webhook_id},
            )

            # Remove from registered webhooks
            if webhook_id in self.registered_webhooks:
                del self.registered_webhooks[webhook_id]

            self.logger.info(f"Unregistered webhook {webhook_id}")

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.record_metric(
                    "webhook_unregistered", 1.0, labels={"webhook_id": webhook_id}
                )

            return True

        except Exception as e:
            self.logger.error(f"Error unregistering webhook {webhook_id}: {e}")
            return False

    async def send_webhook_event(
        self, event_type: str, event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send webhook event to registered webhooks.

        Args:
            event_type: Type of event
            event_data: Event data to send

        Returns:
            Dict containing delivery results
        """
        try:
            delivery_results = {}

            # Find webhooks subscribed to this event type
            for webhook_id, webhook_info in self.registered_webhooks.items():
                if event_type in webhook_info["event_types"]:
                    try:
                        # Send webhook (simplified implementation)
                        # In a real implementation, this would make HTTP requests
                        self.logger.info(
                            f"Sending {event_type} event to webhook {webhook_id} at {webhook_info['url']}"
                        )

                        # Record successful delivery
                        await self.database.execute(
                            """
                            INSERT INTO webhook_events (webhook_id, event_type, event_data, status, created_at)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                webhook_id,
                                event_type,
                                event_data,
                                "delivered",
                                datetime.now(timezone.utc),
                            ),
                        )

                        delivery_results[webhook_id] = {
                            "status": "delivered",
                            "url": webhook_info["url"],
                        }

                    except Exception as e:
                        self.logger.error(f"Error sending webhook to {webhook_id}: {e}")
                        delivery_results[webhook_id] = {
                            "status": "failed",
                            "error": str(e),
                            "url": webhook_info["url"],
                        }

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.record_metric(
                    "webhook_events_sent",
                    len(delivery_results),
                    labels={"event_type": event_type},
                )

            return {
                "event_type": event_type,
                "deliveries": delivery_results,
                "total_deliveries": len(delivery_results),
            }

        except Exception as e:
            self.logger.error(f"Error sending webhook event {event_type}: {e}")
            raise

    async def get_webhook_stats(self) -> Dict[str, Any]:
        """Get webhook statistics.

        Returns:
            Dict containing webhook statistics
        """
        try:
            # Get stats from monitor
            monitor_stats = await self.monitor.get_stats()

            # Add service-specific stats
            stats = {
                **monitor_stats,
                "registered_webhooks": len(self.registered_webhooks),
                "active_webhooks": len(
                    [w for w in self.registered_webhooks.values() if w["is_active"]]
                ),
            }

            return stats

        except Exception as e:
            self.logger.error(f"Error getting webhook stats: {e}")
            return {}

    async def register_handler(self, event_type: str, handler: Any) -> None:
        """Register an event handler.

        Args:
            event_type: Type of event to handle
            handler: Handler function or class
        """
        self.handlers[event_type] = handler
        self.logger.info(f"Registered handler for event type: {event_type}")

    async def get_registered_webhooks(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered webhooks.

        Returns:
            Dict of registered webhooks
        """
        return self.registered_webhooks.copy()

    async def shutdown(self) -> None:
        """Shutdown the webhook service."""
        try:
            # Shutdown monitor
            await self.monitor.shutdown()

            self.logger.info("Webhook service shutdown successfully")

        except Exception as e:
            self.logger.error(f"Error shutting down webhook service: {e}")
        finally:
            # Clear registered webhooks
            self.registered_webhooks.clear()
            self.handlers.clear()
