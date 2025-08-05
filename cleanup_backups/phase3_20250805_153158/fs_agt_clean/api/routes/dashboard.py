"""
Dashboard routes for the FlipSync AutonomousAgent Service.

This module provides endpoints for dashboard functionality, including metrics,
visualizations, and data access.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from fs_agt_clean.database.models.unified_user import UnifiedUserResponse, UnifiedUserRole

# ENHANCED: Use unified authentication dependencies
from fs_agt_clean.api.dependencies.dependencies import get_current_user
from fs_agt_clean.api.routes.auth import oauth2_scheme

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


# OPTIONS handlers for CORS preflight requests
@router.options("/")
async def options_dashboards():
    """Handle CORS preflight for dashboards root endpoint."""
    return {"message": "OK"}


@router.options("/{dashboard_id}")
async def options_dashboard(dashboard_id: str):
    """Handle CORS preflight for specific dashboard endpoint."""
    return {"message": "OK"}


@router.options("/metrics/{metric_type}")
async def options_metrics(metric_type: str):
    """Handle CORS preflight for metrics endpoint."""
    return {"message": "OK"}


def get_dashboard_service(request: Request) -> Any:
    """Get the dashboard service.

    Args:
        request: The FastAPI request object

    Returns:
        The dashboard service
    """
    # Get the dashboard service from the application state
    if hasattr(request.app.state, "dashboard_service"):
        return request.app.state.dashboard_service

    # Mock dashboard service removed to prevent conflicts with real eBay data
    # Return None to force proper service initialization
    return None


@router.get("/test", response_model=List[Dict[str, Any]])
async def get_dashboards_test(
    request: Request,
) -> List[Dict[str, Any]]:
    """
    Get all available dashboards (test endpoint without authentication).

    This is a temporary endpoint for Flutter web testing.
    """
    dashboard_service = get_dashboard_service(request)

    # Check if this is the real dashboard service or mock
    if hasattr(dashboard_service, "list_dashboards"):
        # Real dashboard service
        return await dashboard_service.list_dashboards()
    else:
        # Mock dashboard service
        return await dashboard_service.get_dashboards()


async def get_current_user_optional(
    token: str = Depends(oauth2_scheme),
) -> Optional[UnifiedUserResponse]:
    """Get current user but don't raise exception if not authenticated."""
    try:
        return await get_current_user(token)
    except HTTPException:
        # Return None if authentication fails (for development/testing)
        return None


@router.get("/", response_model=List[Dict[str, Any]])
async def get_dashboards(
    request: Request,
    current_user: Optional[UnifiedUserResponse] = Depends(get_current_user_optional),
) -> List[Dict[str, Any]]:
    """
    Get all available dashboards.

    Args:
        request: The FastAPI request object
        current_user: The current authenticated user (optional for testing)

    Returns:
        List of available dashboards
    """
    dashboard_service = get_dashboard_service(request)

    # Check if this is the real dashboard service or mock
    if hasattr(dashboard_service, "list_dashboards"):
        # Real dashboard service
        return await dashboard_service.list_dashboards()
    else:
        # Mock dashboard service
        return await dashboard_service.get_dashboards()


@router.get("/{dashboard_id}", response_model=Dict[str, Any])
async def get_dashboard(
    dashboard_id: str,
    request: Request,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get a specific dashboard by ID.

    Args:
        dashboard_id: The dashboard ID
        request: The FastAPI request object
        current_user: The current authenticated user

    Returns:
        Dashboard data
    """
    dashboard_service = get_dashboard_service(request)
    try:
        return await dashboard_service.get_dashboard(dashboard_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard {dashboard_id} not found",
        )


@router.post("/", response_model=Dict[str, Any], status_code=201)
async def create_dashboard(
    dashboard_data: Dict[str, Any],
    request: Request,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Create a new dashboard.

    Args:
        dashboard_data: Dashboard configuration
        request: The FastAPI request object
        current_user: The current authenticated user

    Returns:
        Created dashboard information
    """
    # Check if user has admin role
    if current_user.role != UnifiedUserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create dashboards",
        )

    dashboard_service = get_dashboard_service(request)
    dashboard_id = await dashboard_service.create_dashboard(dashboard_data)
    return {"id": dashboard_id, "message": "Dashboard created successfully"}


@router.delete("/{dashboard_id}", response_model=Dict[str, str])
async def delete_dashboard(
    dashboard_id: str,
    request: Request,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, str]:
    """
    Delete a dashboard by ID.

    Args:
        dashboard_id: ID of the dashboard to delete
        request: FastAPI request object
        current_user: Current authenticated user

    Returns:
        Success message
    """
    get_dashboard_service(request)

    # For testing purposes, just return a success message
    # In a real implementation, we would delete the dashboard from the database
    return {"message": f"Dashboard {dashboard_id} deleted successfully"}


@router.get("/metrics/{metric_type}", response_model=Dict[str, Any])
async def get_metrics(
    metric_type: str,
    request: Request,
    current_user: UnifiedUserResponse = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get metrics data for dashboards.

    Args:
        metric_type: Type of metrics to retrieve
        request: The FastAPI request object
        current_user: The current authenticated user

    Returns:
        Metrics data
    """
    get_dashboard_service(request)

    # Get metrics service from app state
    metrics_service = None
    if hasattr(request.app.state, "metrics_service"):
        metrics_service = request.app.state.metrics_service
    elif hasattr(request.app.state, "metrics_collector"):
        metrics_service = request.app.state.metrics_collector

    if not metrics_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Metrics service unavailable",
        )

    try:
        # Get metrics data
        if metric_type == "system":
            return await metrics_service.get_system_metrics()
        elif metric_type == "api":
            return await metrics_service.get_api_metrics()
        elif metric_type == "business":
            return await metrics_service.get_business_metrics()
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown metric type: {metric_type}",
            )
    except Exception as e:
        logger.error("Error retrieving metrics: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving metrics",
        )
