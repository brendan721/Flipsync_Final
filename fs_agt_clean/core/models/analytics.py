"""
Analytics models for FlipSync.

This module contains Pydantic models for analytics-related data structures.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TimePeriod(BaseModel):
    """Time period for analytics queries."""

    start_date: datetime = Field(..., description="Start date for the time period")
    end_date: datetime = Field(..., description="End date for the time period")


class AnalyticsFilters(BaseModel):
    """Filters for analytics queries."""

    marketplace_ids: Optional[List[str]] = Field(
        None, description="List of marketplace IDs to filter by"
    )
    category_ids: Optional[List[str]] = Field(
        None, description="List of category IDs to filter by"
    )
    product_ids: Optional[List[str]] = Field(
        None, description="List of product IDs to filter by"
    )


class PerformanceMetricsRequest(BaseModel):
    """Request model for performance metrics."""

    time_period: TimePeriod = Field(..., description="Time period for the metrics")
    filters: Optional[AnalyticsFilters] = Field(
        None, description="Optional filters to apply"
    )


class TopPerformingProduct(BaseModel):
    """Model for top performing product data."""

    product_id: str = Field(..., description="Product ID")
    title: str = Field(..., description="Product title")
    views: int = Field(..., description="Number of views")
    conversion_rate: float = Field(..., description="Conversion rate as percentage")
    sales: int = Field(..., description="Number of sales")
    revenue: float = Field(..., description="Total revenue")


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""

    request_id: str = Field(..., description="Unique request ID")
    time_period: TimePeriod = Field(..., description="Time period for the metrics")
    metrics: Dict[str, Any] = Field(..., description="Performance metrics data")
    top_performing_products: List[TopPerformingProduct] = Field(
        ..., description="Top performing products"
    )
    created_at: datetime = Field(..., description="Response creation timestamp")


class SalesReportRequest(BaseModel):
    """Request model for sales report."""

    time_period: TimePeriod = Field(..., description="Time period for the report")
    filters: Optional[AnalyticsFilters] = Field(
        None, description="Optional filters to apply"
    )


class SalesReportResponse(BaseModel):
    """Response model for sales report."""

    report_id: str = Field(..., description="Unique report ID")
    time_period: TimePeriod = Field(..., description="Time period for the report")
    filters: Optional[AnalyticsFilters] = Field(None, description="Applied filters")
    summary: Dict[str, Any] = Field(..., description="Sales summary data")
    sales_by_marketplace: Dict[str, Any] = Field(
        ..., description="Sales breakdown by marketplace"
    )
    sales_by_category: Dict[str, Any] = Field(
        ..., description="Sales breakdown by category"
    )
    top_products: List[Dict[str, Any]] = Field(..., description="Top selling products")
    report_url: str = Field(..., description="URL to download the full report")
    created_at: datetime = Field(..., description="Report creation timestamp")


class MarketplaceComparisonRequest(BaseModel):
    """Request model for marketplace comparison."""

    time_period: TimePeriod = Field(..., description="Time period for the comparison")
    marketplaces: List[str] = Field(..., description="List of marketplaces to compare")


class MarketplaceComparisonResponse(BaseModel):
    """Response model for marketplace comparison."""

    comparison_id: str = Field(..., description="Unique comparison ID")
    time_period: TimePeriod = Field(..., description="Time period for the comparison")
    marketplaces: List[str] = Field(..., description="Compared marketplaces")
    overall_comparison: Dict[str, Any] = Field(
        ..., description="Overall comparison data"
    )
    category_comparison: Dict[str, Any] = Field(
        ..., description="Category-wise comparison"
    )
    product_comparison: List[Dict[str, Any]] = Field(
        ..., description="Product-wise comparison"
    )
    recommendations: List[str] = Field(..., description="Optimization recommendations")
    created_at: datetime = Field(..., description="Comparison creation timestamp")


class DashboardMetrics(BaseModel):
    """Model for dashboard metrics."""

    total_sales: int = Field(..., description="Total number of sales")
    total_revenue: float = Field(..., description="Total revenue")
    total_views: int = Field(..., description="Total number of views")
    conversion_rate: float = Field(..., description="Overall conversion rate")
    average_order_value: float = Field(..., description="Average order value")
    active_listings: int = Field(..., description="Number of active listings")
    active_marketplaces: int = Field(..., description="Number of active marketplaces")
    last_updated: str = Field(..., description="Last update timestamp")


class AnalyticsDashboardResponse(BaseModel):
    """Response model for analytics dashboard."""

    status: str = Field(..., description="Response status")
    analytics: DashboardMetrics = Field(..., description="Dashboard analytics data")
    timestamp: str = Field(..., description="Response timestamp")


class MetricPoint(BaseModel):
    """Model for a single metric data point."""

    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    timestamp: datetime = Field(..., description="Metric timestamp")
    labels: Optional[Dict[str, str]] = Field(None, description="Metric labels")


class MetricsCollection(BaseModel):
    """Model for a collection of metrics."""

    metrics: List[MetricPoint] = Field(..., description="List of metric points")
    total_count: int = Field(..., description="Total number of metrics")
    time_range: TimePeriod = Field(..., description="Time range for the metrics")
    created_at: datetime = Field(..., description="Collection creation timestamp")


class AnalyticsHealthCheck(BaseModel):
    """Model for analytics service health check."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    metrics_count: int = Field(..., description="Number of available metrics")
    timestamp: str = Field(..., description="Health check timestamp")
