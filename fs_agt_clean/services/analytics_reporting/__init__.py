"""
Analytics and Business Intelligence Services.

This module provides comprehensive analytics and reporting capabilities including:
- Campaign analytics and performance tracking
- Inventory metrics and monitoring
- Business intelligence reporting
- Real-time metrics collection
- InfluxDB integration for time-series data
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Import analytics components
try:
    from .analytics_service import AnalyticsService
except ImportError:
    AnalyticsService = None

try:
    from .analytics_engine import AnalyticsEngine
except ImportError:
    AnalyticsEngine = None

try:
    from .inventory_metrics import InventoryMetrics
except ImportError:
    InventoryMetrics = None

try:
    from .service import MetricsService
except ImportError:
    MetricsService = None

try:
    from .influxdb_service import InfluxDBService
except ImportError:
    InfluxDBService = None

try:
    from .error_handler import ErrorHandler
except ImportError:
    ErrorHandler = None

try:
    from .models import (
        AnalyticsReport,
        CampaignAnalytics,
        PerformanceMetrics,
    )
except ImportError:
    CampaignAnalytics = None
    PerformanceMetrics = None
    AnalyticsReport = None


class AnalyticsReportingService:
    """Main service for analytics and business intelligence."""

    def __init__(self, config_manager=None, influxdb_config=None):
        """Initialize the analytics reporting service."""
        self.config_manager = config_manager

        # Initialize components
        self.analytics_service = AnalyticsService() if AnalyticsService else None
        self.analytics_engine = AnalyticsEngine() if AnalyticsEngine else None
        self.inventory_metrics = InventoryMetrics() if InventoryMetrics else None
        self.metrics_service = MetricsService() if MetricsService else None
        self.influxdb_service = (
            InfluxDBService(influxdb_config)
            if InfluxDBService and influxdb_config
            else None
        )
        self.error_handler = ErrorHandler() if ErrorHandler else None

    async def track_campaign_performance(self, campaign_id: str, metrics: Dict) -> bool:
        """Track campaign performance metrics."""
        try:
            if self.analytics_engine:
                return await self.analytics_engine.track_campaign(campaign_id, metrics)
            return False
        except Exception as e:
            logger.error("Failed to track campaign performance: %s", str(e))
            return False

    async def generate_analytics_report(
        self, report_type: str, date_range: Dict, filters: Optional[Dict] = None
    ) -> Dict:
        """Generate comprehensive analytics report."""
        try:
            if self.analytics_service:
                return await self.analytics_service.generate_report(
                    report_type, date_range, filters
                )
            return {}
        except Exception as e:
            logger.error("Failed to generate analytics report: %s", str(e))
            return {}

    async def get_inventory_metrics(self) -> Dict:
        """Get current inventory metrics."""
        try:
            if self.inventory_metrics:
                return await self.inventory_metrics.get_current_metrics()
            return {}
        except Exception as e:
            logger.error("Failed to get inventory metrics: %s", str(e))
            return {}

    async def record_metric(
        self, metric_name: str, value: float, tags: Optional[Dict] = None
    ) -> bool:
        """Record a metric value."""
        try:
            if self.metrics_service:
                return await self.metrics_service.record(metric_name, value, tags)
            return False
        except Exception as e:
            logger.error("Failed to record metric: %s", str(e))
            return False


__all__ = [
    "AnalyticsReportingService",
    "AnalyticsService",
    "AnalyticsEngine",
    "InventoryMetrics",
    "MetricsService",
    "InfluxDBService",
    "ErrorHandler",
    "CampaignAnalytics",
    "PerformanceMetrics",
    "AnalyticsReport",
]
