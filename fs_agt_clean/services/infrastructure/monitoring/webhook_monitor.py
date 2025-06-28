import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union, cast

# Define constants for notification priorities to avoid enum access issues
PRIORITY_LOW = "LOW"
PRIORITY_MEDIUM = "MEDIUM"
PRIORITY_HIGH = "HIGH"
CATEGORY_SYSTEM_ALERT = "SYSTEM_ALERT"

# Use TYPE_CHECKING for type annotations
if TYPE_CHECKING:
    from fs_agt_clean.core.config.config_manager import ConfigManager
    from fs_agt_clean.core.db.database import Database
    from fs_agt_clean.core.monitoring.metrics_service import MetricsService
    from fs_agt_clean.services.notifications.service import NotificationService
else:
    # Simple type aliases for runtime
    ConfigManager = Any
    Database = Any
    MetricsService = Any
    NotificationService = Any


def normalize_db_result(
    result: Any, expected_keys: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convert a database result to a dict. Optionally, an expected_keys list
    can be provided if result is a tuple or list.

    Args:
        result: The database query result to normalize
        expected_keys: List of expected keys if result is a tuple/list

    Returns:
        A dictionary representation of the result
    """
    logger = logging.getLogger("webhook_monitor")
    logger.info(
        f"Normalizing result: {type(result)}, {result}, expected_keys={expected_keys}"
    )

    # Handle None case
    if result is None:
        logger.info("Result is None, returning empty dict")
        return {}

    # Handle dict case
    if isinstance(result, dict):
        logger.info("Result is already a dict, returning as is")
        return result

    # Handle Record-like objects (SQLAlchemy, databases, etc.)
    if hasattr(result, "_mapping"):
        try:
            logger.info("Converting _mapping attribute to dict")
            result_dict = dict(result._mapping)
            logger.info(f"Converted to: {result_dict}")
            return result_dict
        except Exception as e:
            logger.error(f"Failed to convert _mapping to dict: {e}")
            # Continue to other methods

    # Handle objects with keys() method
    if hasattr(result, "keys"):
        try:
            logger.info("Converting object with keys() method to dict")
            result_dict = {key: result[key] for key in result.keys()}
            logger.info(f"Converted to: {result_dict}")
            return result_dict
        except Exception as e:
            logger.error(f"Failed to convert keys() to dict: {e}")
            # Continue to other methods

    # Handle tuple/list case with expected keys
    if isinstance(result, (tuple, list)) and expected_keys is not None:
        try:
            logger.info(
                f"Converting tuple/list to dict with expected keys: {expected_keys}"
            )
            # If result is empty, return an empty dict
            if not result:
                logger.info("Result is empty, returning empty dict")
                return {}

            # Handle case where result is a single-item tuple containing a dict
            if len(result) == 1 and isinstance(result[0], dict):
                logger.info(
                    "Found single-item tuple containing a dict, returning inner dict"
                )
                return result[0]

            # Check that the number of items matches the expected keys
            if len(result) != len(expected_keys):
                logger.warning(
                    f"Expected {len(expected_keys)} columns but got {len(result)}. Result: {result}"
                )
                # Create a dict with default values for all expected keys
                return {key: None for key in expected_keys}

            # Create a dictionary from the tuple/list and expected keys
            # This is the most common case for database results
            result_dict = {}
            for i, key in enumerate(expected_keys):
                if i < len(result):
                    result_dict[key] = result[i]
                else:
                    result_dict[key] = None

            logger.info(f"Converted to: {result_dict}")
            return result_dict
        except Exception as e:
            logger.error(f"Failed to convert tuple/list to dict: {e}")
            # Continue to other methods

    # Handle objects with __getitem__ method
    if hasattr(result, "__getitem__"):
        if expected_keys is not None:
            try:
                logger.info("Trying key-based access with __getitem__")
                result_dict = {}
                for key in expected_keys:
                    try:
                        result_dict[key] = result[key]
                    except (KeyError, IndexError, TypeError):
                        result_dict[key] = None
                logger.info(f"Converted to: {result_dict}")
                return result_dict
            except Exception as e:
                logger.error(f"Failed key-based access: {e}")
                try:
                    # Try positional access if key access fails
                    logger.info("Trying positional access with __getitem__")
                    result_dict = {}
                    for i, key in enumerate(expected_keys):
                        try:
                            result_dict[key] = result[i]
                        except (IndexError, TypeError):
                            result_dict[key] = None
                    logger.info(f"Converted to: {result_dict}")
                    return result_dict
                except Exception as e2:
                    logger.error(f"Failed positional access: {e2}")
                    # Continue to other methods

    # Last resort: try direct conversion
    try:
        logger.info("Trying direct dict() conversion")
        # Print detailed information about the result
        logger.info(f"Result type: {type(result)}")
        logger.info(f"Result value: {result}")
        if isinstance(result, (list, tuple)):
            logger.info(f"Result length: {len(result)}")
            if len(result) > 0:
                logger.info(f"First item type: {type(result[0])}")
                logger.info(f"First item value: {result[0]}")
                if len(result) > 1:
                    logger.info(f"Second item type: {type(result[1])}")
                    logger.info(f"Second item value: {result[1]}")

        # Check if result is a sequence of key-value pairs
        if isinstance(result, (list, tuple)) and all(
            isinstance(item, (list, tuple)) and len(item) == 2 for item in result
        ):
            result_dict = dict(result)
            logger.info(f"Converted sequence of key-value pairs to: {result_dict}")
            return result_dict
        # If it's a single key-value pair, handle it specially
        elif (
            isinstance(result, (list, tuple))
            and len(result) == 2
            and not isinstance(result[0], (list, tuple))
        ):
            # Convert to string keys for safety
            key = str(result[0]) if result[0] is not None else "None"
            result_dict = {key: result[1]}
            logger.info(f"Converted single key-value pair to: {result_dict}")
            return result_dict
        # Otherwise, try standard dict conversion
        else:
            # If we have expected keys and result is a single value, create a dict with the first key
            if (
                isinstance(result, (list, tuple))
                and len(result) == 1
                and expected_keys
                and len(expected_keys) > 0
            ):
                result_dict = {expected_keys[0]: result[0]}
                logger.info(f"Created dict with first expected key: {result_dict}")
                return result_dict
            # Try standard dict conversion
            result_dict = dict(result)
            logger.info(f"Converted to: {result_dict}")
            return result_dict
    except Exception as e:
        logger.error(f"Failed direct conversion: {e}")
        logger.error(f"Result type: {type(result)}, value: {result}")
        # If all else fails, return an empty dict or a dict with None values
        if expected_keys is not None:
            return {key: None for key in expected_keys}
        return {}


class WebhookMonitor:
    """Monitor webhook deliveries and alert on issues."""

    def __init__(
        self,
        config_manager: Any,
        database: Any,
        metrics_service: Optional[Any] = None,
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
            # Create all tables with IF NOT EXISTS to avoid errors
            # This is safer than checking if they exist first

            # Create webhook_delivery_logs table
            self.logger.info("Ensuring webhook_delivery_logs table exists")
            await self.database.execute(
                """
                CREATE TABLE IF NOT EXISTS webhook_delivery_logs (
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

            # Create webhook_retry_logs table
            self.logger.info("Ensuring webhook_retry_logs table exists")
            await self.database.execute(
                """
                CREATE TABLE IF NOT EXISTS webhook_retry_logs (
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

            # Check if webhook_stats table exists with the correct schema
            self.logger.info("Checking webhook_stats table schema")
            try:
                # Try to insert a test record to see if the schema is correct
                await self.database.execute(
                    """
                    INSERT INTO webhook_stats (
                        timestamp,
                        total_deliveries,
                        successful_deliveries,
                        failed_deliveries,
                        retry_attempts,
                        retry_successes,
                        success_rate,
                        retry_success_rate,
                        avg_response_time_ms,
                        webhook_count,
                        failed_webhook_count
                    ) VALUES (NOW(), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
                    """
                )
                # If we get here, the schema is correct
                self.logger.info("webhook_stats table exists with correct schema")
                # Delete the test record
                await self.database.execute(
                    """
                    DELETE FROM webhook_stats WHERE total_deliveries = 0 AND successful_deliveries = 0
                    AND failed_deliveries = 0 AND retry_attempts = 0 AND retry_successes = 0
                    AND success_rate = 0 AND retry_success_rate = 0 AND avg_response_time_ms = 0
                    AND webhook_count = 0 AND failed_webhook_count = 0
                    """
                )
            except Exception as schema_error:
                # If we get here, the schema is incorrect or the table doesn't exist
                self.logger.warning(
                    f"webhook_stats table has incorrect schema: {schema_error}"
                )
                self.logger.info("Dropping and recreating webhook_stats table")
                # Drop the table if it exists
                await self.database.execute(
                    """
                    DROP TABLE IF EXISTS webhook_stats
                    """
                )
                # Create webhook_stats table with the correct schema
                self.logger.info("Creating webhook_stats table with correct schema")
                await self.database.execute(
                    """
                    CREATE TABLE webhook_stats (
                        id UUID PRIMARY KEY,
                        timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        total_deliveries INTEGER NOT NULL,
                        successful_deliveries INTEGER NOT NULL,
                        failed_deliveries INTEGER NOT NULL,
                        retry_attempts INTEGER NOT NULL,
                        retry_successes INTEGER NOT NULL,
                        success_rate FLOAT NOT NULL,
                        retry_success_rate FLOAT NOT NULL,
                        avg_response_time_ms FLOAT NOT NULL,
                        webhook_count INTEGER NOT NULL,
                        failed_webhook_count INTEGER NOT NULL
                    )
                    """
                )
                self.logger.info("webhook_stats table created successfully")

        except Exception as e:
            self.logger.error(f"Error ensuring webhook monitoring tables exist: {e}")

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
            now = datetime.utcnow()

            # Query recent webhook deliveries (last monitoring interval)
            last_check = now - timedelta(seconds=self.monitoring_interval)

            # Initialize default values
            successful_deliveries = {"count": 0, "avg_time": 0}
            failed_deliveries = {"count": 0}
            retry_attempts = {"attempts": 0, "successes": 0}
            webhook_counts = {"total": 0, "active": 0, "inactive": 0}
            failed_webhook_count = {"count": 0}

            # Execute database queries with error handling
            try:
                # Get successful deliveries
                successful_deliveries_result = await self.database.fetch_one(
                    """
                    SELECT COUNT(*) as count, AVG(response_time) as avg_time
                    FROM webhook_delivery_logs
                    WHERE timestamp >= :last_check AND success = 1
                    """,
                    {"last_check": last_check},
                )

                # Add more debug information
                self.logger.info(
                    f"Successful deliveries result: {type(successful_deliveries_result)}, {successful_deliveries_result}"
                )

                # Handle None result
                if successful_deliveries_result is None:
                    self.logger.info("No successful deliveries found")
                    successful_deliveries["count"] = 0
                    successful_deliveries["avg_time"] = 0
                else:
                    # Convert result to dictionary using our helper function
                    result_dict = normalize_db_result(
                        successful_deliveries_result,
                        expected_keys=["count", "avg_time"],
                    )

                    self.logger.info(f"Normalized result_dict: {result_dict}")

                    # Update with safe access - use direct assignment instead of update()
                    successful_deliveries["count"] = result_dict.get("count", 0)
                    successful_deliveries["avg_time"] = result_dict.get("avg_time", 0)

                # Get failed deliveries
                try:
                    failed_deliveries_result = await self.database.fetch_one(
                        """
                        SELECT COUNT(*) as count
                        FROM webhook_delivery_logs
                        WHERE timestamp >= :last_check AND success = 0
                        """,
                        {"last_check": last_check},
                    )

                    # Handle None result
                    if failed_deliveries_result is None:
                        self.logger.info("No failed deliveries found")
                        failed_deliveries["count"] = 0
                    else:
                        # Convert result to dictionary using our helper function
                        result_dict = normalize_db_result(
                            failed_deliveries_result, expected_keys=["count"]
                        )

                        # Update with safe access - use direct assignment
                        failed_deliveries["count"] = result_dict.get("count", 0)
                except Exception as e:
                    self.logger.error(f"Error getting failed deliveries: {e}")
                    failed_deliveries["count"] = 0

                # Get retry attempts
                try:
                    retry_attempts_result = await self.database.fetch_one(
                        """
                        SELECT
                            COUNT(*) as attempts,
                            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successes
                        FROM webhook_retry_logs
                        WHERE timestamp >= :last_check
                        """,
                        {"last_check": last_check},
                    )

                    # Handle None result
                    if retry_attempts_result is None:
                        self.logger.info("No retry attempts found")
                        retry_attempts["attempts"] = 0
                        retry_attempts["successes"] = 0
                    else:
                        # Convert result to dictionary using our helper function
                        result_dict = normalize_db_result(
                            retry_attempts_result,
                            expected_keys=["attempts", "successes"],
                        )

                        # Update with safe access - use direct assignment
                        retry_attempts["attempts"] = result_dict.get("attempts", 0)
                        retry_attempts["successes"] = (
                            result_dict.get("successes", 0) or 0
                        )
                except Exception as e:
                    self.logger.error(f"Error getting retry attempts: {e}")
                    retry_attempts["attempts"] = 0
                    retry_attempts["successes"] = 0

                # Get webhook counts
                try:
                    webhook_counts_result = await self.database.fetch_one(
                        """
                        SELECT
                            COUNT(*) as total,
                            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                            SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END) as inactive
                        FROM webhooks
                        """
                    )

                    # Handle None result
                    if webhook_counts_result is None:
                        self.logger.info("No webhooks found")
                        webhook_counts["total"] = 0
                        webhook_counts["active"] = 0
                        webhook_counts["inactive"] = 0
                    else:
                        # Convert result to dictionary using our helper function
                        result_dict = normalize_db_result(
                            webhook_counts_result,
                            expected_keys=["total", "active", "inactive"],
                        )

                        # Update with safe access - use direct assignment
                        webhook_counts["total"] = result_dict.get("total", 0)
                        webhook_counts["active"] = result_dict.get("active", 0) or 0
                        webhook_counts["inactive"] = result_dict.get("inactive", 0) or 0
                except Exception as e:
                    self.logger.error(f"Error getting webhook counts: {e}")
                    webhook_counts["total"] = 0
                    webhook_counts["active"] = 0
                    webhook_counts["inactive"] = 0

                # Get failed webhook count
                try:
                    failed_webhook_count_result = await self.database.fetch_one(
                        """
                        SELECT COUNT(DISTINCT webhook_id) as count
                        FROM webhook_retry_logs
                        WHERE status = 'pending' OR status = 'processing'
                        """
                    )

                    # Handle None result
                    if failed_webhook_count_result is None:
                        self.logger.info("No failed webhooks found")
                        failed_webhook_count["count"] = 0
                    else:
                        # Convert result to dictionary using our helper function
                        result_dict = normalize_db_result(
                            failed_webhook_count_result, expected_keys=["count"]
                        )

                        # Update with safe access - use direct assignment
                        failed_webhook_count["count"] = result_dict.get("count", 0)
                except Exception as e:
                    self.logger.error(f"Error getting failed webhook count: {e}")
                    failed_webhook_count["count"] = 0

            except Exception as e:
                self.logger.error(
                    "Database query failed in webhook metrics collection: %s", e
                )
                # Print more detailed error information
                import traceback

                self.logger.error("Traceback: %s", traceback.format_exc())
                return

            # Add debug information for dictionaries
            self.logger.info("successful_deliveries: %s", successful_deliveries)
            self.logger.info("failed_deliveries: %s", failed_deliveries)
            self.logger.info("retry_attempts: %s", retry_attempts)
            self.logger.info("webhook_counts: %s", webhook_counts)
            self.logger.info("failed_webhook_count: %s", failed_webhook_count)

            # Update current stats - safely extract values with defaults
            successful_count = successful_deliveries.get("count", 0)
            failed_count = failed_deliveries.get("count", 0)
            total_count = successful_count + failed_count

            retry_attempt_count = retry_attempts.get("attempts", 0)
            retry_success_count = retry_attempts.get("successes", 0)

            # Ensure avg_response_time is not None
            avg_response_time = successful_deliveries.get("avg_time", 0)
            if avg_response_time is None:
                avg_response_time = 0

            # Calculate rates
            success_rate = successful_count / total_count if total_count > 0 else 1.0

            retry_success_rate = (
                retry_success_count / retry_attempt_count
                if retry_attempt_count > 0
                else 0.0
            )

            # Create a copy of the current stats
            new_stats = dict(self.current_stats)

            # Update the copy with new values
            new_stats["total_deliveries"] = new_stats["total_deliveries"] + total_count
            new_stats["successful_deliveries"] = (
                new_stats["successful_deliveries"] + successful_count
            )
            new_stats["failed_deliveries"] = (
                new_stats["failed_deliveries"] + failed_count
            )
            new_stats["retry_attempts"] = (
                new_stats["retry_attempts"] + retry_attempt_count
            )
            new_stats["retry_successes"] = (
                new_stats["retry_successes"] + retry_success_count
            )
            new_stats["success_rate"] = success_rate
            new_stats["retry_success_rate"] = retry_success_rate
            new_stats["avg_response_time_ms"] = avg_response_time
            new_stats["webhook_count"] = webhook_counts.get("total", 0)
            new_stats["failed_webhook_count"] = failed_webhook_count.get("count", 0)

            # Replace the current stats with the new stats
            self.current_stats = new_stats

            # Record metrics
            if self.metrics_service:
                await self.metrics_service.record_metric(
                    name="webhook_success_rate",
                    value=success_rate * 100.0,
                    labels={"interval": f"{self.monitoring_interval}s"},
                )

                await self.metrics_service.record_metric(
                    name="webhook_retry_success_rate",
                    value=retry_success_rate * 100.0,
                    labels={"interval": f"{self.monitoring_interval}s"},
                )

                await self.metrics_service.record_metric(
                    name="webhook_avg_response_time",
                    value=self.current_stats["avg_response_time_ms"],
                    labels={"interval": f"{self.monitoring_interval}s"},
                )

                await self.metrics_service.record_metric(
                    name="webhook_failed_count",
                    value=self.current_stats["failed_webhook_count"],
                    labels={},
                )

            # Persist stats
            await self._persist_stats()

            # Log stats
            self.logger.info(
                f"Webhook stats: Success rate {success_rate:.2%}, "
                f"Retry success rate {retry_success_rate:.2%}, "
                f"Failed webhooks: {self.current_stats['failed_webhook_count']}"
            )

        except Exception as e:
            self.logger.error("Error collecting webhook metrics: %s", e)

    async def _check_alerts(self) -> None:
        """Check if any alerts should be triggered based on metrics."""
        try:
            # Check overall success rate
            if self.current_stats["success_rate"] < self.alert_threshold:
                # Alert on low success rate
                await self._send_alert(
                    "webhook_low_success_rate",
                    f"Webhook delivery success rate is below threshold: "
                    f"{self.current_stats['success_rate']:.2%} (threshold: {self.alert_threshold:.2%})",
                    PRIORITY_HIGH,
                )

            # Check for webhooks with sustained failures
            try:
                problem_webhooks_result = await self.database.fetch_all(
                    """
                    SELECT
                        r.webhook_id,
                        w.url,
                        COUNT(*) as failure_count,
                        MAX(retry_count) as max_retries,
                        MIN(r.timestamp) as first_failure
                    FROM webhook_retry_logs r
                    JOIN webhooks w ON r.webhook_id = w.id
                    WHERE r.status = 'pending' OR r.status = 'processing'
                    GROUP BY r.webhook_id, w.url
                    HAVING COUNT(*) >= 5  -- Consider webhooks with 5+ failures
                    """
                )

                # Convert result to list of dictionaries using our helper function
                problem_webhooks = []
                if problem_webhooks_result:
                    for row in problem_webhooks_result:
                        row_dict = normalize_db_result(
                            row,
                            expected_keys=[
                                "webhook_id",
                                "url",
                                "failure_count",
                                "max_retries",
                                "first_failure",
                            ],
                        )
                        problem_webhooks.append(row_dict)
            except Exception as e:
                self.logger.error("Failed to query problem webhooks: %s", e)
                problem_webhooks = []

            # Set to collect webhook IDs for problematic webhooks
            problem_webhook_ids = set()

            for webhook_dict in problem_webhooks:
                try:
                    # Get webhook ID with default
                    webhook_id = webhook_dict.get("webhook_id", "unknown")
                    problem_webhook_ids.add(webhook_id)

                    # Check if this is a new problematic webhook
                    if webhook_id not in self.problematic_webhooks:
                        self.problematic_webhooks[webhook_id] = {
                            "url": webhook_dict.get("url", "unknown"),
                            "first_alert_sent": False,
                            "last_alert_sent": None,
                            "failure_count": webhook_dict.get("failure_count", 0),
                            "first_failure": webhook_dict.get(
                                "first_failure", "unknown"
                            ),
                        }

                    webhook_info = self.problematic_webhooks[webhook_id]

                    # Send initial alert if not sent already
                    if not webhook_info["first_alert_sent"]:
                        await self._send_alert(
                            "webhook_sustained_failures",
                            f"Webhook {webhook_id} ({webhook_dict.get('url', 'unknown')}) has sustained failures. "
                            f"Failed {webhook_dict.get('failure_count', 0)} times since {webhook_dict.get('first_failure', 'unknown')}.",
                            PRIORITY_MEDIUM,
                        )

                        webhook_info["first_alert_sent"] = True
                        webhook_info["last_alert_sent"] = datetime.utcnow()

                    # Send follow-up alert every 24 hours for sustained issues
                    elif webhook_info["last_alert_sent"] and (
                        datetime.utcnow() - webhook_info["last_alert_sent"]
                        > timedelta(hours=24)
                    ):
                        # Update failure count
                        new_failures = (
                            webhook_dict.get("failure_count", 0)
                            - webhook_info["failure_count"]
                        )

                        await self._send_alert(
                            "webhook_sustained_failures_update",
                            f"Webhook {webhook_id} ({webhook_dict.get('url', 'unknown')}) continues to fail. "
                            f"{new_failures} new failures in the last 24 hours. "
                            f"Total: {webhook_dict.get('failure_count', 0)} failures since {webhook_dict.get('first_failure', 'unknown')}.",
                            PRIORITY_MEDIUM,
                        )

                        webhook_info["last_alert_sent"] = datetime.utcnow()
                        webhook_info["failure_count"] = webhook_dict.get(
                            "failure_count", 0
                        )
                except Exception as e:
                    self.logger.error("Error processing problem webhook: %s", e)
                    continue

            # Remove webhooks that are no longer problematic
            resolved_webhooks = [
                webhook_id
                for webhook_id in self.problematic_webhooks
                if webhook_id not in problem_webhook_ids
            ]

            for webhook_id in resolved_webhooks:
                webhook_info = self.problematic_webhooks.pop(webhook_id)

                # Send resolution notification
                await self._send_alert(
                    "webhook_failures_resolved",
                    f"Webhook {webhook_id} ({webhook_info['url']}) is no longer failing.",
                    PRIORITY_LOW,
                )

        except Exception as e:
            self.logger.error("Error checking webhook alerts: %s", e)

    async def _send_alert(self, template_id: str, message: str, priority: str) -> None:
        """Send an alert notification."""
        self.logger.warning("WEBHOOK ALERT: %s", message)

        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id=template_id,
                    category=CATEGORY_SYSTEM_ALERT,
                    data={
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat(),
                        "priority": priority,
                    },
                )
            except Exception as e:
                self.logger.error("Error sending notification: %s", e)

    async def _load_stats(self) -> None:
        """Load webhook stats from database."""
        try:
            # Load the latest stats record
            stats = await self.database.fetch_one(
                """
                SELECT * FROM webhook_stats
                ORDER BY timestamp DESC
                LIMIT 1
                """
            )

            if stats:
                # Convert result to dictionary using our helper function
                stats_dict = normalize_db_result(
                    stats,
                    expected_keys=[
                        "id",
                        "timestamp",
                        "total_deliveries",
                        "successful_deliveries",
                        "failed_deliveries",
                        "retry_attempts",
                        "retry_successes",
                        "success_rate",
                        "retry_success_rate",
                        "avg_response_time_ms",
                        "webhook_count",
                        "failed_webhook_count",
                    ],
                )

                # Create a new dictionary with updated values
                new_stats = {
                    "total_deliveries": stats_dict.get("total_deliveries", 0),
                    "successful_deliveries": stats_dict.get("successful_deliveries", 0),
                    "failed_deliveries": stats_dict.get("failed_deliveries", 0),
                    "retry_attempts": stats_dict.get("retry_attempts", 0),
                    "retry_successes": stats_dict.get("retry_successes", 0),
                    "success_rate": stats_dict.get("success_rate", 1.0),
                    "retry_success_rate": stats_dict.get("retry_success_rate", 0.0),
                    "avg_response_time_ms": stats_dict.get("avg_response_time_ms", 0),
                    "webhook_count": stats_dict.get("webhook_count", 0),
                    "failed_webhook_count": stats_dict.get("failed_webhook_count", 0),
                }

                # Replace the current stats with the new stats
                self.current_stats = new_stats

        except Exception as e:
            self.logger.error("Error loading webhook stats: %s", e)

    async def _persist_stats(self) -> None:
        """Persist current webhook stats to database."""
        try:
            now = datetime.utcnow()

            # Generate a UUID for the id field
            import uuid

            await self.database.execute(
                """
                INSERT INTO webhook_stats (
                    id,
                    timestamp,
                    total_deliveries,
                    successful_deliveries,
                    failed_deliveries,
                    retry_attempts,
                    retry_successes,
                    success_rate,
                    retry_success_rate,
                    avg_response_time_ms,
                    webhook_count,
                    failed_webhook_count
                ) VALUES (:id, :timestamp, :total_deliveries, :successful_deliveries, :failed_deliveries,
                          :retry_attempts, :retry_successes, :success_rate, :retry_success_rate,
                          :avg_response_time_ms, :webhook_count, :failed_webhook_count)
                """,
                {
                    "id": str(uuid.uuid4()),  # Generate a UUID for the id field
                    "timestamp": now,
                    "total_deliveries": self.current_stats["total_deliveries"],
                    "successful_deliveries": self.current_stats[
                        "successful_deliveries"
                    ],
                    "failed_deliveries": self.current_stats["failed_deliveries"],
                    "retry_attempts": self.current_stats["retry_attempts"],
                    "retry_successes": self.current_stats["retry_successes"],
                    "success_rate": self.current_stats["success_rate"],
                    "retry_success_rate": self.current_stats["retry_success_rate"],
                    "avg_response_time_ms": (
                        self.current_stats["avg_response_time_ms"]
                        if self.current_stats["avg_response_time_ms"] is not None
                        else 0
                    ),
                    "webhook_count": self.current_stats["webhook_count"],
                    "failed_webhook_count": self.current_stats["failed_webhook_count"],
                },
            )

        except Exception as e:
            self.logger.error("Error persisting webhook stats: %s", e)

    async def _cleanup_old_stats(self) -> None:
        """Clean up old webhook stats records."""
        try:
            retention_date = datetime.utcnow() - timedelta(
                days=self.stats_retention_days
            )

            await self.database.execute(
                """
                DELETE FROM webhook_stats
                WHERE timestamp < :retention_date
                """,
                {"retention_date": retention_date},
            )

            await self.database.execute(
                """
                DELETE FROM webhook_delivery_logs
                WHERE timestamp < :retention_date
                """,
                {"retention_date": retention_date},
            )

            await self.database.execute(
                """
                DELETE FROM webhook_retry_logs
                WHERE timestamp < :retention_date
                """,
                {"retention_date": retention_date},
            )

        except Exception as e:
            self.logger.error("Error cleaning up old webhook stats: %s", e)

    async def get_webhook_stats(self) -> Dict[str, Any]:
        """Get current webhook statistics."""
        return self.current_stats

    async def get_problematic_webhooks(self) -> List[Dict[str, Any]]:
        """Get list of problematic webhooks."""
        return [
            {"id": webhook_id, **info}
            for webhook_id, info in self.problematic_webhooks.items()
        ]
