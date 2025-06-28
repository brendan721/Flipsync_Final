"""
Database Monitoring Module

This module provides real-time monitoring of database performance metrics,
alerting, and performance statistics tracking.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, Union, cast

from fs_agt_clean.services.notifications.service import (
    NotificationCategory,
    NotificationPriority,
    NotificationService,
)

# Use string literals for constants to avoid enum access issues
NOTIFICATION_CATEGORY_SYSTEM_INFO = "SYSTEM_INFO"

# Type checking handling
if TYPE_CHECKING:
    from fs_agt_clean.services.notifications.service import NotificationService
else:
    NotificationService = Any


class DatabaseMetricsCollector:
    """
    Collects and tracks database performance metrics.
    """

    def __init__(self, db, logger=None):
        """Initialize the database metrics collector.

        Args:
            db: Database connection pool
            logger: Optional logger instance
        """
        self.db = db
        self.logger = logger or logging.getLogger("db_metrics")

        # Main metrics store
        self.metrics: Dict[str, Any] = {
            "query_count": 0,
            "error_count": 0,
            "slow_query_count": 0,
            "queries_per_second": 0.0,
            "avg_query_time_ms": 0.0,
            "p95_query_time_ms": 0.0,
            "p99_query_time_ms": 0.0,
            "max_query_time_ms": 0.0,
            "total_rows_affected": 0,
            "transaction_count": 0,
            "percentiles": {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0},
        }

        # Connection pool metrics - use all float values for consistency
        self.connection_stats: Dict[str, Union[int, float]] = {
            "total_created": 0,
            "total_closed": 0,
            "total_acquired": 0,
            "total_released": 0,
            "connection_attempts": 0,
            "connection_timeouts": 0,
            "current_active": 0,
            "peak_active": 0,
            "avg_wait_time_ms": 0.0,
            "max_wait_time_ms": 0.0,
            "avg_lifetime_ms": 0.0,
        }

        # Tracking for recent slow queries
        self.recent_slow_queries: List[Dict[str, Any]] = []

        # Tracking for recent errors
        self.recent_errors: List[Dict[str, Any]] = []

        # History of metrics for trend analysis
        self.metrics_history: List[Dict[str, Any]] = []

        # Query execution times for percentile calculation
        self.recent_query_times: List[float] = []

        # Configurable thresholds
        self.slow_query_threshold_ms = 100.0
        self.metrics_retention_days = 7

        # Setup DB hooks if possible
        self._register_db_hooks()

    def record_query_execution(
        self,
        query: str,
        params: Any,
        execution_time_ms: float,
        rows_affected: int,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """Record a query execution event.

        Args:
            query: Query string
            params: Query parameters
            execution_time_ms: Execution time in milliseconds
            rows_affected: Number of rows affected
            success: Whether the query was successful
            error_message: Optional error message if not successful
        """
        # Update general metrics
        self.metrics["query_count"] += 1

        if success:
            self.metrics["total_rows_affected"] += rows_affected
            self.metrics["transaction_count"] += 1

            # Update average and max query time
            prev_total = self.metrics["avg_query_time_ms"] * (
                self.metrics["query_count"] - 1
            )
            self.metrics["avg_query_time_ms"] = (
                prev_total + execution_time_ms
            ) / self.metrics["query_count"]
            self.metrics["max_query_time_ms"] = max(
                self.metrics["max_query_time_ms"], execution_time_ms
            )

            # Add to query times for percentile calculation
            self.recent_query_times.append(execution_time_ms)
            # Keep only the last 1000 query times
            if len(self.recent_query_times) > 1000:
                self.recent_query_times = self.recent_query_times[-1000:]

            # Check if it's a slow query
            if execution_time_ms > self.slow_query_threshold_ms:
                self.metrics["slow_query_count"] += 1

                # Add to recent slow queries
                self.recent_slow_queries.append(
                    {
                        "query": query,
                        "params": str(params),
                        "execution_time_ms": execution_time_ms,
                        "rows_affected": rows_affected,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

                # Keep only the most recent slow queries
                if len(self.recent_slow_queries) > 50:
                    self.recent_slow_queries = self.recent_slow_queries[-50:]

            # Add to recent queries
            self.recent_queries.append(
                {
                    "query": query,
                    "params": str(params),
                    "execution_time_ms": execution_time_ms,
                    "rows_affected": rows_affected,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Keep only the most recent queries
            if len(self.recent_queries) > 100:
                self.recent_queries = self.recent_queries[-100:]
        else:
            # Record error
            self.metrics["error_count"] += 1

            # Add to recent errors
            self.recent_errors.append(
                {
                    "query": query,
                    "params": str(params),
                    "error": error_message or "Unknown error",
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

            # Keep only the most recent errors
            if len(self.recent_errors) > 50:
                self.recent_errors = self.recent_errors[-50:]

        # Update last update timestamp
        self.metrics["last_update"] = datetime.utcnow().isoformat()

    def record_connection_event(
        self,
        event_type: str,
        wait_time_ms: Optional[float] = None,
        lifetime_ms: Optional[float] = None,
    ) -> None:
        """Record a connection pool event.

        Args:
            event_type: Type of event (create, close, acquire, release, timeout)
            wait_time_ms: Time spent waiting for connection (for acquire)
            lifetime_ms: Connection lifetime (for close)
        """
        if event_type == "create":
            self.connection_stats["total_created"] = (
                cast(int, self.connection_stats["total_created"]) + 1
            )
            self.connection_stats["current_active"] = (
                cast(int, self.connection_stats["current_active"]) + 1
            )

            # Update peak count if needed
            if cast(int, self.connection_stats["current_active"]) > cast(
                int, self.connection_stats["peak_active"]
            ):
                self.connection_stats["peak_active"] = self.connection_stats[
                    "current_active"
                ]

        elif event_type == "close":
            self.connection_stats["total_closed"] = (
                cast(int, self.connection_stats["total_closed"]) + 1
            )
            self.connection_stats["current_active"] = (
                cast(int, self.connection_stats["current_active"]) - 1
            )

            # Track average connection lifetime
            if lifetime_ms is not None:
                # Always work with floats for average calculations
                lifetime_ms_float = float(lifetime_ms)
                total_closed = cast(int, self.connection_stats["total_closed"])
                prev_count = total_closed - 1
                prev_avg = cast(
                    float, self.connection_stats.get("avg_lifetime_ms", 0.0)
                )

                if prev_count > 0:
                    # Calculate new average
                    new_avg = (
                        (prev_avg * prev_count) + lifetime_ms_float
                    ) / total_closed
                    # Store as float
                    self.connection_stats["avg_lifetime_ms"] = new_avg
                else:
                    # First record, just use the value
                    self.connection_stats["avg_lifetime_ms"] = lifetime_ms_float

        elif event_type == "acquire":
            self.connection_stats["connection_attempts"] = (
                cast(int, self.connection_stats["connection_attempts"]) + 1
            )

            if wait_time_ms is not None:
                # Ensure we're working with float
                wait_time_float = float(wait_time_ms)

                # Update max wait time
                if wait_time_float > cast(
                    float, self.connection_stats["max_wait_time_ms"]
                ):
                    self.connection_stats["max_wait_time_ms"] = wait_time_float

                # Update average wait time
                conn_attempts = cast(int, self.connection_stats["connection_attempts"])
                prev_attempts = conn_attempts - 1
                prev_avg = cast(float, self.connection_stats["avg_wait_time_ms"])

                if prev_attempts > 0:
                    new_avg = (
                        (prev_avg * prev_attempts) + wait_time_float
                    ) / conn_attempts
                    self.connection_stats["avg_wait_time_ms"] = new_avg
                else:
                    self.connection_stats["avg_wait_time_ms"] = wait_time_float

            self.connection_stats["total_acquired"] = (
                cast(int, self.connection_stats["total_acquired"]) + 1
            )

        elif event_type == "release":
            self.connection_stats["total_released"] = (
                cast(int, self.connection_stats["total_released"]) + 1
            )

        elif event_type == "timeout":
            self.connection_stats["connection_timeouts"] = (
                cast(int, self.connection_stats["connection_timeouts"]) + 1
            )

    def record_metrics_snapshot(self) -> None:
        """Take a snapshot of current metrics and save to history."""
        # Create a metrics snapshot
        current_time = datetime.utcnow()

        # Get current metrics
        snapshot = self.get_current_metrics()
        snapshot["timestamp"] = current_time.isoformat()

        # Calculate queries per second since last snapshot
        if self.metrics_history:
            try:
                # Get the last snapshot safely
                last_snapshot = self.metrics_history[-1]
                last_time_str = (
                    last_snapshot.get("timestamp") if last_snapshot else None
                )

                if last_time_str:
                    # Parse timestamp and calculate time difference
                    last_time = datetime.fromisoformat(last_time_str)
                    elapsed_seconds = (current_time - last_time).total_seconds()

                    if elapsed_seconds > 0:
                        # Get query counts with defaults
                        current_query_count = self.metrics.get("query_count", 0)
                        last_query_count = last_snapshot.get("query_count", 0)
                        query_diff = current_query_count - last_query_count

                        # Calculate queries per second
                        self.metrics["queries_per_second"] = (
                            query_diff / elapsed_seconds
                        )
            except (ValueError, KeyError, IndexError) as e:
                self.logger.error("Error calculating queries per second: %s", e)

        # Take a snapshot
        self.metrics_history.append(snapshot)

        # Prune old snapshots (keep up to metrics_retention_days)
        self._prune_old_metrics()

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current metrics.

        Returns:
            Current metrics
        """
        # Create a copy of the metrics
        metrics_copy = dict(self.metrics)

        # Add percentiles if we have enough data
        if len(self.recent_query_times) >= 10:
            sorted_times = sorted(self.recent_query_times)
            metrics_copy["percentiles"] = {
                "p50": sorted_times[len(sorted_times) // 2],
                "p90": sorted_times[int(len(sorted_times) * 0.9)],
                "p95": sorted_times[int(len(sorted_times) * 0.95)],
                "p99": sorted_times[int(len(sorted_times) * 0.99)],
            }

        # Add connection stats
        metrics_copy["connection_stats"] = dict(self.connection_stats)

        return metrics_copy

    def get_metrics_history(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics history within a time range.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of metrics snapshots
        """
        # If no time filters, return all history
        if not start_time and not end_time:
            return self.metrics_history

        # Set default end time to now if not provided
        if not end_time:
            end_time = datetime.utcnow()

        # Apply time filters
        filtered_history = []
        for entry in self.metrics_history:
            # Safely get and parse timestamp
            timestamp_str = entry.get("timestamp", "")
            if timestamp_str:
                try:
                    entry_time = datetime.fromisoformat(timestamp_str)

                    # Apply time filters
                    if start_time and entry_time < start_time:
                        continue

                    if entry_time > end_time:
                        continue

                    filtered_history.append(entry)
                except (ValueError, TypeError) as e:
                    self.logger.warning(
                        f"Could not parse timestamp '{timestamp_str}': {e}"
                    )

        return filtered_history

    def get_recent_slow_queries(self) -> List[Dict[str, Any]]:
        """Get recent slow queries.

        Returns:
            List of recent slow queries
        """
        return self.recent_slow_queries

    def get_recent_errors(self) -> List[Dict[str, Any]]:
        """Get recent query errors.

        Returns:
            List of recent errors
        """
        return self.recent_errors

    def export_metrics(self, file_path: str) -> None:
        """Export metrics to a file.

        Args:
            file_path: Path to save the metrics
        """
        export_data = {
            "current_metrics": self.get_current_metrics(),
            "metrics_history": self.metrics_history,
            "recent_slow_queries": self.recent_slow_queries,
            "recent_errors": self.recent_errors,
            "export_time": datetime.utcnow().isoformat(),
        }

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        self.logger.info("Metrics exported to %s", file_path)

    # Hook registrar for database monitoring
    def _register_db_hooks(self) -> None:
        """Register hooks on the database connection.

        Note: This is a placeholder. The actual implementation will depend on
        the database driver and connection pool being used.
        """
        # In an actual implementation, this would add hooks to track
        # query execution and connection events
        pass


class DatabaseMonitor:
    """
    Monitors database performance and triggers alerts when thresholds are exceeded.
    """

    def __init__(
        self,
        db,
        notification_service: Optional[NotificationService] = None,
        config: Optional[Dict[str, Any]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the database monitor.

        Args:
            db: Database connection
            notification_service: Optional notification service for alerts
            config: Optional configuration dictionary
            logger: Optional logger instance
        """
        self.db = db
        self.notification_service = notification_service
        self.logger = logger or logging.getLogger("db_monitor")

        # Default configuration
        self.config = {
            "monitoring_interval": 60,  # seconds
            "metrics_snapshot_interval": 300,  # 5 minutes
            "metrics_export_interval": 3600,  # 1 hour
            "metrics_retention_days": 7,
            "metrics_export_path": "./metrics/",
            "alert_thresholds": {
                "error_percent": 5.0,  # percentage of queries resulting in errors
                "slow_query_percent": 10.0,  # percentage of queries that are slow
                "avg_query_time_ms": 100.0,  # average query time
                "p95_query_time_ms": 500.0,  # 95th percentile query time
                "connection_usage_percent": 80.0,  # percentage of connection pool in use
                "connection_wait_time_ms": 100.0,  # average connection wait time
            },
        }

        # Override with provided config
        if config:
            self._update_config(config)

        # Create metrics collector
        self.metrics_collector = DatabaseMetricsCollector(db, logger)

        # Set collector thresholds from config
        if "alert_thresholds" in self.config:
            thresholds = self.config["alert_thresholds"]
            if "avg_query_time_ms" in thresholds:
                self.metrics_collector.slow_query_threshold_ms = float(
                    thresholds["avg_query_time_ms"]
                )

        self.metrics_collector.metrics_retention_days = self.config.get(
            "metrics_retention_days", 7
        )

        # Active alerts
        self.active_alerts: Dict[str, Dict[str, Any]] = {}

        # Alert history
        self.alert_history: List[Dict[str, Any]] = []

        # Monitoring status
        self.is_monitoring = False

        # Ensure export directory exists
        os.makedirs(self.config["metrics_export_path"], exist_ok=True)

    def _update_config(self, config: Dict[str, Any]) -> None:
        """Update configuration with provided values.

        Args:
            config: Configuration dictionary
        """
        for key, value in config.items():
            if key == "alert_thresholds" and isinstance(value, dict):
                self.config["alert_thresholds"].update(value)
            else:
                self.config[key] = value

    async def start_monitoring(self) -> None:
        """Start the database monitoring."""
        self.logger.info("Starting database monitoring")

        # Register hooks if enabled
        if self.config["hook_enabled"]:
            self.metrics_collector._register_db_hooks()

        # Start background monitoring tasks
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self.metrics_snapshot_loop())

        if self.config["export_interval"] > 0:
            asyncio.create_task(self.metrics_export_loop())

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while True:
            try:
                # Collect basic database metrics
                await self._collect_db_metrics()

                # Check alert thresholds
                await self._check_alert_thresholds()

            except Exception as e:
                self.logger.error("Error in database monitoring loop: %s", e)

            # Wait for next monitoring interval
            await asyncio.sleep(self.config["monitoring_interval"])

    async def _metrics_snapshot_loop(self) -> None:
        """Background metrics snapshot loop."""
        while True:
            try:
                # Take a snapshot of current metrics
                self.metrics_collector.record_metrics_snapshot()

            except Exception as e:
                self.logger.error("Error recording metrics snapshot: %s", e)

            # Wait for next snapshot interval
            await asyncio.sleep(self.config["metrics_snapshot_interval"])

    async def _metrics_export_loop(self) -> None:
        """Background metrics export loop."""
        while True:
            try:
                # Export metrics to file
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                export_path = os.path.join(
                    self.config["metrics_export_path"], f"db_metrics_{timestamp}.json"
                )

                self.metrics_collector.export_metrics(export_path)

            except Exception as e:
                self.logger.error("Error exporting metrics: %s", e)

            # Wait for next export interval
            await asyncio.sleep(self.config["metrics_export_interval"])

    async def _collect_db_metrics(self) -> None:
        """Collect database metrics."""
        try:
            # Collect connection pool stats
            pool_stats = await self._get_connection_pool_stats()

            # Collect query performance metrics
            if self.config["detailed_metrics"]:
                # Run test queries to measure performance
                await self._run_performance_test_queries()

            # Add to metrics collector
            self.metrics_collector.record_connection_event(
                "snapshot", wait_time_ms=pool_stats.get("avg_wait_time_ms", 0)
            )

        except Exception as e:
            self.logger.error("Error collecting database metrics: %s", e)

    async def _get_connection_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics.

        This is a placeholder that would be implemented based on the
        specific database driver and connection pool being used.

        Returns:
            Pool statistics
        """
        # Placeholder implementation
        try:
            # In a real implementation, this would query the connection pool
            # for its current statistics
            return {
                "size": 5,
                "max_size": 10,
                "overflow": 0,
                "max_overflow": 10,
                "timeout": 30,
                "in_use": 0,
                "available": 5,
                "avg_wait_time_ms": 0,
            }
        except Exception as e:
            self.logger.error("Error getting connection pool stats: %s", e)
            return {}

    async def _run_performance_test_queries(self) -> None:
        """Run test queries to measure database performance."""
        # Simple test query
        start_time = time.time()

        try:
            # Run a simple query
            await self.db.fetch_one("SELECT 1")
            execution_time = (time.time() - start_time) * 1000  # to ms

            # Record in metrics
            self.metrics_collector.record_query_execution(
                query="SELECT 1",
                params=None,
                execution_time_ms=execution_time,
                rows_affected=1,
                success=True,
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000  # to ms

            # Record error
            self.metrics_collector.record_query_execution(
                query="SELECT 1",
                params=None,
                execution_time_ms=execution_time,
                rows_affected=0,
                success=False,
                error_message=str(e),
            )

    async def _check_alert_thresholds(self) -> None:
        """Check if any alert thresholds have been exceeded."""
        try:
            # Get current metrics
            metrics = await self.get_metrics()

            # Get alert thresholds with safe access
            thresholds = self.config.get("alert_thresholds", {})

            # Active alerts for this check
            new_alerts = set()

            # Only check percentages if we have queries
            query_count = metrics.get("query_count", 0)
            if query_count > 0:
                # Check error percentage
                error_count = metrics.get("error_count", 0)
                error_percent = (error_count / max(query_count, 1)) * 100
                error_threshold = thresholds.get("error_percent", 100.0)

                if error_percent > error_threshold:
                    alert_id = "error_percent"
                    new_alerts.add(alert_id)

                    if alert_id not in self.active_alerts:
                        await self._trigger_alert(
                            "high_error_percentage",
                            f"Query error percentage ({error_percent:.2f}%) exceeds threshold ({error_threshold:.2f}%)",
                            "HIGH",
                            metrics,
                        )

                # Check slow query percentage
                slow_query_count = metrics.get("slow_query_count", 0)
                slow_query_percent = (slow_query_count / max(query_count, 1)) * 100
                slow_threshold = thresholds.get("slow_query_percent", 100.0)

                if slow_query_percent > slow_threshold:
                    alert_id = "slow_query_percent"
                    new_alerts.add(alert_id)

                    if alert_id not in self.active_alerts:
                        await self._trigger_alert(
                            "high_slow_query_percentage",
                            f"Slow query percentage ({slow_query_percent:.2f}%) exceeds threshold ({slow_threshold:.2f}%)",
                            "MEDIUM",
                            metrics,
                        )

            # Check average query time
            avg_query_time = metrics.get("avg_query_time_ms", 0.0)
            avg_time_threshold = thresholds.get("avg_query_time_ms", float("inf"))

            if avg_query_time > avg_time_threshold:
                alert_id = "avg_query_time"
                new_alerts.add(alert_id)

                if alert_id not in self.active_alerts:
                    await self._trigger_alert(
                        "high_avg_query_time",
                        f"Average query time ({avg_query_time:.2f}ms) exceeds threshold ({avg_time_threshold:.2f}ms)",
                        "MEDIUM",
                        metrics,
                    )

            # Check 95th percentile query time
            percentiles = metrics.get("percentiles", {})
            p95_time = percentiles.get("p95", 0.0)
            p95_threshold = thresholds.get("p95_query_time_ms", float("inf"))

            if p95_time > p95_threshold:
                alert_id = "p95_query_time"
                new_alerts.add(alert_id)

                if alert_id not in self.active_alerts:
                    await self._trigger_alert(
                        "high_p95_query_time",
                        f"95th percentile query time ({p95_time:.2f}ms) exceeds threshold ({p95_threshold:.2f}ms)",
                        "MEDIUM",
                        metrics,
                    )

            # Check connection pool usage
            connection_stats = metrics.get("connection_stats", {})
            peak_active = connection_stats.get("peak_active", 0)
            pool_size = 10  # This should come from actual pool config

            if peak_active > 0:
                connection_usage = (float(peak_active) / float(pool_size)) * 100.0
                usage_threshold = thresholds.get("connection_usage_percent", 100.0)

                if connection_usage > usage_threshold:
                    alert_id = "connection_usage"
                    new_alerts.add(alert_id)

                    if alert_id not in self.active_alerts:
                        await self._trigger_alert(
                            "high_connection_usage",
                            f"Connection usage ({peak_active}/{pool_size}, {connection_usage:.2f}%) exceeds threshold ({usage_threshold:.2f}%)",
                            "MEDIUM",
                            metrics,
                        )

            # Check connection wait time
            wait_time = connection_stats.get("avg_wait_time_ms", 0.0)
            wait_threshold = thresholds.get("connection_wait_time_ms", float("inf"))

            if wait_time > wait_threshold:
                alert_id = "connection_wait_time"
                new_alerts.add(alert_id)

                if alert_id not in self.active_alerts:
                    await self._trigger_alert(
                        "high_connection_wait_time",
                        f"Connection wait time ({wait_time:.2f}ms) exceeds threshold ({wait_threshold:.2f}ms)",
                        "HIGH",
                        metrics,
                    )

            # Check for resolved alerts
            resolved_alerts = set(self.active_alerts.keys()) - new_alerts
            for alert_id in resolved_alerts:
                alert = self.active_alerts[alert_id]
                await self._resolve_alert(alert_id, metrics)

        except Exception as e:
            self.logger.error("Error checking alert thresholds: %s", e)

    async def _trigger_alert(
        self, alert_type: str, message: str, priority: str, metrics: Dict[str, Any]
    ) -> None:
        """Trigger a database alert.

        Args:
            alert_type: Type of alert
            message: Alert message
            priority: Alert priority
            metrics: Current metrics
        """
        # Log the alert
        self.logger.warning("DATABASE ALERT: %s", message)

        # Record in alert history
        alert_record = {
            "type": alert_type,
            "message": message,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_snapshot": {
                "query_count": metrics["query_count"],
                "slow_query_count": metrics["slow_query_count"],
                "error_count": metrics["error_count"],
                "avg_query_time_ms": metrics["avg_query_time_ms"],
                "queries_per_second": metrics["queries_per_second"],
            },
        }

        self.alert_history.append(alert_record)

        # Keep only the last 100 alerts
        if len(self.alert_history) > 100:
            self.alert_history = self.alert_history[-100:]

        # Send notification if service is available
        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id=f"database_alert_{alert_type}",
                    category=NotificationCategory.SYSTEM_ALERT,
                    data={
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat(),
                        "component": "database",
                        "metrics": alert_record["metrics_snapshot"],
                    },
                    priority=priority,
                )
            except Exception as e:
                self.logger.error("Failed to send database alert: %s", e)

    async def _resolve_alert(self, alert_id: str, metrics: Dict[str, Any]) -> None:
        """Mark an alert as resolved.

        Args:
            alert_id: Alert ID
            metrics: Current metrics
        """
        # Generate resolution message based on alert ID
        message = f"Alert condition '{alert_id}' has been resolved"

        # Add specific details based on alert type
        if alert_id == "slow_query_percent":
            slow_query_percent = (
                (metrics["slow_query_count"] / metrics["query_count"]) * 100
                if metrics["query_count"] > 0
                else 0
            )
            message = f"Slow query percentage ({slow_query_percent:.2f}%) is now below threshold"

        elif alert_id == "error_percent":
            error_percent = (
                (metrics["error_count"] / metrics["query_count"]) * 100
                if metrics["query_count"] > 0
                else 0
            )
            message = (
                f"Query error percentage ({error_percent:.2f}%) is now below threshold"
            )

        elif alert_id == "avg_query_time":
            message = f"Average query time ({metrics['avg_query_time_ms']:.2f}ms) is now below threshold"

        elif alert_id == "p95_query_time" and "percentiles" in metrics:
            message = f"95th percentile query time ({metrics['percentiles']['p95']:.2f}ms) is now below threshold"

        # Log the resolution
        self.logger.info("DATABASE ALERT RESOLVED: %s", message)

        # Record in alert history
        resolution_record = {
            "type": f"{alert_id}_resolved",
            "message": message,
            "priority": NotificationPriority.LOW,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics_snapshot": {
                "query_count": metrics["query_count"],
                "slow_query_count": metrics["slow_query_count"],
                "error_count": metrics["error_count"],
                "avg_query_time_ms": metrics["avg_query_time_ms"],
                "queries_per_second": metrics["queries_per_second"],
            },
        }

        self.alert_history.append(resolution_record)

        # Send resolution notification if service is available
        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id="database_alert_resolved",
                    category=NotificationCategory.SYSTEM_INFO,
                    data={
                        "message": message,
                        "timestamp": datetime.utcnow().isoformat(),
                        "component": "database",
                        "metrics": resolution_record["metrics_snapshot"],
                    },
                    priority=NotificationPriority.LOW,
                )
            except Exception as e:
                self.logger.error("Failed to send alert resolution: %s", e)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get current database metrics.

        Returns:
            Current metrics
        """
        return self.metrics_collector.get_current_metrics()

    async def get_metrics_history(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get metrics history.

        Args:
            start_time: Optional start time
            end_time: Optional end time

        Returns:
            Metrics history
        """
        return self.metrics_collector.get_metrics_history(start_time, end_time)

    async def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get recent slow queries.

        Returns:
            List of slow queries
        """
        return self.metrics_collector.get_recent_slow_queries()

    async def get_errors(self) -> List[Dict[str, Any]]:
        """Get recent errors.

        Returns:
            List of errors
        """
        return self.metrics_collector.get_recent_errors()

    async def get_alerts(self) -> List[Dict[str, Any]]:
        """Get alert history.

        Returns:
            List of alerts
        """
        return self.alert_history

    async def export_metrics(self, file_path: str) -> None:
        """Export metrics to a file.

        Args:
            file_path: Path to save the metrics
        """
        self.metrics_collector.export_metrics(file_path)

    async def export_alerts(self, file_path: str) -> None:
        """Export alert history to a file.

        Args:
            file_path: Path to save the alerts
        """
        export_data = {
            "alerts": self.alert_history,
            "active_alerts": list(self.active_alerts),
            "export_time": datetime.utcnow().isoformat(),
        }

        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2)

        self.logger.info("Alerts exported to %s", file_path)

    async def _send_notification(self, template_id, message, category, data):
        """Send a notification if notification service is available."""
        if self.notification_service:
            try:
                await self.notification_service.send_notification(
                    user_id="system",
                    template_id=template_id,
                    category=NOTIFICATION_CATEGORY_SYSTEM_INFO,
                    data=data,
                )
            except Exception as e:
                self.logger.error("Error sending notification: %s", e)


# Factory function to create database monitor
async def setup_database_monitoring(
    db,
    notification_service: Optional[NotificationService] = None,
    config: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None,
) -> DatabaseMonitor:
    """
    Set up database monitoring.

    Args:
        db: Database connection
        notification_service: Optional notification service
        config: Optional configuration
        logger: Optional logger

    Returns:
        Configured database monitor
    """
    monitor = DatabaseMonitor(db, notification_service, config, logger)
    await monitor.start_monitoring()
    return monitor
