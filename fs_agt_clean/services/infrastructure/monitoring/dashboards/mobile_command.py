"""
Mobile Command Center Dashboard Module for FlipSync Monitoring System

This module defines the mobile command center dashboard with mobile-friendly
critical alerts and operational status views.
"""

import datetime
import json
from typing import Dict, List, Optional, Union

from .system_health import AlertPanel, Dashboard, LogPanel, MetricsPanel, StatusPanel


def create_mobile_command_dashboard() -> Dashboard:
    """Create mobile command center dashboard."""
    dashboard = Dashboard(
        name="Mobile Command Center",
        description="Mobile-friendly critical alerts and operational status views",
        category="Mobile",
        refresh_interval_seconds=30,
        time_range_minutes=30,
        auto_refresh=True,
    )

    # Critical Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="Critical Alerts",
            description="Currently active critical alerts",
            alert_query="severity:critical",
            width=12,
            height=4,
            refresh_interval_seconds=30,
            time_range_minutes=60,
            group_by="category",
            data_source="mobile_command",
        )
    )

    # System Status Panel
    dashboard.add_panel(
        StatusPanel(
            title="System Status",
            description="Current status of critical systems",
            status_items=[
                {"name": "API Gateway", "metric": "service.api_gateway.health"},
                {"name": "Database", "metric": "service.database.health"},
                {"name": "UnifiedAgent Network", "metric": "service.agent.health"},
                {
                    "name": "Marketplace Integration",
                    "metric": "service.marketplace.health",
                },
                {"name": "Authentication", "metric": "service.auth.health"},
            ],
            width=12,
            height=4,
            data_source="mobile_command",
        )
    )

    # Key Business Metrics Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Key Business Metrics",
            description="Critical business metrics at a glance",
            metrics=[
                "business.revenue.daily",
                "marketplace.transactions.volume",
                "users.active.daily",
            ],
            visualization="stat",
            width=12,
            height=3,
            data_source="mobile_command",
        )
    )

    # Error Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Error Rates",
            description="Error rates across critical systems",
            metrics=[
                "api.error.rate",
                "marketplace.orders.error_rate",
                "agent.error_rate.executive",
            ],
            visualization="gauge",
            width=12,
            height=3,
            data_source="mobile_command",
            thresholds=[
                {"value": 1, "color": "green", "label": "Healthy"},
                {"value": 2, "color": "yellow", "label": "Warning"},
                {"value": 5, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Recent Critical Errors Panel
    dashboard.add_panel(
        LogPanel(
            title="Recent Critical Errors",
            description="Most recent critical errors",
            log_query="level:critical",
            width=12,
            height=4,
            refresh_interval_seconds=30,
            time_range_minutes=30,
            max_entries=5,
            data_source="mobile_command",
        )
    )

    # UnifiedAgent Status Panel
    dashboard.add_panel(
        StatusPanel(
            title="UnifiedAgent Status",
            description="Current status of agent types",
            status_items=[
                {"name": "Executive UnifiedAgents", "metric": "agent.status.executive"},
                {"name": "Market UnifiedAgents", "metric": "agent.status.market"},
                {"name": "Logistics UnifiedAgents", "metric": "agent.status.logistics"},
                {"name": "Content UnifiedAgents", "metric": "agent.status.content"},
            ],
            width=12,
            height=4,
            data_source="mobile_command",
        )
    )

    # On-Call Information Panel
    dashboard.add_panel(
        StatusPanel(
            title="On-Call Information",
            description="Current on-call contacts",
            status_items=[
                {"name": "Primary On-Call", "metric": "oncall.primary"},
                {"name": "Secondary On-Call", "metric": "oncall.secondary"},
                {"name": "Engineering Manager", "metric": "oncall.manager"},
            ],
            width=12,
            height=3,
            data_source="mobile_command",
        )
    )

    # Quick Actions Panel
    dashboard.add_panel(
        StatusPanel(
            title="Quick Actions",
            description="Common actions for incident response",
            status_items=[
                {
                    "name": "Restart API Gateway",
                    "metric": "action.restart_api",
                    "action": True,
                },
                {
                    "name": "Restart UnifiedAgent Service",
                    "metric": "action.restart_agent",
                    "action": True,
                },
                {
                    "name": "Pause Marketplace Integration",
                    "metric": "action.pause_marketplace",
                    "action": True,
                },
                {
                    "name": "Enable Maintenance Mode",
                    "metric": "action.maintenance",
                    "action": True,
                },
            ],
            width=12,
            height=4,
            data_source="mobile_command",
        )
    )

    return dashboard


# Export dashboards
MOBILE_COMMAND_DASHBOARDS = [create_mobile_command_dashboard()]
