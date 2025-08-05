"""
Compatibility module for the Metrics Service.

This module provides a compatibility layer for transitioning from the mock
implementation to the real implementation of the Metrics Service.
"""

import logging
from typing import Optional

from fs_agt_clean.core.config.manager import ConfigManager, get_config_manager
from fs_agt_clean.core.db.database import Database, get_database
from fs_agt_clean.services.metrics.service import MetricsService

logger = logging.getLogger(__name__)


class MetricsServiceCompat:
    """Compatibility wrapper for MetricsService implementations.

    This class provides a unified interface that works with both the core
    MetricsService and the service-specific MetricsService.
    """

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        database: Optional[Database] = None,
        **kwargs,
    ):
        """Initialize the compatibility wrapper.

        Args:
            config_manager: Optional configuration manager
            database: Optional database instance
            **kwargs: Additional keyword arguments for specific implementations
        """
        # Get default instances if not provided
        if not config_manager:
            config_manager = get_config_manager()
        if not database:
            database = get_database()

        # Use the real MetricsService implementation
        self._service = MetricsService(
            config_manager=config_manager,
            database=database,
        )
        logger.debug("Using real database-backed MetricsService")

    async def increment_counter(self, name, value=1.0, labels=None):
        """Increment a counter metric."""
        return await self._service.increment_counter(name, value, labels)

    async def record_metric(self, name, value, labels=None):
        """Record a metric value."""
        return await self._service.record_metric(name, value, labels=labels)

    async def record_operation_duration(self, operation_type, duration):
        """Record duration of a document operation."""
        return await self._service.record_operation_duration(operation_type, duration)

    async def record_operation_error(self, operation_type, error_type):
        """Record a document operation error."""
        return await self._service.record_operation_error(operation_type, error_type)

    async def record_search_duration(self, query_type, duration):
        """Record duration of a search operation."""
        return await self._service.record_search_duration(query_type, duration)

    async def get_metrics(self, **kwargs):
        """Get metrics with optional filtering."""
        return await self._service.get_metrics(**kwargs)

    async def get_aggregations(self, **kwargs):
        """Get metric aggregations with optional filtering."""
        return await self._service.get_aggregations(**kwargs)

    async def get_metric_series(self, name, **kwargs):
        """Get a time series for a specific metric."""
        return await self._service.get_metric_series(name, **kwargs)

    def __getattr__(self, name):
        """Forward attribute access to the underlying service."""
        return getattr(self._service, name)


# Create a type alias for compatibility
MetricsService = MetricsServiceCompat


# Singleton instance
_metrics_service_instance = None


def get_metrics_service(
    config_manager: Optional[ConfigManager] = None,
    database: Optional[Database] = None,
) -> MetricsService:
    """Get a singleton instance of the MetricsService.

    Args:
        config_manager: Optional ConfigManager instance
        database: Optional Database instance

    Returns:
        MetricsService instance
    """
    global _metrics_service_instance
    if _metrics_service_instance is None:
        _metrics_service_instance = MetricsService(
            config_manager=config_manager,
            database=database,
        )
    return _metrics_service_instance
