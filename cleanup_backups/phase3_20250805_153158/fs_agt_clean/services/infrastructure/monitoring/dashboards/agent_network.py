"""
AutonomousAgent Network Dashboard Module for FlipSync Monitoring System

This module defines the agent network dashboards including agent communication flow,
performance visualizations, and agent health monitoring.
"""


from .system_health import AlertPanel, Dashboard, LogPanel, MetricsPanel, StatusPanel


def create_agent_communication_dashboard() -> Dashboard:
    """Create agent communication flow dashboard."""
    dashboard = Dashboard(
        name="AutonomousAgent Communication Flow",
        description="Visualization of agent communication patterns and message flow",
        category="AutonomousAgent Network",
        refresh_interval_seconds=30,
        time_range_minutes=30,
        auto_refresh=True,
    )

    # Message Volume Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Message Volume",
            description="Total message volume across all agent types",
            metrics=["agent.messages.sent", "agent.messages.received"],
            visualization="line",
            width=8,
            height=4,
            data_source="agent_network",
        )
    )

    # Message Type Distribution Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Message Type Distribution",
            description="Distribution of messages by type",
            metrics=[
                "agent.messages.command",
                "agent.messages.query",
                "agent.messages.response",
                "agent.messages.notification",
                "agent.messages.event",
                "agent.messages.error",
            ],
            visualization="pie",
            width=4,
            height=4,
            data_source="agent_network",
        )
    )

    # AutonomousAgent-to-AutonomousAgent Communication Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent-to-AutonomousAgent Communication",
            description="Communication volume between agent types",
            metrics=[
                "agent.communication.executive_to_market",
                "agent.communication.executive_to_logistics",
                "agent.communication.executive_to_content",
                "agent.communication.market_to_logistics",
                "agent.communication.market_to_content",
                "agent.communication.logistics_to_content",
            ],
            visualization="heatmap",
            width=6,
            height=6,
            data_source="agent_network",
        )
    )

    # Message Latency Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Message Latency",
            description="Message processing latency by agent type",
            metrics=[
                "agent.latency.executive",
                "agent.latency.market",
                "agent.latency.logistics",
                "agent.latency.content",
            ],
            visualization="line",
            width=6,
            height=4,
            data_source="agent_network",
            thresholds=[
                {"value": 500, "color": "yellow", "label": "Warning"},
                {"value": 1000, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Message Queue Depth Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Message Queue Depth",
            description="Message queue depth by agent type",
            metrics=[
                "agent.queue.executive",
                "agent.queue.market",
                "agent.queue.logistics",
                "agent.queue.content",
            ],
            visualization="line",
            width=6,
            height=4,
            data_source="agent_network",
            thresholds=[
                {"value": 100, "color": "yellow", "label": "Warning"},
                {"value": 500, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Communication Errors Panel
    dashboard.add_panel(
        LogPanel(
            title="Communication Errors",
            description="Recent communication errors between agents",
            log_query="category:agent_communication AND level:error",
            width=12,
            height=6,
            data_source="agent_network",
            refresh_interval_seconds=30,
            time_range_minutes=30,
            max_entries=100,
        )
    )

    # Communication Status Panel
    dashboard.add_panel(
        StatusPanel(
            title="Communication Channel Status",
            description="Current status of agent communication channels",
            status_items=[
                {
                    "name": "Internal Messaging",
                    "metric": "agent.channel.internal.health",
                },
                {
                    "name": "External Integration",
                    "metric": "agent.channel.external.health",
                },
                {"name": "UnifiedUser Communication", "metric": "agent.channel.user.health"},
                {"name": "Event Bus", "metric": "agent.channel.event_bus.health"},
            ],
            width=4,
            height=4,
            data_source="agent_network",
        )
    )

    # Active Communication Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="Active Communication Alerts",
            description="Currently active agent communication alerts",
            alert_query="category:agent_communication",
            width=8,
            height=4,
            data_source="agent_network",
            refresh_interval_seconds=30,
            time_range_minutes=60,
            group_by="severity",
        )
    )

    return dashboard


def create_agent_performance_dashboard() -> Dashboard:
    """Create agent performance dashboard."""
    dashboard = Dashboard(
        name="AutonomousAgent Performance",
        description="Performance metrics for all agent types",
        category="AutonomousAgent Network",
        refresh_interval_seconds=60,
        time_range_minutes=60,
        auto_refresh=True,
    )

    # Executive AutonomousAgent Performance Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Executive AutonomousAgent Performance",
            description="Performance metrics for executive agents",
            metrics=[
                "agent.executive.decisions_per_minute",
                "agent.executive.decision_quality_score",
                "agent.executive.resource_allocation_efficiency",
            ],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Market AutonomousAgent Performance Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Market AutonomousAgent Performance",
            description="Performance metrics for market agents",
            metrics=[
                "agent.market.listings_optimized_per_hour",
                "agent.market.pricing_strategy_effectiveness",
                "agent.market.competitive_analysis_accuracy",
            ],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Logistics AutonomousAgent Performance Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Logistics AutonomousAgent Performance",
            description="Performance metrics for logistics agents",
            metrics=[
                "agent.logistics.shipping_optimization_score",
                "agent.logistics.inventory_accuracy",
                "agent.logistics.fulfillment_efficiency",
            ],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Content AutonomousAgent Performance Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Content AutonomousAgent Performance",
            description="Performance metrics for content agents",
            metrics=[
                "agent.content.descriptions_generated_per_hour",
                "agent.content.content_quality_score",
                "agent.content.seo_effectiveness",
            ],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # AutonomousAgent CPU Utilization Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent CPU Utilization",
            description="CPU utilization by agent type",
            metrics=[
                "agent.cpu.executive",
                "agent.cpu.market",
                "agent.cpu.logistics",
                "agent.cpu.content",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 80, "color": "yellow", "label": "Warning"},
                {"value": 90, "color": "red", "label": "Critical"},
            ],
        )
    )

    # AutonomousAgent Memory Utilization Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent Memory Utilization",
            description="Memory utilization by agent type",
            metrics=[
                "agent.memory.executive",
                "agent.memory.market",
                "agent.memory.logistics",
                "agent.memory.content",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 85, "color": "yellow", "label": "Warning"},
                {"value": 95, "color": "red", "label": "Critical"},
            ],
        )
    )

    # AutonomousAgent Error Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent Error Rate",
            description="Error rate by agent type",
            metrics=[
                "agent.error_rate.executive",
                "agent.error_rate.market",
                "agent.error_rate.logistics",
                "agent.error_rate.content",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 1, "color": "yellow", "label": "Warning"},
                {"value": 5, "color": "red", "label": "Critical"},
            ],
        )
    )

    # AutonomousAgent Response Time Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent Response Time",
            description="Response time by agent type",
            metrics=[
                "agent.response_time.executive",
                "agent.response_time.market",
                "agent.response_time.logistics",
                "agent.response_time.content",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 1000, "color": "yellow", "label": "Warning"},
                {"value": 3000, "color": "red", "label": "Critical"},
            ],
        )
    )

    # AutonomousAgent Performance Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="AutonomousAgent Performance Alerts",
            description="Currently active agent performance alerts",
            alert_query="category:agent_performance",
            width=12,
            height=4,
            refresh_interval_seconds=30,
            time_range_minutes=60,
            group_by="agent_type",
        )
    )

    return dashboard


def create_agent_health_dashboard() -> Dashboard:
    """Create agent health monitoring dashboard."""
    dashboard = Dashboard(
        name="AutonomousAgent Health Monitoring",
        description="Health and status monitoring for all agent types",
        category="AutonomousAgent Network",
        refresh_interval_seconds=30,
        time_range_minutes=30,
        auto_refresh=True,
    )

    # AutonomousAgent Status Overview Panel
    dashboard.add_panel(
        StatusPanel(
            title="AutonomousAgent Status Overview",
            description="Current status of all agent types",
            status_items=[
                {"name": "Executive AutonomousAgents", "metric": "agent.status.executive"},
                {"name": "Market AutonomousAgents", "metric": "agent.status.market"},
                {"name": "Logistics AutonomousAgents", "metric": "agent.status.logistics"},
                {"name": "Content AutonomousAgents", "metric": "agent.status.content"},
            ],
            width=4,
            height=4,
        )
    )

    # AutonomousAgent Instance Count Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent Instance Count",
            description="Number of active instances by agent type",
            metrics=[
                "agent.instances.executive",
                "agent.instances.market",
                "agent.instances.logistics",
                "agent.instances.content",
            ],
            visualization="bar",
            width=4,
            height=4,
        )
    )

    # AutonomousAgent Restart Count Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent Restart Count",
            description="Number of agent restarts in the last 24 hours",
            metrics=[
                "agent.restarts.executive",
                "agent.restarts.market",
                "agent.restarts.logistics",
                "agent.restarts.content",
            ],
            visualization="bar",
            width=4,
            height=4,
            thresholds=[
                {"value": 5, "color": "yellow", "label": "Warning"},
                {"value": 10, "color": "red", "label": "Critical"},
            ],
        )
    )

    # AutonomousAgent Memory Leaks Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent Memory Growth",
            description="Memory growth over time by agent type",
            metrics=[
                "agent.memory_growth.executive",
                "agent.memory_growth.market",
                "agent.memory_growth.logistics",
                "agent.memory_growth.content",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 10, "color": "yellow", "label": "Warning"},
                {"value": 20, "color": "red", "label": "Critical"},
            ],
        )
    )

    # AutonomousAgent Database Connections Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent Database Connections",
            description="Database connections by agent type",
            metrics=[
                "agent.db_connections.executive",
                "agent.db_connections.market",
                "agent.db_connections.logistics",
                "agent.db_connections.content",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 80, "color": "yellow", "label": "Warning"},
                {"value": 100, "color": "red", "label": "Critical"},
            ],
        )
    )

    # AutonomousAgent Errors Panel
    dashboard.add_panel(
        LogPanel(
            title="AutonomousAgent Errors",
            description="Recent agent errors",
            log_query="category:agent AND level:error",
            width=12,
            height=6,
            refresh_interval_seconds=30,
            time_range_minutes=30,
            max_entries=100,
        )
    )

    # AutonomousAgent Health Checks Panel
    dashboard.add_panel(
        MetricsPanel(
            title="AutonomousAgent Health Checks",
            description="Health check success rate by agent type",
            metrics=[
                "agent.health_check.executive",
                "agent.health_check.market",
                "agent.health_check.logistics",
                "agent.health_check.content",
            ],
            visualization="gauge",
            width=6,
            height=4,
            thresholds=[
                {"value": 90, "color": "red", "label": "Critical"},
                {"value": 95, "color": "yellow", "label": "Warning"},
                {"value": 99, "color": "green", "label": "Healthy"},
            ],
        )
    )

    # AutonomousAgent Deployment Status Panel
    dashboard.add_panel(
        StatusPanel(
            title="AutonomousAgent Deployment Status",
            description="Current deployment status of agent versions",
            status_items=[
                {
                    "name": "Executive AutonomousAgent v1.2.3",
                    "metric": "agent.deployment.executive",
                },
                {"name": "Market AutonomousAgent v1.1.7", "metric": "agent.deployment.market"},
                {
                    "name": "Logistics AutonomousAgent v1.0.9",
                    "metric": "agent.deployment.logistics",
                },
                {"name": "Content AutonomousAgent v1.3.1", "metric": "agent.deployment.content"},
            ],
            width=6,
            height=4,
        )
    )

    # AutonomousAgent Health Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="AutonomousAgent Health Alerts",
            description="Currently active agent health alerts",
            alert_query="category:agent_health",
            width=12,
            height=4,
            refresh_interval_seconds=30,
            time_range_minutes=60,
            group_by="agent_type",
        )
    )

    return dashboard


# Export dashboards
AGENT_NETWORK_DASHBOARDS = [
    create_agent_communication_dashboard(),
    create_agent_performance_dashboard(),
    create_agent_health_dashboard(),
]


def create_agent_network_dashboard() -> Dashboard:
    """Create agent network dashboard.

    This is a convenience function that returns the agent communication dashboard
    with data_source attribute added to all panels.
    """
    dashboard = create_agent_communication_dashboard()

    # Add data_source attribute to all panels
    for panel in dashboard.panels:
        if panel.data_source is None:
            panel.data_source = "agent_network"

    return dashboard
