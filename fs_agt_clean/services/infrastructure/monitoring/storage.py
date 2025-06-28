import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from fs_agt_clean.core.monitoring.metrics.models import MetricType
from fs_agt_clean.core.utils.config import get_settings

"\nMetrics storage and aggregation system.\nHandles persistent storage and aggregation of metrics data.\n"
logger: logging.Logger = logging.getLogger(__name__)


class MetricsStorage:
    """Handles storage and retrieval of metrics data."""

    def __init__(self):
        """Initialize metrics storage."""
        self.settings = get_settings()
        self.client = self._init_client()
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.bucket = self.settings.INFLUXDB_BUCKET
        self.org = self.settings.INFLUXDB_ORG

    def _init_client(self) -> InfluxDBClient:
        """Initialize InfluxDB client."""
        return InfluxDBClient(
            url=self.settings.INFLUXDB_URL,
            token=self.settings.INFLUXDB_TOKEN,
            org=self.settings.INFLUXDB_ORG,
        )

    async def store_metrics(
        self,
        metrics: Dict[str, float],
        metric_type: MetricType,
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Store metrics in InfluxDB.

        Args:
            metrics: Dictionary of metric names and values
            metric_type: Type of metrics
            labels: Optional metric labels
            timestamp: Optional timestamp (defaults to now)
        """
        try:
            timestamp = timestamp or datetime.utcnow()
            points = []
            for name, value in metrics.items():
                point = Point(name).field("value", value).tag("type", metric_type.value)
                if labels:
                    for key, val in labels.items():
                        point = point.tag(key, val)
                point = point.time(timestamp, WritePrecision.NS)
                points.append(point)
            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
        except Exception as e:
            logger.error("Failed to store metrics: %s", str(e))

    async def get_metrics(
        self,
        metric_names: List[str],
        start_time: datetime,
        end_time: Optional[datetime] = None,
        aggregation: Optional[str] = None,
        interval: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Query metrics from storage.

        Args:
            metric_names: List of metric names to query
            start_time: Start time for query
            end_time: Optional end time (defaults to now)
            aggregation: Optional aggregation function (mean, sum, etc.)
            interval: Optional time interval for aggregation

        Returns:
            DataFrame with metric data
        """
        try:
            end_time = end_time or datetime.utcnow()
            metric_list = '"|".join(metric_names)'
            query = f'\n                from(bucket: "{self.bucket}")\n                |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})\n                |> filter(fn: (r) => r["_measurement"] =~ /^({metric_list})$/)\n            '
            if aggregation and interval:
                query += f"\n                    |> aggregateWindow(\n                        every: {interval},\n                        fn: {aggregation},\n                        createEmpty: false\n                    )\n                "
            tables = self.query_api.query(query, org=self.org)
            return self._tables_to_dataframe(tables)
        except Exception as e:
            logger.error("Failed to query metrics: %s", str(e))
            return pd.DataFrame()

    async def get_latest_metrics(self, metric_names: List[str]) -> Dict[str, float]:
        """
        Get latest values for specified metrics.

        Args:
            metric_names: List of metric names

        Returns:
            Dictionary of metric names and their latest values
        """
        try:
            metric_list = '"|".join(metric_names)'
            query = f'\n                from(bucket: "{self.bucket}")\n                |> range(start: -1h)\n                |> filter(fn: (r) => r["_measurement"] =~ /^({metric_list})$/)\n                |> last()\n            '
            tables = self.query_api.query(query, org=self.org)
            result = {}
            for table in tables:
                for record in table.records:
                    result[record.get_measurement()] = record.get_value()
            return result
        except Exception as e:
            logger.error("Failed to get latest metrics: %s", str(e))
            return {}

    async def aggregate_metrics(
        self, metric_names: List[str], window: timedelta, aggregation: str = "mean"
    ) -> Dict[str, Dict[str, float]]:
        """
        Aggregate metrics over time window.

        Args:
            metric_names: List of metric names
            window: Time window for aggregation
            aggregation: Aggregation function to use

        Returns:
            Dictionary of aggregated metrics
        """
        try:
            start_time = datetime.utcnow() - window
            metric_list = '"|".join(metric_names)'
            query = f'\n                from(bucket: "{self.bucket}")\n                |> range(start: {start_time.isoformat()})\n                |> filter(fn: (r) => r["_measurement"] =~ /^({metric_list})$/)\n                |> aggregateWindow(\n                    every: {int(window.total_seconds())}s,\n                    fn: {aggregation},\n                    createEmpty: false\n                )\n            '
            tables = self.query_api.query(query, org=self.org)
            result = {}
            for table in tables:
                metric_name = table.records[0].get_measurement()
                result[metric_name] = {
                    "value": table.records[0].get_value(),
                    "timestamp": table.records[0].get_time(),
                }
            return result
        except Exception as e:
            logger.error("Failed to aggregate metrics: %s", str(e))
            return {}

    def _tables_to_dataframe(self, tables: List[Any]) -> pd.DataFrame:
        """Convert InfluxDB tables to pandas DataFrame."""
        records = []
        for table in tables:
            for record in table.records:
                records.append(
                    {
                        "metric": record.get_measurement(),
                        "value": record.get_value(),
                        "timestamp": record.get_time(),
                        **record.values,
                    }
                )
        if not records:
            return pd.DataFrame()
        df = pd.DataFrame.from_records(records)
        df.set_index("timestamp", inplace=True)
        return df

    async def cleanup(self) -> None:
        """Clean up resources."""
        try:
            self.client.close()
        except Exception as e:
            logger.error("Error closing InfluxDB client: %s", str(e))


class MetricsAggregator:
    """Handles real-time aggregation of metrics."""

    def __init__(self, window_size: int = 300):
        """
        Initialize aggregator.

        Args:
            window_size: Window size in seconds for aggregation
        """
        self.window_size = window_size
        self.metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._lock = asyncio.Lock()

    async def add_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Add a metric value for aggregation.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            timestamp: Optional timestamp
        """
        async with self._lock:
            if name not in self.metrics:
                self.metrics[name] = []
            self.metrics[name].append(
                {
                    "value": value,
                    "type": metric_type,
                    "timestamp": timestamp or datetime.utcnow(),
                }
            )
            await self._cleanup_old_values(name)

    async def get_aggregates(
        self, name: str, aggregation: str = "mean"
    ) -> Optional[float]:
        """
        Get aggregated value for a metric.

        Args:
            name: Metric name
            aggregation: Aggregation function

        Returns:
            Aggregated value if available
        """
        async with self._lock:
            if name not in self.metrics or not self.metrics[name]:
                return None
            values = [m["value"] for m in self.metrics[name]]
            if aggregation == "mean":
                return sum(values) / len(values)
            elif aggregation == "sum":
                return sum(values)
            elif aggregation == "min":
                return min(values)
            elif aggregation == "max":
                return max(values)
            else:
                raise ValueError(f"Unknown aggregation: {aggregation}")

    async def _cleanup_old_values(self, name: str) -> None:
        """Clean up values outside the window."""
        if name not in self.metrics:
            return
        cutoff = datetime.utcnow() - timedelta(seconds=self.window_size)
        self.metrics[name] = [m for m in self.metrics[name] if m["timestamp"] > cutoff]
