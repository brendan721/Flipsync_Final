from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field

from fs_agt_clean.core.config import get_settings
from fs_agt_clean.core.config.manager import get_config_manager
from fs_agt_clean.core.models.analytics import (
    MarketplaceComparisonRequest,
    MarketplaceComparisonResponse,
    PerformanceMetricsRequest,
    PerformanceMetricsResponse,
    SalesReportRequest,
    SalesReportResponse,
)
from fs_agt_clean.core.models.api_response import ApiResponse
from fs_agt_clean.core.models.user import UnifiedUser
from fs_agt_clean.core.monitoring.log_manager import LogManager
from fs_agt_clean.core.security.auth import get_current_user
from fs_agt_clean.services.analytics.analytics_service import AnalyticsService

# Create router without prefix (prefix is added in main.py)
router = APIRouter(
    tags=["analytics"],
    responses={404: {"description": "Not found"}},
)


# OPTIONS handlers for CORS preflight requests
@router.options("/dashboard")
async def options_analytics_dashboard():
    """Handle CORS preflight for analytics dashboard endpoint."""
    return {"message": "OK"}


# Get analytics service instance
async def get_analytics_service() -> AnalyticsService:
    """Get the analytics service instance."""
    config_manager = get_config_manager()
    log_manager = LogManager()
    return AnalyticsService(config=config_manager, log_manager=log_manager)


@router.post("/performance-metrics", response_model=PerformanceMetricsResponse)
async def get_performance_metrics(
    request: PerformanceMetricsRequest,
    current_user: UnifiedUser = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get performance metrics for listings across marketplaces.

    This endpoint provides detailed performance metrics for listings,
    including views, conversion rates, and revenue data.
    """
    try:
        # Get metrics from analytics service
        metrics = await analytics_service.get_metrics(
            category="performance",
            start_time=request.time_period.start_date,
            end_time=request.time_period.end_date,
        )

        # Process metrics into the required format
        total_views = 0
        unique_visitors = 0
        total_sales = 0
        total_revenue = 0
        marketplace_breakdown = {}
        top_products = []

        # Process metrics to extract required data
        for point in metrics:
            if point.name == "views":
                total_views += point.value
            elif point.name == "unique_visitors":
                unique_visitors += point.value
            elif point.name == "sales":
                total_sales += point.value
            elif point.name == "revenue":
                total_revenue += point.value

            # Extract marketplace data
            marketplace = point.labels.get("marketplace")
            if marketplace:
                if marketplace not in marketplace_breakdown:
                    marketplace_breakdown[marketplace] = {
                        "views": 0,
                        "conversion_rate": 0,
                        "sales": 0,
                        "revenue": 0,
                    }

                if point.name == "views":
                    marketplace_breakdown[marketplace]["views"] += point.value
                elif point.name == "sales":
                    marketplace_breakdown[marketplace]["sales"] += point.value
                elif point.name == "revenue":
                    marketplace_breakdown[marketplace]["revenue"] += point.value

            # Extract product data
            product_id = point.labels.get("product_id")
            product_title = point.labels.get("product_title")
            if product_id and product_title:
                product_exists = False
                for product in top_products:
                    if product["product_id"] == product_id:
                        product_exists = True
                        if point.name == "views":
                            product["views"] += point.value
                        elif point.name == "sales":
                            product["sales"] += point.value
                        elif point.name == "revenue":
                            product["revenue"] += point.value
                        break

                if not product_exists and len(top_products) < 10:
                    top_products.append(
                        {
                            "product_id": product_id,
                            "title": product_title,
                            "views": point.value if point.name == "views" else 0,
                            "conversion_rate": 0,
                            "sales": point.value if point.name == "sales" else 0,
                            "revenue": point.value if point.name == "revenue" else 0,
                        }
                    )

        # Calculate derived metrics
        conversion_rate = (total_sales / total_views * 100) if total_views > 0 else 0
        average_order_value = (total_revenue / total_sales) if total_sales > 0 else 0

        # Calculate conversion rates for marketplaces
        for marketplace in marketplace_breakdown:
            views = marketplace_breakdown[marketplace]["views"]
            sales = marketplace_breakdown[marketplace]["sales"]
            marketplace_breakdown[marketplace]["conversion_rate"] = (
                (sales / views * 100) if views > 0 else 0
            )

        # Calculate conversion rates for products
        for product in top_products:
            views = product["views"]
            sales = product["sales"]
            product["conversion_rate"] = (sales / views * 100) if views > 0 else 0

        # Sort top products by revenue
        top_products.sort(key=lambda x: x["revenue"], reverse=True)

        return PerformanceMetricsResponse(
            request_id=f"metrics_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            time_period=request.time_period,
            metrics={
                "total_views": total_views,
                "unique_visitors": unique_visitors,
                "conversion_rate": conversion_rate,
                "total_sales": total_sales,
                "total_revenue": total_revenue,
                "average_order_value": average_order_value,
                "return_rate": 0,  # This would need additional data
                "marketplace_breakdown": marketplace_breakdown,
            },
            top_performing_products=top_products[:5],  # Limit to top 5
            created_at=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance metrics: {str(e)}",
        )


@router.post("/sales-report", response_model=SalesReportResponse)
async def generate_sales_report(
    request: SalesReportRequest,
    current_user: UnifiedUser = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Generate a comprehensive sales report.

    This endpoint generates detailed sales reports with filtering by
    time period, marketplace, and product category.
    """
    try:
        # Get metrics from analytics service with filters
        filters = {}
        if request.filters:
            if request.filters.marketplace_ids:
                filters["marketplace_id"] = request.filters.marketplace_ids[
                    0
                ]  # Use first for simplicity
            if request.filters.category_ids:
                filters["category_id"] = request.filters.category_ids[
                    0
                ]  # Use first for simplicity

        # Get sales metrics
        metrics = await analytics_service.get_metrics(
            category="sales",
            start_time=request.time_period.start_date,
            end_time=request.time_period.end_date,
        )

        # Process metrics into the required format
        total_sales = 0
        total_revenue = 0
        total_profit = 0
        sales_by_marketplace = {}
        sales_by_category = {}
        top_products = []

        # Process metrics to extract required data
        for point in metrics:
            if point.name == "sales":
                total_sales += point.value
            elif point.name == "revenue":
                total_revenue += point.value
            elif point.name == "profit":
                total_profit += point.value

            # Extract marketplace data
            marketplace = point.labels.get("marketplace")
            if marketplace:
                if marketplace not in sales_by_marketplace:
                    sales_by_marketplace[marketplace] = {
                        "sales": 0,
                        "revenue": 0,
                        "profit": 0,
                    }

                if point.name == "sales":
                    sales_by_marketplace[marketplace]["sales"] += point.value
                elif point.name == "revenue":
                    sales_by_marketplace[marketplace]["revenue"] += point.value
                elif point.name == "profit":
                    sales_by_marketplace[marketplace]["profit"] += point.value

            # Extract category data
            category = point.labels.get("category")
            if category:
                if category not in sales_by_category:
                    sales_by_category[category] = {
                        "sales": 0,
                        "revenue": 0,
                        "profit": 0,
                    }

                if point.name == "sales":
                    sales_by_category[category]["sales"] += point.value
                elif point.name == "revenue":
                    sales_by_category[category]["revenue"] += point.value
                elif point.name == "profit":
                    sales_by_category[category]["profit"] += point.value

            # Extract product data
            product_id = point.labels.get("product_id")
            product_title = point.labels.get("product_title")
            if product_id and product_title:
                product_exists = False
                for product in top_products:
                    if product["product_id"] == product_id:
                        product_exists = True
                        if point.name == "sales":
                            product["sales"] += point.value
                        elif point.name == "revenue":
                            product["revenue"] += point.value
                        elif point.name == "profit":
                            product["profit"] += point.value
                        break

                if not product_exists and len(top_products) < 10:
                    top_products.append(
                        {
                            "product_id": product_id,
                            "title": product_title,
                            "sales": point.value if point.name == "sales" else 0,
                            "revenue": point.value if point.name == "revenue" else 0,
                            "profit": point.value if point.name == "profit" else 0,
                        }
                    )

        # Calculate derived metrics
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        average_order_value = (total_revenue / total_sales) if total_sales > 0 else 0

        # Sort top products by revenue
        top_products.sort(key=lambda x: x["revenue"], reverse=True)

        # Generate report ID and URL
        report_id = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        report_url = f"https://api.flipsync.com/reports/{report_id}.pdf"

        return SalesReportResponse(
            report_id=report_id,
            time_period=request.time_period,
            filters=request.filters,
            summary={
                "total_sales": total_sales,
                "total_revenue": total_revenue,
                "total_profit": total_profit,
                "profit_margin": profit_margin,
                "average_order_value": average_order_value,
                "sales_growth": 0,  # This would need historical data comparison
            },
            sales_by_marketplace=sales_by_marketplace,
            sales_by_category=sales_by_category,
            top_products=top_products[:5],  # Limit to top 5
            report_url=report_url,
            created_at=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate sales report: {str(e)}",
        )


@router.post("/marketplace-comparison", response_model=MarketplaceComparisonResponse)
async def compare_marketplaces(
    request: MarketplaceComparisonRequest,
    current_user: UnifiedUser = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Compare performance across different marketplaces.

    This endpoint provides comparative analysis of product performance
    across different marketplaces.
    """
    try:
        # Get metrics for each marketplace
        marketplace_metrics = {}
        for marketplace in request.marketplaces:
            metrics = await analytics_service.get_metrics(
                category="marketplace",
                start_time=request.time_period.start_date,
                end_time=request.time_period.end_date,
                filters={"marketplace": marketplace},
            )
            marketplace_metrics[marketplace] = metrics

        # Process metrics into the required format
        sales_volume = {}
        revenue = {}
        profit = {}
        conversion_rate = {}
        average_price = {}

        # Category data
        category_data = {}

        # Product data
        product_data = {}

        # Process metrics for each marketplace
        for marketplace, metrics in marketplace_metrics.items():
            total_sales = 0
            total_revenue = 0
            total_profit = 0
            total_conversions = 0

            for point in metrics:
                if point.name == "sales":
                    total_sales += point.value
                elif point.name == "revenue":
                    total_revenue += point.value
                elif point.name == "profit":
                    total_profit += point.value
                elif point.name == "conversions":
                    total_conversions += point.value

                # Extract category data
                category = point.labels.get("category")
                if category:
                    if category not in category_data:
                        category_data[category] = {
                            "best_performing": "",
                            "sales_volume": {},
                            "revenue": {},
                        }

                    if point.name == "sales":
                        if marketplace not in category_data[category]["sales_volume"]:
                            category_data[category]["sales_volume"][marketplace] = 0
                        category_data[category]["sales_volume"][
                            marketplace
                        ] += point.value
                    elif point.name == "revenue":
                        if marketplace not in category_data[category]["revenue"]:
                            category_data[category]["revenue"][marketplace] = 0
                        category_data[category]["revenue"][marketplace] += point.value

                # Extract product data
                product_id = point.labels.get("product_id")
                product_title = point.labels.get("product_title")
                if product_id and product_title:
                    if product_id not in product_data:
                        product_data[product_id] = {
                            "product_id": product_id,
                            "title": product_title,
                            "best_performing": "",
                            "sales": {},
                            "revenue": {},
                            "conversion_rate": {},
                        }

                    if point.name == "sales":
                        product_data[product_id]["sales"][marketplace] = point.value
                    elif point.name == "revenue":
                        product_data[product_id]["revenue"][marketplace] = point.value
                    elif (
                        point.name == "conversions"
                        and product_id in product_data
                        and "sales" in product_data[product_id]
                        and marketplace in product_data[product_id]["sales"]
                    ):
                        sales = product_data[product_id]["sales"][marketplace]
                        product_data[product_id]["conversion_rate"][marketplace] = (
                            (point.value / sales * 100) if sales > 0 else 0
                        )

            # Store aggregated data for the marketplace
            sales_volume[marketplace] = total_sales
            revenue[marketplace] = total_revenue
            profit_margin = (
                (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            )
            profit[marketplace] = profit_margin
            conversion_rate[marketplace] = (
                (total_conversions / total_sales * 100) if total_sales > 0 else 0
            )
            average_price[marketplace] = (
                (total_revenue / total_sales) if total_sales > 0 else 0
            )

        # Determine best performing marketplace overall
        best_marketplace = (
            max(revenue.items(), key=lambda x: x[1])[0] if revenue else ""
        )

        # Determine best performing marketplace for each category
        for category in category_data:
            if category_data[category]["revenue"]:
                best_category_marketplace = max(
                    category_data[category]["revenue"].items(), key=lambda x: x[1]
                )[0]
                category_data[category]["best_performing"] = best_category_marketplace

        # Determine best performing marketplace for each product
        for product_id, product in product_data.items():
            if product["revenue"]:
                best_product_marketplace = max(
                    product["revenue"].items(), key=lambda x: x[1]
                )[0]
                product["best_performing"] = best_product_marketplace

        # Convert product_data dictionary to list and sort by revenue
        product_comparison = list(product_data.values())
        product_comparison.sort(key=lambda x: sum(x["revenue"].values()), reverse=True)

        # Generate recommendations based on the data
        recommendations = []

        # Add category-based recommendations
        for category, data in category_data.items():
            best = data["best_performing"]
            if best:
                recommendations.append(
                    f"Focus {category} listings on {best} for better performance"
                )

        # Add general recommendations based on conversion rates
        if conversion_rate:
            best_conversion = max(conversion_rate.items(), key=lambda x: x[1])[0]
            recommendations.append(
                f"Optimize listings for {best_conversion} to improve conversion rates"
            )

        # Add pricing recommendations
        if average_price:
            best_price = max(average_price.items(), key=lambda x: x[1])[0]
            worst_price = min(average_price.items(), key=lambda x: x[1])[0]
            recommendations.append(
                f"Consider adjusting pricing strategy on {worst_price} to increase average selling price"
            )

        # Limit to 4 recommendations
        recommendations = recommendations[:4]

        return MarketplaceComparisonResponse(
            comparison_id=f"comp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            time_period=request.time_period,
            marketplaces=request.marketplaces,
            overall_comparison={
                "best_performing": best_marketplace,
                "sales_volume": sales_volume,
                "revenue": revenue,
                "profit_margin": profit,
                "conversion_rate": conversion_rate,
                "average_selling_price": average_price,
            },
            category_comparison=category_data,
            product_comparison=product_comparison[:5],  # Limit to top 5 products
            recommendations=recommendations,
            created_at=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare marketplaces: {str(e)}",
        )


@router.get("/dashboard")
async def get_dashboard():
    """
    Get basic analytics dashboard data without authentication for mobile app testing.
    """
    return {
        "status": "ok",
        "analytics": {
            "total_sales": 1250,
            "total_revenue": 45000.00,
            "conversion_rate": 3.2,
            "active_listings": 89,
        },
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/dashboard-data", response_model=Dict)
async def get_dashboard_data(
    time_period: str = Query(
        "last_30_days", description="Time period for dashboard data"
    ),
    current_user: UnifiedUser = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service),
):
    """
    Get data for the analytics dashboard.

    This endpoint provides summary data for the analytics dashboard,
    including key performance indicators and trend data.
    """
    try:
        # Convert time_period string to actual date range
        end_date = datetime.now()
        start_date = None

        if time_period == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif time_period == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif time_period == "last_90_days":
            start_date = end_date - timedelta(days=90)
        elif time_period == "year_to_date":
            start_date = datetime(end_date.year, 1, 1)
        else:
            # Default to last 30 days
            start_date = end_date - timedelta(days=30)

        # Get dashboard metrics
        metrics = await analytics_service.get_metrics(
            category="dashboard", start_time=start_date, end_time=end_date
        )

        # Process metrics for dashboard
        dashboard_data = {
            "summary": {
                "total_sales": 0,
                "total_revenue": 0,
                "total_orders": 0,
                "conversion_rate": 0,
            },
            "trends": {
                "sales_trend": [],
                "revenue_trend": [],
                "order_trend": [],
            },
            "top_products": [],
            "marketplace_breakdown": {},
            "time_period": time_period,
            "last_updated": datetime.now().isoformat(),
        }

        # Process metrics
        for point in metrics:
            if point.name == "sales":
                dashboard_data["summary"]["total_sales"] += point.value
            elif point.name == "revenue":
                dashboard_data["summary"]["total_revenue"] += point.value
            elif point.name == "orders":
                dashboard_data["summary"]["total_orders"] += point.value

        # Calculate conversion rate
        if dashboard_data["summary"]["total_orders"] > 0:
            dashboard_data["summary"]["conversion_rate"] = (
                dashboard_data["summary"]["total_sales"]
                / dashboard_data["summary"]["total_orders"]
                * 100
            )

        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard data: {str(e)}",
        )
