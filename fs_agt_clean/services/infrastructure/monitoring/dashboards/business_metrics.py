"""
Business Metrics Dashboard Module for FlipSync Monitoring System

This module defines the business metrics dashboards including sales, revenue,
profit, and other key business performance indicators.
"""

from typing import Dict, List, Optional

from .system_health import AlertPanel, Dashboard, MetricsPanel, StatusPanel


def create_business_metrics_dashboard() -> Dashboard:
    """Create business metrics dashboard."""
    dashboard = Dashboard(
        name="Business Metrics",
        description="Key business performance indicators and metrics",
        category="Business",
        refresh_interval_seconds=300,
        time_range_minutes=1440,  # 24 hours
        auto_refresh=True,
    )

    # Sales Overview Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Sales Overview",
            description="Daily, weekly, and monthly sales",
            metrics=[
                "business.sales.daily",
                "business.sales.weekly",
                "business.sales.monthly",
            ],
            visualization="bar",
            width=8,
            height=4,
            data_source="business_metrics",
        )
    )

    # Sales Growth Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Sales Growth",
            description="Month-over-month sales growth percentage",
            metrics=["business.sales.growth"],
            visualization="gauge",
            width=4,
            height=4,
            data_source="business_metrics",
            thresholds=[
                {"value": 0, "color": "red", "label": "Negative"},
                {"value": 5, "color": "yellow", "label": "Low"},
                {"value": 10, "color": "green", "label": "Healthy"},
            ],
        )
    )

    # Sales by Channel Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Sales by Channel",
            description="Distribution of sales by marketplace channel",
            metrics=[
                "business.sales.channel.amazon",
                "business.sales.channel.ebay",
                "business.sales.channel.website",
            ],
            visualization="pie",
            width=4,
            height=4,
            data_source="business_metrics",
        )
    )

    # Inventory Overview Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Inventory Overview",
            description="Inventory levels and status",
            metrics=[
                "business.inventory.total",
                "business.inventory.out_of_stock",
                "business.inventory.low_stock",
            ],
            visualization="bar",
            width=4,
            height=4,
            data_source="business_metrics",
        )
    )

    # Inventory Turnover Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Inventory Turnover",
            description="Inventory turnover rate",
            metrics=["business.inventory.turnover"],
            visualization="gauge",
            width=4,
            height=4,
            data_source="business_metrics",
            thresholds=[
                {"value": 2, "color": "red", "label": "Low"},
                {"value": 4, "color": "yellow", "label": "Medium"},
                {"value": 6, "color": "green", "label": "High"},
            ],
        )
    )

    # Inventory by Category Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Inventory by Category",
            description="Distribution of inventory by product category",
            metrics=[
                "business.inventory.category.electronics",
                "business.inventory.category.clothing",
                "business.inventory.category.home",
                "business.inventory.category.other",
            ],
            visualization="pie",
            width=4,
            height=4,
            data_source="business_metrics",
        )
    )

    # Customer Metrics Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Customer Metrics",
            description="Customer acquisition and retention metrics",
            metrics=[
                "business.customers.total",
                "business.customers.new",
                "business.customers.repeat_rate",
            ],
            visualization="bar",
            width=6,
            height=4,
            data_source="business_metrics",
        )
    )

    # Average Order Value Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Average Order Value",
            description="Average order value trend",
            metrics=["business.customers.aov"],
            visualization="line",
            width=6,
            height=4,
            data_source="business_metrics",
        )
    )

    # Profit Metrics Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Profit Metrics",
            description="Gross and net profit metrics",
            metrics=[
                "business.profit.gross",
                "business.profit.net",
            ],
            visualization="bar",
            width=6,
            height=4,
            data_source="business_metrics",
        )
    )

    # Profit Margin Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Profit Margin",
            description="Overall profit margin percentage",
            metrics=["business.profit.margin"],
            visualization="gauge",
            width=6,
            height=4,
            data_source="business_metrics",
            thresholds=[
                {"value": 10, "color": "red", "label": "Low"},
                {"value": 20, "color": "yellow", "label": "Medium"},
                {"value": 30, "color": "green", "label": "High"},
            ],
        )
    )

    # Business Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="Business Alerts",
            description="Critical business alerts requiring attention",
            alert_query="category:business AND severity:critical",
            width=12,
            height=4,
            refresh_interval_seconds=60,
            data_source="business_metrics",
        )
    )

    # Business Health Status Panel
    dashboard.add_panel(
        StatusPanel(
            title="Business Health",
            description="Overall business health indicators",
            status_items=[
                {"name": "Sales", "metric": "business.health.sales"},
                {"name": "Inventory", "metric": "business.health.inventory"},
                {"name": "Customers", "metric": "business.health.customers"},
                {"name": "Profit", "metric": "business.health.profit"},
            ],
            width=12,
            height=3,
            data_source="business_metrics",
        )
    )

    return dashboard
