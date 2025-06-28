"""InfluxDB service for storing metrics data."""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from influxdb_client import InfluxDBClient, Point, WriteOptions
from influxdb_client.client.write_api import SYNCHRONOUS, WriteType
from influxdb_client.domain.write_precision import WritePrecision

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.monitoring.models import MetricCategory, MetricType, MetricUpdate

logger = logging.getLogger(__name__)


class InfluxDBService:
    """Service for managing InfluxDB operations."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize InfluxDB service.

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager.get("influxdb", {})

        # Configure write options
        self.write_options = WriteOptions(
            write_type=WriteType.synchronous,
            batch_size=self.config.get("batch_size", 1000),
            flush_interval=self.config.get("flush_interval", 1000),
            jitter_interval=0,
            retry_interval=5_000,
            max_retries=5,
            max_retry_delay=125_000,
            exponential_base=2,
        )

        # Get InfluxDB URL from environment variable or fallback to config
        self.url = os.getenv("INFLUXDB_URL") or self.config.get(
            "url", "http://localhost:8086"
        )
        self.token = os.getenv("INFLUXDB_TOKEN") or self.config.get("token")
        self.org = os.getenv("INFLUXDB_ORG") or self.config.get("org")
        self.bucket = os.getenv("INFLUXDB_BUCKET") or self.config.get(
            "bucket", "metrics"
        )

        if not self.token:
            raise ValueError("InfluxDB token must be provided")
        if not self.org:
            raise ValueError("InfluxDB organization must be provided")

        # Initialize client and APIs with version-specific options
        try:
            self.client = InfluxDBClient(
                url=self.url,
                token=self.token,
                org=self.org,
                enable_gzip=True,
                verify_ssl=self.config.get("verify_ssl", True),
                timeout=self.config.get("timeout", 10000),
                debug=self.config.get("log_level", "info") == "debug",
                connection_pool_maxsize=self.config.get("connection_pool_maxsize", 25),
                auth_basic=self.config.get("auth_basic", False),
                proxy=self.config.get("proxy", None),
                retries=self.config.get("retries", 3),
            )
            self._write_api = self.client.write_api(write_options=self.write_options)
            self._query_api = self.client.query_api()
            self._delete_api = self.client.delete_api()
            logger.info(
                "Successfully initialized InfluxDB client %s with Python %s",
                self.client.version,
                sys.version,
            )

        except Exception as e:
            logger.error(
                "Failed to initialize InfluxDB client: %s", str(e), exc_info=True
            )

            raise

    async def store_metric(self, metric: MetricUpdate) -> bool:
        """Store a metric in InfluxDB.

        Args:
            metric: Metric to store

        Returns:
            bool indicating success
        """
        try:
            point = (
                Point("metrics")
                .tag("type", metric.metric_type.value)
                .tag("category", metric.category.value)
                .tag("name", metric.name)
            )

            # Add custom labels as tags
            for key, value in metric.labels.items():
                point = point.tag(key, str(value))

            # Handle different value types
            if isinstance(metric.value, (int, float)):
                point = point.field("value", float(metric.value))
            elif isinstance(metric.value, dict):
                for key, val in metric.value.items():
                    point = point.field(key, float(val))
            else:
                logger.warning("Unsupported metric value type: %s", type(metric.value))
                return bool(False)

            # Add timestamp with nanosecond precision
            point = point.time(metric.timestamp)

            self._write_api.write(
                bucket=self.bucket, record=point, write_precision=WritePrecision.NS
            )
            return True

        except Exception as e:
            logger.error("Error storing metric: %s", str(e), exc_info=True)
            return False

    async def query_metrics(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        metric_type: Optional[MetricType] = None,
        category: Optional[MetricCategory] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Query metrics from InfluxDB.

        Args:
            start_time: Start time for query
            end_time: Optional end time for query
            metric_type: Optional metric type filter
            category: Optional category filter
            labels: Optional labels to filter by

        Returns:
            List of metrics matching the query
        """
        try:
            # Build Flux query with optimized filtering
            query = f"""
                from(bucket: "{self.bucket}")
                    |> range(start: {start_time.isoformat()}Z{f", stop: {end_time.isoformat()}Z" if end_time else ""})
                    |> filter(fn: (r) => r["_measurement"] == "metrics")
            """

            # Add filters using optimized Flux syntax
            if metric_type:
                query += f' |> filter(fn: (r) => r["type"] == "{metric_type.value}")'
            if category:
                query += f' |> filter(fn: (r) => r["category"] == "{category.value}")'
            if labels:
                for key, value in labels.items():
                    query += f' |> filter(fn: (r) => r["{key}"] == "{value}")'

            # Add optimizations for large datasets
            query += """
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: true)
            """

            # Execute query with timeout
            tables = self._query_api.query(
                query=query,
                org=self.org,
                params={"now": datetime.utcnow().isoformat()},
            )

            # Process results efficiently
            metrics = []
            for table in tables:
                for record in table.records:
                    metric = {
                        "timestamp": record.get_time(),
                        "value": record.get_value(),
                        "type": record.values.get("type"),
                        "category": record.values.get("category"),
                        "name": record.values.get("name"),
                        "labels": {
                            k: v
                            for k, v in record.values.items()
                            if k
                            not in [
                                "_time",
                                "_value",
                                "_field",
                                "_measurement",
                                "type",
                                "category",
                                "name",
                            ]
                        },
                    }
                    metrics.append(metric)

            return metrics

        except Exception as e:
            logger.error("Error querying metrics: %s", str(e), exc_info=True)
            return []

    async def get_metric_statistics(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        aggregation: str = "mean",
    ) -> Dict[str, Any]:
        """Get statistics for a metric.

        Args:
            metric_name: Name of the metric
            start_time: Start time for statistics
            end_time: Optional end time for statistics
            aggregation: Aggregation function to use (mean, min, max, sum)

        Returns:
            Dictionary containing metric statistics
        """
        try:
            # Build optimized Flux query for statistics
            query = f"""
                from(bucket: "{self.bucket}")
                    |> range(start: {start_time.isoformat()}Z{f", stop: {end_time.isoformat()}Z" if end_time else ""})
                    |> filter(fn: (r) => r["_measurement"] == "metrics" and r["name"] == "{metric_name}")
                    |> filter(fn: (r) => r["_field"] == "value")
                    |> {aggregation}()
                    |> yield(name: "last")
            """

            # Execute query with timeout
            tables = self._query_api.query(
                query=query,
                org=self.org,
                params={"now": datetime.utcnow().isoformat()},
            )

            # Process results
            stats = {
                "metric": metric_name,
                "aggregation": aggregation,
                "start_time": start_time,
                "end_time": end_time or datetime.now(),
                "value": None,
            }

            for table in tables:
                for record in table.records:
                    stats["value"] = record.get_value()
                    break

            return stats

        except Exception as e:
            logger.error("Error getting metric statistics: %s", str(e), exc_info=True)
            return {"metric": metric_name, "error": str(e)}

    async def delete_metrics(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        predicate: Optional[str] = None,
    ) -> bool:
        """Delete metrics within a time range.

        Args:
            start_time: Start time for deletion
            end_time: Optional end time for deletion
            predicate: Optional predicate for filtering metrics to delete

        Returns:
            bool indicating success
        """
        try:
            self._delete_api.delete(
                start=start_time,
                stop=end_time if end_time else "",
                predicate=predicate if predicate else "",
                bucket=self.bucket,
                org=self.org,
            )
            return True
        except Exception as e:
            logger.error("Error deleting metrics: %s", str(e), exc_info=True)
            return False

    async def close(self) -> None:
        """Close InfluxDB connection."""
        try:
            if self._write_api:
                self._write_api.close()
            if self.client:
                self.client.close()
            logger.info("Closed InfluxDB connection")
        except Exception as e:
            logger.error("Error closing InfluxDB connection: %s", str(e), exc_info=True)
