"""
System Health Dashboard Module for FlipSync Monitoring System

This module defines the system health dashboards including infrastructure,
service-level, and resource utilization visualizations.
"""

import datetime
import json
from typing import Dict, List, Optional, Union


class DashboardPanel:
    """Base class for dashboard panels."""

    def __init__(
        self,
        title: str,
        description: str,
        panel_type: str,
        width: int = 6,
        height: int = 4,
        refresh_interval_seconds: int = 60,
        data_source: Optional[str] = None,
    ):
        self.title = title
        self.description = description
        self.panel_type = panel_type
        self.width = width
        self.height = height
        self.refresh_interval_seconds = refresh_interval_seconds
        self.data_source = data_source
        self.id = None  # Set when added to dashboard

    def to_json(self) -> Dict:
        """Convert panel to JSON representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "type": self.panel_type,
            "width": self.width,
            "height": self.height,
            "refreshInterval": self.refresh_interval_seconds,
            "data_source": self.data_source,
        }


class MetricsPanel(DashboardPanel):
    """Panel for displaying metrics data."""

    def __init__(
        self,
        title: str,
        description: str,
        metrics: List[str],
        visualization: str = "line",  # line, bar, area, gauge
        width: int = 6,
        height: int = 4,
        refresh_interval_seconds: int = 60,
        time_range_minutes: int = 60,
        stacked: bool = False,
        thresholds: Optional[List[Dict]] = None,
        data_source: Optional[str] = None,
    ):
        super().__init__(
            title,
            description,
            "metrics",
            width,
            height,
            refresh_interval_seconds,
            data_source=data_source,
        )
        self.metrics = metrics
        self.visualization = visualization
        self.time_range_minutes = time_range_minutes
        self.stacked = stacked
        self.thresholds = thresholds or []

    def to_json(self) -> Dict:
        """Convert metrics panel to JSON representation."""
        json_data = super().to_json()
        json_data.update(
            {
                "metrics": self.metrics,
                "visualization": self.visualization,
                "timeRange": self.time_range_minutes,
                "stacked": self.stacked,
                "thresholds": self.thresholds,
            }
        )
        return json_data


class LogPanel(DashboardPanel):
    """Panel for displaying log data."""

    def __init__(
        self,
        title: str,
        description: str,
        log_query: str,
        width: int = 12,
        height: int = 6,
        refresh_interval_seconds: int = 30,
        time_range_minutes: int = 30,
        max_entries: int = 100,
        data_source: Optional[str] = None,
    ):
        super().__init__(
            title,
            description,
            "logs",
            width,
            height,
            refresh_interval_seconds,
            data_source=data_source,
        )
        self.log_query = log_query
        self.time_range_minutes = time_range_minutes
        self.max_entries = max_entries

    def to_json(self) -> Dict:
        """Convert log panel to JSON representation."""
        json_data = super().to_json()
        json_data.update(
            {
                "logQuery": self.log_query,
                "timeRange": self.time_range_minutes,
                "maxEntries": self.max_entries,
            }
        )
        return json_data


class StatusPanel(DashboardPanel):
    """Panel for displaying status information."""

    def __init__(
        self,
        title: str,
        description: str,
        status_items: List[Dict],
        width: int = 4,
        height: int = 4,
        refresh_interval_seconds: int = 60,
        data_source: Optional[str] = None,
    ):
        super().__init__(
            title,
            description,
            "status",
            width,
            height,
            refresh_interval_seconds,
            data_source=data_source,
        )
        self.status_items = status_items

    def to_json(self) -> Dict:
        """Convert status panel to JSON representation."""
        json_data = super().to_json()
        json_data.update({"statusItems": self.status_items})
        return json_data


class AlertPanel(DashboardPanel):
    """Panel for displaying alerts."""

    def __init__(
        self,
        title: str,
        description: str,
        alert_query: str,
        width: int = 6,
        height: int = 4,
        refresh_interval_seconds: int = 30,
        time_range_minutes: int = 60,
        group_by: Optional[str] = None,
        data_source: Optional[str] = None,
    ):
        super().__init__(
            title,
            description,
            "alerts",
            width,
            height,
            refresh_interval_seconds,
            data_source=data_source,
        )
        self.alert_query = alert_query
        self.time_range_minutes = time_range_minutes
        self.group_by = group_by

    def to_json(self) -> Dict:
        """Convert alert panel to JSON representation."""
        json_data = super().to_json()
        json_data.update(
            {
                "alertQuery": self.alert_query,
                "timeRange": self.time_range_minutes,
                "groupBy": self.group_by,
            }
        )
        return json_data


class Dashboard:
    """Dashboard containing multiple panels."""

    def __init__(
        self,
        name: str,
        description: str,
        category: str,
        refresh_interval_seconds: int = 60,
        time_range_minutes: int = 60,
        auto_refresh: bool = True,
    ):
        self.name = name
        self.description = description
        self.category = category
        self.refresh_interval_seconds = refresh_interval_seconds
        self.time_range_minutes = time_range_minutes
        self.auto_refresh = auto_refresh
        self.panels = []
        self.next_panel_id = 1

    def add_panel(self, panel: DashboardPanel) -> None:
        """Add a panel to the dashboard."""
        panel.id = self.next_panel_id
        self.panels.append(panel)
        self.next_panel_id += 1

    def to_json(self) -> Dict:
        """Convert dashboard to JSON representation."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "refreshInterval": self.refresh_interval_seconds,
            "timeRange": self.time_range_minutes,
            "autoRefresh": self.auto_refresh,
            "panels": [panel.to_json() for panel in self.panels],
        }

    def to_json_string(self) -> str:
        """Convert dashboard to JSON string."""
        return json.dumps(self.to_json(), indent=2)


# System Health Dashboard Definitions


def create_infrastructure_dashboard() -> Dashboard:
    """Create infrastructure health dashboard."""
    dashboard = Dashboard(
        name="Infrastructure Health",
        description="Overview of infrastructure health and resource utilization",
        category="System Health",
        refresh_interval_seconds=60,
        time_range_minutes=60,
        auto_refresh=True,
    )

    # CPU Utilization Panel
    dashboard.add_panel(
        MetricsPanel(
            title="CPU Utilization",
            description="CPU utilization across all services",
            metrics=["system.cpu.user", "system.cpu.system", "system.cpu.idle"],
            visualization="area",
            width=6,
            height=4,
            stacked=True,
            thresholds=[
                {"value": 80, "color": "yellow", "label": "Warning"},
                {"value": 90, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Memory Utilization Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Memory Utilization",
            description="Memory utilization across all services",
            metrics=[
                "system.memory.used",
                "system.memory.cached",
                "system.memory.free",
            ],
            visualization="area",
            width=6,
            height=4,
            stacked=True,
            thresholds=[
                {"value": 85, "color": "yellow", "label": "Warning"},
                {"value": 95, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Disk Utilization Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Disk Utilization",
            description="Disk utilization across all services",
            metrics=["system.disk.used_percent"],
            visualization="gauge",
            width=4,
            height=4,
            thresholds=[
                {"value": 80, "color": "yellow", "label": "Warning"},
                {"value": 90, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Network Traffic Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Network Traffic",
            description="Network traffic across all services",
            metrics=["system.network.in_bytes", "system.network.out_bytes"],
            visualization="line",
            width=8,
            height=4,
        )
    )

    # System Errors Panel
    dashboard.add_panel(
        LogPanel(
            title="System Errors",
            description="Recent system errors",
            log_query="level:error OR level:critical",
            width=12,
            height=6,
            refresh_interval_seconds=30,
            time_range_minutes=30,
            max_entries=100,
        )
    )

    # Service Status Panel
    dashboard.add_panel(
        StatusPanel(
            title="Service Status",
            description="Current status of all services",
            status_items=[
                {"name": "API Gateway", "metric": "service.api_gateway.health"},
                {"name": "Database", "metric": "service.database.health"},
                {"name": "UnifiedAgent Service", "metric": "service.agent.health"},
                {"name": "Authentication", "metric": "service.auth.health"},
                {"name": "Storage", "metric": "service.storage.health"},
            ],
            width=4,
            height=6,
        )
    )

    # Active Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="Active Alerts",
            description="Currently active infrastructure alerts",
            alert_query="category:infrastructure",
            width=8,
            height=6,
            refresh_interval_seconds=30,
            time_range_minutes=60,
            group_by="severity",
        )
    )

    return dashboard


def create_service_level_dashboard() -> Dashboard:
    """Create service level health dashboard."""
    dashboard = Dashboard(
        name="Service Level Health",
        description="Overview of service level metrics and health indicators",
        category="System Health",
        refresh_interval_seconds=60,
        time_range_minutes=60,
        auto_refresh=True,
    )

    # API Request Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="API Request Rate",
            description="Request rate across all API endpoints",
            metrics=["api.request.rate"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # API Latency Panel
    dashboard.add_panel(
        MetricsPanel(
            title="API Latency",
            description="Latency across all API endpoints",
            metrics=["api.latency.p50", "api.latency.p95", "api.latency.p99"],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 1000, "color": "yellow", "label": "Warning"},
                {"value": 2000, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Error Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Error Rate",
            description="Error rate across all services",
            metrics=["api.error.rate"],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 1, "color": "yellow", "label": "Warning"},
                {"value": 5, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Database Query Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Database Query Rate",
            description="Query rate across all database instances",
            metrics=["database.query.rate"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Database Latency Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Database Latency",
            description="Latency across all database queries",
            metrics=[
                "database.latency.p50",
                "database.latency.p95",
                "database.latency.p99",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 500, "color": "yellow", "label": "Warning"},
                {"value": 1000, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Cache Hit Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Cache Hit Rate",
            description="Cache hit rate across all services",
            metrics=["cache.hit.rate"],
            visualization="gauge",
            width=4,
            height=4,
            thresholds=[
                {"value": 50, "color": "red", "label": "Poor"},
                {"value": 80, "color": "yellow", "label": "Good"},
                {"value": 95, "color": "green", "label": "Excellent"},
            ],
        )
    )

    # Service Errors Panel
    dashboard.add_panel(
        LogPanel(
            title="Service Errors",
            description="Recent service errors",
            log_query="service:* AND level:error",
            width=12,
            height=6,
            refresh_interval_seconds=30,
            time_range_minutes=30,
            max_entries=100,
        )
    )

    # Endpoint Status Panel
    dashboard.add_panel(
        StatusPanel(
            title="Endpoint Status",
            description="Current status of critical endpoints",
            status_items=[
                {"name": "UnifiedUser API", "metric": "endpoint.user.health"},
                {"name": "UnifiedAgent API", "metric": "endpoint.agent.health"},
                {"name": "Marketplace API", "metric": "endpoint.marketplace.health"},
                {"name": "Authentication API", "metric": "endpoint.auth.health"},
                {"name": "Analytics API", "metric": "endpoint.analytics.health"},
            ],
            width=4,
            height=6,
        )
    )

    # Active Service Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="Active Service Alerts",
            description="Currently active service alerts",
            alert_query="category:service",
            width=8,
            height=6,
            refresh_interval_seconds=30,
            time_range_minutes=60,
            group_by="service",
        )
    )

    return dashboard


def create_resource_utilization_dashboard() -> Dashboard:
    """Create resource utilization dashboard."""
    dashboard = Dashboard(
        name="Resource Utilization",
        description="Detailed view of resource utilization across all services",
        category="System Health",
        refresh_interval_seconds=60,
        time_range_minutes=60,
        auto_refresh=True,
    )

    # CPU Utilization by Service Panel
    dashboard.add_panel(
        MetricsPanel(
            title="CPU Utilization by Service",
            description="CPU utilization broken down by service",
            metrics=["service.*.cpu.utilization"],
            visualization="bar",
            width=6,
            height=6,
            thresholds=[
                {"value": 80, "color": "yellow", "label": "Warning"},
                {"value": 90, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Memory Utilization by Service Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Memory Utilization by Service",
            description="Memory utilization broken down by service",
            metrics=["service.*.memory.utilization"],
            visualization="bar",
            width=6,
            height=6,
            thresholds=[
                {"value": 85, "color": "yellow", "label": "Warning"},
                {"value": 95, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Disk I/O by Service Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Disk I/O by Service",
            description="Disk I/O operations broken down by service",
            metrics=["service.*.disk.read_ops", "service.*.disk.write_ops"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Network I/O by Service Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Network I/O by Service",
            description="Network I/O operations broken down by service",
            metrics=["service.*.network.in", "service.*.network.out"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    return dashboard
