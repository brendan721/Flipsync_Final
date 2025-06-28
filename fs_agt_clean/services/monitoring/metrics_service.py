"""
Metrics service for storing and retrieving historical metrics data.

This service provides functionality for:
- Storing metrics data points to the database
- Retrieving historical metrics with time-based queries
- Managing metric thresholds and alerting
- Aggregating metrics data for dashboards
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.core.db.database import Database
from fs_agt_clean.database.models.metrics import (
    UnifiedAgentMetrics,
    AlertCategory,
    AlertLevel,
    AlertRecord,
    AlertSource,
    MetricCategory,
    MetricDataPoint,
    MetricThreshold,
    MetricType,
    SystemMetrics,
)


class MetricsService:
    """Service for managing historical metrics data."""

    def __init__(self, database: Database):
        """Initialize the metrics service.

        Args:
            database: Database instance for data operations
        """
        self.database = database
        self.logger = logging.getLogger(__name__)

    async def store_metric_data_point(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        category: MetricCategory = MetricCategory.SYSTEM,
        labels: Optional[Dict[str, str]] = None,
        agent_id: Optional[str] = None,
        service_name: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Store a single metric data point.

        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric
            category: Metric category
            labels: Optional labels/tags
            agent_id: Optional agent identifier
            service_name: Optional service name
            timestamp: Optional timestamp (defaults to now)

        Returns:
            ID of the stored metric data point
        """
        async with self.database.get_session_context() as session:
            metric = MetricDataPoint(
                name=name,
                value=value,
                type=metric_type,
                category=category,
                labels=labels,
                agent_id=agent_id,
                service_name=service_name,
                timestamp=timestamp or datetime.now(timezone.utc),
            )

            session.add(metric)
            await session.commit()
            await session.refresh(metric)

            self.logger.debug(f"Stored metric data point: {name}={value}")
            return str(metric.id)

    async def store_system_metrics(
        self,
        cpu_usage_percent: Optional[float] = None,
        memory_total_bytes: Optional[int] = None,
        memory_used_bytes: Optional[int] = None,
        memory_usage_percent: Optional[float] = None,
        disk_total_bytes: Optional[int] = None,
        disk_used_bytes: Optional[int] = None,
        disk_usage_percent: Optional[float] = None,
        network_bytes_sent: Optional[int] = None,
        network_bytes_received: Optional[int] = None,
        process_cpu_percent: Optional[float] = None,
        process_memory_percent: Optional[float] = None,
        process_memory_rss: Optional[int] = None,
        process_memory_vms: Optional[int] = None,
        process_num_threads: Optional[int] = None,
        process_num_fds: Optional[int] = None,
        hostname: Optional[str] = None,
        service_name: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Store system metrics snapshot.

        Args:
            Various system and process metrics

        Returns:
            ID of the stored system metrics record
        """
        async with self.database.get_session_context() as session:
            metrics = SystemMetrics(
                timestamp=timestamp or datetime.now(timezone.utc),
                cpu_usage_percent=cpu_usage_percent,
                memory_total_bytes=memory_total_bytes,
                memory_used_bytes=memory_used_bytes,
                memory_usage_percent=memory_usage_percent,
                disk_total_bytes=disk_total_bytes,
                disk_used_bytes=disk_used_bytes,
                disk_usage_percent=disk_usage_percent,
                network_bytes_sent=network_bytes_sent,
                network_bytes_received=network_bytes_received,
                process_cpu_percent=process_cpu_percent,
                process_memory_percent=process_memory_percent,
                process_memory_rss=process_memory_rss,
                process_memory_vms=process_memory_vms,
                process_num_threads=process_num_threads,
                process_num_fds=process_num_fds,
                hostname=hostname,
                service_name=service_name,
            )

            session.add(metrics)
            await session.commit()
            await session.refresh(metrics)

            self.logger.debug("Stored system metrics snapshot")
            return str(metrics.id)

    async def store_agent_metrics(
        self,
        agent_id: str,
        status: str,
        uptime_seconds: Optional[float] = None,
        error_count: int = 0,
        last_error_time: Optional[datetime] = None,
        last_success_time: Optional[datetime] = None,
        requests_total: Optional[int] = None,
        requests_success: Optional[int] = None,
        requests_failed: Optional[int] = None,
        avg_response_time_ms: Optional[float] = None,
        peak_response_time_ms: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None,
        memory_usage_percent: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """Store agent metrics.

        Args:
            agent_id: UnifiedAgent identifier
            status: UnifiedAgent status
            Various agent metrics

        Returns:
            ID of the stored agent metrics record
        """
        async with self.database.get_session_context() as session:
            metrics = UnifiedAgentMetrics(
                agent_id=agent_id,
                timestamp=timestamp or datetime.now(timezone.utc),
                status=status,
                uptime_seconds=uptime_seconds,
                error_count=error_count,
                last_error_time=last_error_time,
                last_success_time=last_success_time,
                requests_total=requests_total,
                requests_success=requests_success,
                requests_failed=requests_failed,
                avg_response_time_ms=avg_response_time_ms,
                peak_response_time_ms=peak_response_time_ms,
                cpu_usage_percent=cpu_usage_percent,
                memory_usage_percent=memory_usage_percent,
                agent_metadata=metadata,
            )

            session.add(metrics)
            await session.commit()
            await session.refresh(metrics)

            self.logger.debug(f"Stored agent metrics for {agent_id}")
            return str(metrics.id)

    async def get_metric_data_points(
        self,
        name: Optional[str] = None,
        category: Optional[MetricCategory] = None,
        agent_id: Optional[str] = None,
        service_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Retrieve metric data points with filtering.

        Args:
            name: Optional metric name filter
            category: Optional category filter
            agent_id: Optional agent ID filter
            service_name: Optional service name filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of results

        Returns:
            List of metric data points as dictionaries
        """
        async with self.database.get_session_context() as session:
            query = select(MetricDataPoint)

            # Apply filters
            conditions = []
            if name:
                conditions.append(MetricDataPoint.name == name)
            if category:
                conditions.append(MetricDataPoint.category == category)
            if agent_id:
                conditions.append(MetricDataPoint.agent_id == agent_id)
            if service_name:
                conditions.append(MetricDataPoint.service_name == service_name)
            if start_time:
                conditions.append(MetricDataPoint.timestamp >= start_time)
            if end_time:
                conditions.append(MetricDataPoint.timestamp <= end_time)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(MetricDataPoint.timestamp)).limit(limit)

            result = await session.execute(query)
            metrics = result.scalars().all()

            return [metric.to_dict() for metric in metrics]

    async def get_system_metrics_history(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        service_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve system metrics history.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter
            service_name: Optional service name filter
            limit: Maximum number of results

        Returns:
            List of system metrics as dictionaries
        """
        async with self.database.get_session_context() as session:
            query = select(SystemMetrics)

            conditions = []
            if start_time:
                conditions.append(SystemMetrics.timestamp >= start_time)
            if end_time:
                conditions.append(SystemMetrics.timestamp <= end_time)
            if service_name:
                conditions.append(SystemMetrics.service_name == service_name)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(SystemMetrics.timestamp)).limit(limit)

            result = await session.execute(query)
            metrics = result.scalars().all()

            return [metric.to_dict() for metric in metrics]

    async def get_agent_metrics_history(
        self,
        agent_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve agent metrics history.

        Args:
            agent_id: Optional agent ID filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of results

        Returns:
            List of agent metrics as dictionaries
        """
        async with self.database.get_session_context() as session:
            query = select(UnifiedAgentMetrics)

            conditions = []
            if agent_id:
                conditions.append(UnifiedAgentMetrics.agent_id == agent_id)
            if start_time:
                conditions.append(UnifiedAgentMetrics.timestamp >= start_time)
            if end_time:
                conditions.append(UnifiedAgentMetrics.timestamp <= end_time)

            if conditions:
                query = query.where(and_(*conditions))

            query = query.order_by(desc(UnifiedAgentMetrics.timestamp)).limit(limit)

            result = await session.execute(query)
            metrics = result.scalars().all()

            return [metric.to_dict() for metric in metrics]

    async def get_metrics_summary(
        self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get a summary of metrics for the specified time period.

        Args:
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            Dictionary containing metrics summary
        """
        if not start_time:
            start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now(timezone.utc)

        async with self.database.get_session_context() as session:
            # Get total metric data points
            metric_count_query = select(func.count(MetricDataPoint.id)).where(
                and_(
                    MetricDataPoint.timestamp >= start_time,
                    MetricDataPoint.timestamp <= end_time,
                )
            )
            metric_count_result = await session.execute(metric_count_query)
            total_metrics = metric_count_result.scalar() or 0

            # Get system metrics count
            system_count_query = select(func.count(SystemMetrics.id)).where(
                and_(
                    SystemMetrics.timestamp >= start_time,
                    SystemMetrics.timestamp <= end_time,
                )
            )
            system_count_result = await session.execute(system_count_query)
            system_metrics_count = system_count_result.scalar() or 0

            # Get agent metrics count
            agent_count_query = select(func.count(UnifiedAgentMetrics.id)).where(
                and_(
                    UnifiedAgentMetrics.timestamp >= start_time,
                    UnifiedAgentMetrics.timestamp <= end_time,
                )
            )
            agent_count_result = await session.execute(agent_count_query)
            agent_metrics_count = agent_count_result.scalar() or 0

            # Get unique agents
            unique_agents_query = select(
                func.count(func.distinct(UnifiedAgentMetrics.agent_id))
            ).where(
                and_(
                    UnifiedAgentMetrics.timestamp >= start_time,
                    UnifiedAgentMetrics.timestamp <= end_time,
                )
            )
            unique_agents_result = await session.execute(unique_agents_query)
            unique_agents = unique_agents_result.scalar() or 0

            return {
                "time_period": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration_hours": (end_time - start_time).total_seconds() / 3600,
                },
                "metrics": {
                    "total_data_points": total_metrics,
                    "system_metrics_snapshots": system_metrics_count,
                    "agent_metrics_snapshots": agent_metrics_count,
                    "unique_agents": unique_agents,
                },
            }
