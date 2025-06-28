"""
Business Operations Dashboard Module for FlipSync Monitoring System

This module defines the business operations dashboards including marketplace activity,
user engagement, and business metrics visualizations.
"""

import datetime
import json
from typing import Dict, List, Optional, Union

from .system_health import AlertPanel, Dashboard, LogPanel, MetricsPanel, StatusPanel


def create_marketplace_activity_dashboard() -> Dashboard:
    """Create marketplace activity dashboard."""
    dashboard = Dashboard(
        name="Marketplace Activity",
        description="Visualization of marketplace activity and performance metrics",
        category="Business Operations",
        refresh_interval_seconds=60,
        time_range_minutes=60,
        auto_refresh=True,
    )

    # Transaction Volume Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Transaction Volume",
            description="Transaction volume across all marketplaces",
            metrics=["marketplace.transactions.volume"],
            visualization="line",
            width=6,
            height=4,
            data_source="business_operations",
        )
    )

    # Transaction Value Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Transaction Value",
            description="Transaction value across all marketplaces",
            metrics=["marketplace.transactions.value"],
            visualization="line",
            width=6,
            height=4,
            data_source="business_operations",
        )
    )

    # Marketplace Distribution Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Marketplace Distribution",
            description="Distribution of transactions by marketplace",
            metrics=[
                "marketplace.amazon.transactions",
                "marketplace.ebay.transactions",
                "marketplace.walmart.transactions",
                "marketplace.etsy.transactions",
                "marketplace.shopify.transactions",
            ],
            visualization="pie",
            width=4,
            height=4,
            data_source="business_operations",
        )
    )

    # Product Category Distribution Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Product Category Distribution",
            description="Distribution of transactions by product category",
            metrics=[
                "marketplace.category.electronics",
                "marketplace.category.home",
                "marketplace.category.clothing",
                "marketplace.category.toys",
                "marketplace.category.beauty",
                "marketplace.category.other",
            ],
            visualization="pie",
            width=4,
            height=4,
            data_source="business_operations",
        )
    )

    # Order Success Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Order Success Rate",
            description="Success rate of orders across all marketplaces",
            metrics=["marketplace.orders.success_rate"],
            visualization="gauge",
            width=4,
            height=4,
            thresholds=[
                {"value": 90, "color": "red", "label": "Critical"},
                {"value": 95, "color": "yellow", "label": "Warning"},
                {"value": 98, "color": "green", "label": "Healthy"},
            ],
        )
    )

    # Marketplace Error Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Marketplace Error Rate",
            description="Error rate by marketplace",
            metrics=[
                "marketplace.amazon.error_rate",
                "marketplace.ebay.error_rate",
                "marketplace.walmart.error_rate",
                "marketplace.etsy.error_rate",
                "marketplace.shopify.error_rate",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 2, "color": "yellow", "label": "Warning"},
                {"value": 5, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Marketplace Latency Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Marketplace Latency",
            description="API latency by marketplace",
            metrics=[
                "marketplace.amazon.latency",
                "marketplace.ebay.latency",
                "marketplace.walmart.latency",
                "marketplace.etsy.latency",
                "marketplace.shopify.latency",
            ],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 1000, "color": "yellow", "label": "Warning"},
                {"value": 2000, "color": "red", "label": "Critical"},
            ],
        )
    )

    # Marketplace Errors Panel
    dashboard.add_panel(
        LogPanel(
            title="Marketplace Errors",
            description="Recent marketplace integration errors",
            log_query="category:marketplace AND level:error",
            width=12,
            height=6,
            refresh_interval_seconds=30,
            time_range_minutes=30,
            max_entries=100,
        )
    )

    # Marketplace Status Panel
    dashboard.add_panel(
        StatusPanel(
            title="Marketplace Status",
            description="Current status of marketplace integrations",
            status_items=[
                {"name": "Amazon", "metric": "marketplace.amazon.status"},
                {"name": "eBay", "metric": "marketplace.ebay.status"},
                {"name": "Walmart", "metric": "marketplace.walmart.status"},
                {"name": "Etsy", "metric": "marketplace.etsy.status"},
                {"name": "Shopify", "metric": "marketplace.shopify.status"},
            ],
            width=4,
            height=6,
        )
    )

    # Marketplace Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="Marketplace Alerts",
            description="Currently active marketplace alerts",
            alert_query="category:marketplace",
            width=8,
            height=6,
            refresh_interval_seconds=30,
            time_range_minutes=60,
            group_by="marketplace",
        )
    )

    return dashboard


def create_user_engagement_dashboard() -> Dashboard:
    """Create user engagement dashboard."""
    dashboard = Dashboard(
        name="UnifiedUser Engagement",
        description="Visualization of user engagement and activity metrics",
        category="Business Operations",
        refresh_interval_seconds=60,
        time_range_minutes=60,
        auto_refresh=True,
    )

    # Active UnifiedUsers Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Active UnifiedUsers",
            description="Active users over time",
            metrics=[
                "users.active.daily",
                "users.active.weekly",
                "users.active.monthly",
            ],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # UnifiedUser Session Duration Panel
    dashboard.add_panel(
        MetricsPanel(
            title="UnifiedUser Session Duration",
            description="Average session duration over time",
            metrics=["users.session.duration"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Feature Usage Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Feature Usage",
            description="Usage distribution across features",
            metrics=[
                "users.feature.dashboard",
                "users.feature.inventory",
                "users.feature.pricing",
                "users.feature.orders",
                "users.feature.analytics",
                "users.feature.settings",
            ],
            visualization="bar",
            width=6,
            height=4,
        )
    )

    # UnifiedUser Retention Panel
    dashboard.add_panel(
        MetricsPanel(
            title="UnifiedUser Retention",
            description="UnifiedUser retention by cohort",
            metrics=[
                "users.retention.7day",
                "users.retention.30day",
                "users.retention.90day",
            ],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # UnifiedUser Satisfaction Panel
    dashboard.add_panel(
        MetricsPanel(
            title="UnifiedUser Satisfaction",
            description="UnifiedUser satisfaction score over time",
            metrics=["users.satisfaction.score"],
            visualization="gauge",
            width=4,
            height=4,
            thresholds=[
                {"value": 3.0, "color": "red", "label": "Poor"},
                {"value": 4.0, "color": "yellow", "label": "Good"},
                {"value": 4.5, "color": "green", "label": "Excellent"},
            ],
        )
    )

    # UnifiedUser Error Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="UnifiedUser Error Rate",
            description="Error rate experienced by users",
            metrics=["users.error.rate"],
            visualization="line",
            width=4,
            height=4,
            thresholds=[
                {"value": 1, "color": "yellow", "label": "Warning"},
                {"value": 3, "color": "red", "label": "Critical"},
            ],
        )
    )

    # UnifiedUser Feedback Panel
    dashboard.add_panel(
        LogPanel(
            title="UnifiedUser Feedback",
            description="Recent user feedback",
            log_query="category:user_feedback",
            width=12,
            height=6,
            refresh_interval_seconds=60,
            time_range_minutes=1440,  # 24 hours
            max_entries=100,
        )
    )

    # UnifiedUser Platform Distribution Panel
    dashboard.add_panel(
        MetricsPanel(
            title="UnifiedUser Platform Distribution",
            description="Distribution of users by platform",
            metrics=[
                "users.platform.web",
                "users.platform.ios",
                "users.platform.android",
            ],
            visualization="pie",
            width=4,
            height=4,
        )
    )

    # UnifiedUser Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="UnifiedUser Experience Alerts",
            description="Currently active user experience alerts",
            alert_query="category:user_experience",
            width=8,
            height=4,
            refresh_interval_seconds=30,
            time_range_minutes=60,
            group_by="severity",
        )
    )

    return dashboard


def create_business_metrics_dashboard() -> Dashboard:
    """Create business metrics dashboard."""
    dashboard = Dashboard(
        name="Business Metrics",
        description="Key business metrics and performance indicators",
        category="Business Operations",
        refresh_interval_seconds=300,  # 5 minutes
        time_range_minutes=1440,  # 24 hours
        auto_refresh=True,
    )

    # Add data_source to all panels that will be added

    # Revenue Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Revenue",
            description="Revenue over time",
            metrics=[
                "business.revenue.daily",
                "business.revenue.weekly",
                "business.revenue.monthly",
            ],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Profit Margin Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Profit Margin",
            description="Profit margin over time",
            metrics=["business.profit_margin"],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 10, "color": "red", "label": "Low"},
                {"value": 20, "color": "yellow", "label": "Medium"},
                {"value": 30, "color": "green", "label": "High"},
            ],
        )
    )

    # Customer Acquisition Cost Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Customer Acquisition Cost",
            description="Cost to acquire new customers",
            metrics=["business.cac"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Customer Lifetime Value Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Customer Lifetime Value",
            description="Average lifetime value of customers",
            metrics=["business.ltv"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Inventory Turnover Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Inventory Turnover",
            description="Inventory turnover rate",
            metrics=["business.inventory_turnover"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Order Fulfillment Cost Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Order Fulfillment Cost",
            description="Average cost to fulfill orders",
            metrics=["business.fulfillment_cost"],
            visualization="line",
            width=6,
            height=4,
        )
    )

    # Return Rate Panel
    dashboard.add_panel(
        MetricsPanel(
            title="Return Rate",
            description="Product return rate",
            metrics=["business.return_rate"],
            visualization="line",
            width=6,
            height=4,
            thresholds=[
                {"value": 10, "color": "green", "label": "Low"},
                {"value": 15, "color": "yellow", "label": "Medium"},
                {"value": 20, "color": "red", "label": "High"},
            ],
        )
    )

    # UnifiedAgent ROI Panel
    dashboard.add_panel(
        MetricsPanel(
            title="UnifiedAgent ROI",
            description="Return on investment for agent operations",
            metrics=[
                "business.roi.executive",
                "business.roi.market",
                "business.roi.logistics",
                "business.roi.content",
            ],
            visualization="bar",
            width=6,
            height=4,
        )
    )

    # Business Alerts Panel
    dashboard.add_panel(
        AlertPanel(
            title="Business Metric Alerts",
            description="Currently active business metric alerts",
            alert_query="category:business_metrics",
            width=12,
            height=4,
            refresh_interval_seconds=300,
            time_range_minutes=1440,
            group_by="metric",
        )
    )

    # Add data_source attribute to all panels
    for panel in dashboard.panels:
        if panel.data_source is None:
            panel.data_source = "business_metrics"

    return dashboard


# Export dashboards
BUSINESS_OPERATIONS_DASHBOARDS = [
    create_marketplace_activity_dashboard(),
    create_user_engagement_dashboard(),
    create_business_metrics_dashboard(),
]


def create_business_operations_dashboard() -> Dashboard:
    """Create business operations dashboard.

    This is a convenience function that returns the marketplace activity dashboard
    with data_source attribute added to all panels.
    """
    dashboard = create_marketplace_activity_dashboard()

    # Add data_source attribute to all panels
    for panel in dashboard.panels:
        if panel.data_source is None:
            panel.data_source = "business_operations"

    return dashboard
