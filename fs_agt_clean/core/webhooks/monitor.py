"""Webhook monitoring service for FlipSync."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.services.infrastructure.metrics_service import MetricsService

logger = logging.getLogger(__name__)

# Define constants for notification priorities
PRIORITY_LOW = "LOW"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_HIGH = "HIGH"
CATEGORY_SYSTEM_ALERT = "SYSTEM_ALERT"


# Removed normalize_db_result function - no longer needed since Database.fetch_one() returns dict


class WebhookMonitor:
    """Monitor webhook deliveries and alert on issues."""

    def __init__(
        self,
        config_manager: ConfigManager,
        database: Database,
        metrics_service: Optional[MetricsService] = None,
        notification_service: Optional[Any] = None,
        alert_threshold: float = 0.9,  # 90% success rate required
        monitoring_interval: int = 60,  # 1 minute
        stats_retention_days: int = 7,  # Keep 7 days of webhook stats
    ):
        """
        Initialize the webhook monitor.

        Args:
            config_manager: Configuration manager
            database: Database connection
            metrics_service: Optional metrics service
            notification_service: Optional notification service
            alert_threshold: Success rate threshold for alerts
            monitoring_interval: Interval between checks in seconds
            stats_retention_days: Days to retain webhook statistics
        """
        self.config_manager = config_manager
        self.database = database
        self.metrics_service = metrics_service
        self.notification_service = notification_service
        self.alert_threshold = alert_threshold
        self.monitoring_interval = monitoring_interval
        self.stats_retention_days = stats_retention_days

        # Initialize logger
        self.logger = logging.getLogger("webhook_monitor")

        # Initialize current stats
        self.current_stats = {
            "total_deliveries": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "retry_attempts": 0,
            "retry_successes": 0,
            "success_rate": 1.0,
            "retry_success_rate": 0.0,
            "avg_response_time_ms": 0,
            "webhook_count": 0,
            "failed_webhook_count": 0,
        }

        # Track problematic webhooks
        self.problematic_webhooks: Dict[str, Dict[str, Any]] = {}

        # Initialize metric collection dictionaries
        self.successful_deliveries = {"count": 0, "avg_time": 0}
        self.failed_deliveries = {"count": 0}
        self.retry_attempts = {"attempts": 0, "successes": 0}
        self.webhook_counts = {"total": 0, "active": 0, "inactive": 0}
        self.failed_webhook_count = {"count": 0}

    async def start_monitoring(self) -> None:
        """Start the webhook monitoring process."""
        self.logger.info("Starting webhook monitoring")

        # Ensure tables exist
        await self._ensure_tables_exist()

        # Load initial stats
        await self._load_stats()

        # Start background monitoring task
        asyncio.create_task(self._monitoring_loop())

    async def _ensure_tables_exist(self) -> None:
        """Ensure webhook monitoring tables exist."""
        try:
            # Check if webhook_delivery_logs table exists (check both public and flipsync schemas)
            table_check = await self.database.fetch_one(
                """
                SELECT table_name FROM information_schema.tables
                WHERE (table_schema = 'public' OR table_schema = 'flipsync')
                AND table_name = 'webhook_delivery_logs'
                """
            )

            if not table_check:
                # Create webhook_delivery_logs table in public schema (fallback)
                self.logger.info(
                    "Creating webhook_delivery_logs table in public schema"
                )
                await self.database.execute(
                    """
                    CREATE TABLE public.webhook_delivery_logs (
                        id SERIAL PRIMARY KEY,
                        webhook_id INTEGER NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        success BOOLEAN NOT NULL,
                        response_time INTEGER,
                        status_code INTEGER,
                        response_body TEXT,
                        error_message TEXT
                    )
                    """
                )
                self.logger.info("Created webhook_delivery_logs table")
            else:
                self.logger.info("webhook_delivery_logs table already exists")

            # Check if webhook_retry_logs table exists (check both public and flipsync schemas)
            retry_table_check = await self.database.fetch_one(
                """
                SELECT table_name FROM information_schema.tables
                WHERE (table_schema = 'public' OR table_schema = 'flipsync')
                AND table_name = 'webhook_retry_logs'
                """
            )

            if not retry_table_check:
                # Create webhook_retry_logs table in public schema (fallback)
                self.logger.info("Creating webhook_retry_logs table in public schema")
                await self.database.execute(
                    """
                    CREATE TABLE public.webhook_retry_logs (
                        id SERIAL PRIMARY KEY,
                        webhook_id INTEGER NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        status VARCHAR(50) NOT NULL,
                        attempt_number INTEGER NOT NULL,
                        response_time INTEGER,
                        status_code INTEGER,
                        error_message TEXT
                    )
                    """
                )
                self.logger.info("Created webhook_retry_logs table")
            else:
                self.logger.info("webhook_retry_logs table already exists")

            self.logger.info("Webhook monitoring tables verified/created successfully")

        except Exception as e:
            self.logger.error(f"Error ensuring webhook monitoring tables exist: {e}")
            # Don't raise the exception - continue without monitoring tables
            self.logger.warning("Continuing without webhook monitoring tables")

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                # Collect and process metrics
                await self._collect_metrics()

                # Check for alerts
                await self._check_alerts()

                # Clean up old stats
                await self._cleanup_old_stats()

            except Exception as e:
                self.logger.error("Error in webhook monitoring loop: %s", e)

            # Wait for next monitoring interval
            await asyncio.sleep(self.monitoring_interval)

    async def _collect_metrics(self) -> None:
        """Collect webhook delivery metrics from the database."""
        try:
            # Get current timestamp
            now = datetime.now(timezone.utc)

            # Query recent webhook deliveries (last monitoring interval)
            last_check = now - timedelta(seconds=self.monitoring_interval)

            # Initialize default values
            successful_deliveries = {"count": 0, "avg_time": 0}
            failed_deliveries = {"count": 0}

            # Get successful deliveries (use public schema where tables exist)
            try:
                successful_deliveries_result = await self.database.fetch_one(
                    """
                    SELECT COUNT(*) as count, AVG(response_time) as avg_time
                    FROM public.webhook_delivery_logs
                    WHERE timestamp >= :last_check AND success = true
                    """,
                    {"last_check": last_check},
                )

                if successful_deliveries_result:
                    successful_deliveries["count"] = (
                        successful_deliveries_result.get("count", 0) or 0
                    )
                    successful_deliveries["avg_time"] = (
                        successful_deliveries_result.get("avg_time", 0) or 0
                    )

            except Exception as e:
                # If table doesn't exist, just log debug message and continue with defaults
                if "does not exist" in str(e).lower() or "relation" in str(e).lower():
                    self.logger.debug(f"Webhook delivery logs table not available: {e}")
                else:
                    self.logger.error(f"Error getting successful deliveries: {e}")

            # Get failed deliveries (use public schema where tables exist)
            try:
                failed_deliveries_result = await self.database.fetch_one(
                    """
                    SELECT COUNT(*) as count
                    FROM public.webhook_delivery_logs
                    WHERE timestamp >= :last_check AND success = false
                    """,
                    {"last_check": last_check},
                )

                if failed_deliveries_result:
                    failed_deliveries["count"] = (
                        failed_deliveries_result.get("count", 0) or 0
                    )

            except Exception as e:
                # If table doesn't exist, just log debug message and continue with defaults
                if "does not exist" in str(e).lower() or "relation" in str(e).lower():
                    self.logger.debug(f"Webhook delivery logs table not available: {e}")
                else:
                    self.logger.error(f"Error getting failed deliveries: {e}")

            # Update current stats
            self.current_stats["successful_deliveries"] = successful_deliveries["count"]
            self.current_stats["failed_deliveries"] = failed_deliveries["count"]
            self.current_stats["total_deliveries"] = (
                successful_deliveries["count"] + failed_deliveries["count"]
            )

            # Calculate success rate
            if self.current_stats["total_deliveries"] > 0:
                self.current_stats["success_rate"] = (
                    self.current_stats["successful_deliveries"]
                    / self.current_stats["total_deliveries"]
                )
            else:
                self.current_stats["success_rate"] = 1.0

            # Record metrics if service is available
            if self.metrics_service:
                await self.metrics_service.record_metric(
                    "webhook_success_rate", self.current_stats["success_rate"]
                )
                await self.metrics_service.record_metric(
                    "webhook_total_deliveries", self.current_stats["total_deliveries"]
                )

        except Exception as e:
            self.logger.error(f"Error collecting webhook metrics: {e}")

    async def _check_alerts(self) -> None:
        """Check for alert conditions."""
        try:
            # Check success rate threshold
            if self.current_stats["success_rate"] < self.alert_threshold:
                await self._send_alert(
                    f"Webhook success rate ({self.current_stats['success_rate']:.2%}) "
                    f"below threshold ({self.alert_threshold:.2%})"
                )

        except Exception as e:
            self.logger.error(f"Error checking webhook alerts: {e}")

    async def _send_alert(self, message: str) -> None:
        """Send alert notification."""
        self.logger.warning(f"Webhook alert: {message}")

        # Send notification if service is available
        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="webhook_alert",
                    data={"message": message, "timestamp": datetime.now().isoformat()},
                    category=CATEGORY_SYSTEM_ALERT,
                )
            except Exception as e:
                self.logger.error(f"Error sending webhook alert notification: {e}")

    async def _load_stats(self) -> None:
        """Load initial statistics."""
        try:
            # Load basic stats from database
            self.logger.info("Loading initial webhook statistics")
            # Implementation would load from webhook_stats table

        except Exception as e:
            self.logger.error(f"Error loading webhook stats: {e}")

    async def _cleanup_old_stats(self) -> None:
        """Clean up old statistics."""
        try:
            # Clean up old delivery logs
            cutoff_date = datetime.now(timezone.utc) - timedelta(
                days=self.stats_retention_days
            )

            try:
                await self.database.execute(
                    "DELETE FROM public.webhook_delivery_logs WHERE timestamp < :cutoff_date",
                    {"cutoff_date": cutoff_date},
                )
            except Exception as e:
                if "does not exist" in str(e).lower() or "relation" in str(e).lower():
                    self.logger.debug(
                        f"Webhook delivery logs table not available for cleanup: {e}"
                    )
                else:
                    self.logger.error(f"Error cleaning up webhook delivery logs: {e}")

            try:
                await self.database.execute(
                    "DELETE FROM public.webhook_retry_logs WHERE timestamp < :cutoff_date",
                    {"cutoff_date": cutoff_date},
                )
            except Exception as e:
                if "does not exist" in str(e).lower() or "relation" in str(e).lower():
                    self.logger.debug(
                        f"Webhook retry logs table not available for cleanup: {e}"
                    )
                else:
                    self.logger.error(f"Error cleaning up webhook retry logs: {e}")

        except Exception as e:
            self.logger.error(f"Error in webhook stats cleanup: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get current webhook statistics."""
        return self.current_stats.copy()

    async def shutdown(self) -> None:
        """Shutdown the webhook monitor."""
        self.logger.info("Shutting down webhook monitor")
        # Any cleanup tasks would go here
