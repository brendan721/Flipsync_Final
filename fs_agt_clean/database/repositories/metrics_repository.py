"""
Metrics Repository for FlipSync Database Operations
=================================================

Repository classes for managing metrics, metric series, and metric aggregations
in the FlipSync database. Provides CRUD operations and specialized queries.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.database.base_repository import BaseRepository
from fs_agt_clean.database.models import (
    Metric,
    MetricAggregation,
    MetricCategory,
    MetricSeries,
    MetricType,
)

logger = logging.getLogger(__name__)


class MetricRepository(BaseRepository[Metric]):
    """Repository for managing Metric entities."""

    def __init__(self, session: AsyncSession):
        """Initialize metric repository."""
        super().__init__(session, Metric)

    async def get_by_name(self, name: str) -> Optional[Metric]:
        """Get metric by name."""
        try:
            result = await self.session.execute(
                select(Metric).where(Metric.name == name)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting metric by name {name}: {e}")
            return None

    async def get_by_category(self, category: MetricCategory) -> List[Metric]:
        """Get metrics by category."""
        try:
            result = await self.session.execute(
                select(Metric).where(Metric.category == category)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting metrics by category {category}: {e}")
            return []

    async def get_by_type(self, metric_type: MetricType) -> List[Metric]:
        """Get metrics by type."""
        try:
            result = await self.session.execute(
                select(Metric).where(Metric.metric_type == metric_type)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting metrics by type {metric_type}: {e}")
            return []


class MetricSeriesRepository(BaseRepository[MetricSeries]):
    """Repository for managing MetricSeries entities."""

    def __init__(self, session: AsyncSession):
        """Initialize metric series repository."""
        super().__init__(session, MetricSeries)

    async def get_by_metric_id(
        self,
        metric_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[MetricSeries]:
        """Get metric series data by metric ID with optional time range."""
        try:
            query = select(MetricSeries).where(MetricSeries.metric_id == metric_id)

            if start_time:
                query = query.where(MetricSeries.timestamp >= start_time)
            if end_time:
                query = query.where(MetricSeries.timestamp <= end_time)

            query = query.order_by(desc(MetricSeries.timestamp))

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting metric series for metric {metric_id}: {e}")
            return []

    async def get_latest_value(self, metric_id: UUID) -> Optional[MetricSeries]:
        """Get the latest metric value for a metric."""
        try:
            result = await self.session.execute(
                select(MetricSeries)
                .where(MetricSeries.metric_id == metric_id)
                .order_by(desc(MetricSeries.timestamp))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting latest value for metric {metric_id}: {e}")
            return None

    async def get_time_range_data(
        self, metric_id: UUID, start_time: datetime, end_time: datetime
    ) -> List[MetricSeries]:
        """Get metric data within a specific time range."""
        try:
            result = await self.session.execute(
                select(MetricSeries)
                .where(
                    and_(
                        MetricSeries.metric_id == metric_id,
                        MetricSeries.timestamp >= start_time,
                        MetricSeries.timestamp <= end_time,
                    )
                )
                .order_by(MetricSeries.timestamp)
            )
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting time range data for metric {metric_id}: {e}")
            return []


class MetricAggregationRepository(BaseRepository[MetricAggregation]):
    """Repository for managing MetricAggregation entities."""

    def __init__(self, session: AsyncSession):
        """Initialize metric aggregation repository."""
        super().__init__(session, MetricAggregation)

    async def get_by_metric_and_window(
        self,
        metric_id: UUID,
        time_window: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[MetricAggregation]:
        """Get aggregations by metric ID and time window."""
        try:
            query = select(MetricAggregation).where(
                and_(
                    MetricAggregation.metric_id == metric_id,
                    MetricAggregation.time_window == time_window,
                )
            )

            if start_time:
                query = query.where(MetricAggregation.start_time >= start_time)
            if end_time:
                query = query.where(MetricAggregation.end_time <= end_time)

            query = query.order_by(desc(MetricAggregation.start_time))

            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting aggregations for metric {metric_id}: {e}")
            return []

    async def get_latest_aggregation(
        self, metric_id: UUID, aggregation_type: str, time_window: str
    ) -> Optional[MetricAggregation]:
        """Get the latest aggregation for a metric."""
        try:
            result = await self.session.execute(
                select(MetricAggregation)
                .where(
                    and_(
                        MetricAggregation.metric_id == metric_id,
                        MetricAggregation.aggregation_type == aggregation_type,
                        MetricAggregation.time_window == time_window,
                    )
                )
                .order_by(desc(MetricAggregation.start_time))
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error getting latest aggregation for metric {metric_id}: {e}"
            )
            return None

    async def get_aggregation_summary(
        self,
        metric_id: UUID,
        aggregation_type: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """Get aggregation summary statistics."""
        try:
            result = await self.session.execute(
                select(
                    func.count(MetricAggregation.id).label("count"),
                    func.avg(MetricAggregation.value).label("avg_value"),
                    func.min(MetricAggregation.value).label("min_value"),
                    func.max(MetricAggregation.value).label("max_value"),
                    func.sum(MetricAggregation.sample_count).label("total_samples"),
                ).where(
                    and_(
                        MetricAggregation.metric_id == metric_id,
                        MetricAggregation.aggregation_type == aggregation_type,
                        MetricAggregation.start_time >= start_time,
                        MetricAggregation.end_time <= end_time,
                    )
                )
            )

            row = result.first()
            if row:
                return {
                    "count": row.count or 0,
                    "avg_value": float(row.avg_value) if row.avg_value else 0.0,
                    "min_value": float(row.min_value) if row.min_value else 0.0,
                    "max_value": float(row.max_value) if row.max_value else 0.0,
                    "total_samples": row.total_samples or 0,
                }
            return {}
        except Exception as e:
            logger.error(
                f"Error getting aggregation summary for metric {metric_id}: {e}"
            )
            return {}
