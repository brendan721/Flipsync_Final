"""
Enhanced monitoring API routes with historical metrics and alerting.

This module provides API endpoints for:
- Historical metrics retrieval and analysis
- Alert management and lifecycle
- Dashboard data aggregation
- Performance monitoring
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from fs_agt_clean.database.models.metrics import (
    AlertCategory,
    AlertLevel,
    AlertSource,
    MetricCategory,
    MetricType,
)
from fs_agt_clean.services.monitoring.alert_service import EnhancedAlertService
from fs_agt_clean.services.monitoring.metrics_service import MetricsService

# Initialize logger
logger = logging.getLogger(__name__)

# Define router
router = APIRouter(prefix="/enhanced-monitoring", tags=["enhanced-monitoring"])


# Request/Response Models
class MetricDataPointRequest(BaseModel):
    """Request model for storing metric data points."""

    name: str = Field(..., description="Metric name")
    value: float = Field(..., description="Metric value")
    type: MetricType = Field(MetricType.GAUGE, description="Metric type")
    category: MetricCategory = Field(
        MetricCategory.SYSTEM, description="Metric category"
    )
    labels: Optional[Dict[str, str]] = Field(None, description="Optional labels/tags")
    agent_id: Optional[str] = Field(None, description="Optional agent identifier")
    service_name: Optional[str] = Field(None, description="Optional service name")


class AlertRequest(BaseModel):
    """Request model for creating alerts."""

    title: str = Field(..., description="Alert title")
    message: str = Field(..., description="Alert message")
    level: AlertLevel = Field(AlertLevel.INFO, description="Alert level")
    category: AlertCategory = Field(AlertCategory.SYSTEM, description="Alert category")
    source: AlertSource = Field(AlertSource.SYSTEM, description="Alert source")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Optional alert details"
    )
    labels: Optional[Dict[str, str]] = Field(None, description="Optional alert labels")
    correlation_id: Optional[str] = Field(None, description="Optional correlation ID")


class AlertAcknowledgeRequest(BaseModel):
    """Request model for acknowledging alerts."""

    acknowledged_by: str = Field(..., description="UnifiedUser who acknowledged the alert")
    notes: Optional[str] = Field(None, description="Optional acknowledgment notes")


class AlertResolveRequest(BaseModel):
    """Request model for resolving alerts."""

    resolved_by: str = Field(..., description="UnifiedUser who resolved the alert")
    resolution_notes: Optional[str] = Field(
        None, description="Optional resolution notes"
    )


# Dependency injection helpers
async def get_metrics_service(request: Request) -> MetricsService:
    """Get metrics service from app state."""
    database = getattr(request.app.state, "database", None)
    if not database:
        raise HTTPException(status_code=500, detail="Database not available")
    return MetricsService(database)


async def get_alert_service(request: Request) -> EnhancedAlertService:
    """Get alert service from app state."""
    database = getattr(request.app.state, "database", None)
    if not database:
        raise HTTPException(status_code=500, detail="Database not available")
    return EnhancedAlertService(database)


# Metrics Endpoints
@router.post("/metrics/data-points")
async def store_metric_data_point(
    metric_request: MetricDataPointRequest,
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> Dict[str, str]:
    """Store a metric data point.

    Args:
        metric_request: Metric data point request
        metrics_service: Metrics service dependency

    Returns:
        Dictionary with the stored metric ID
    """
    try:
        metric_id = await metrics_service.store_metric_data_point(
            name=metric_request.name,
            value=metric_request.value,
            metric_type=metric_request.type,
            category=metric_request.category,
            labels=metric_request.labels,
            agent_id=metric_request.agent_id,
            service_name=metric_request.service_name,
        )

        return {"metric_id": metric_id, "status": "stored"}
    except Exception as e:
        logger.error(f"Error storing metric data point: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/data-points")
async def get_metric_data_points(
    name: Optional[str] = Query(None, description="Metric name filter"),
    category: Optional[MetricCategory] = Query(None, description="Category filter"),
    agent_id: Optional[str] = Query(None, description="UnifiedAgent ID filter"),
    service_name: Optional[str] = Query(None, description="Service name filter"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(100, description="Maximum number of results"),
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> List[Dict[str, Any]]:
    """Retrieve metric data points with filtering.

    Args:
        Various filter parameters
        metrics_service: Metrics service dependency

    Returns:
        List of metric data points
    """
    try:
        metrics = await metrics_service.get_metric_data_points(
            name=name,
            category=category,
            agent_id=agent_id,
            service_name=service_name,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return metrics
    except Exception as e:
        logger.error(f"Error retrieving metric data points: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/system/history")
async def get_system_metrics_history(
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    service_name: Optional[str] = Query(None, description="Service name filter"),
    limit: int = Query(100, description="Maximum number of results"),
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> List[Dict[str, Any]]:
    """Retrieve system metrics history.

    Args:
        Various filter parameters
        metrics_service: Metrics service dependency

    Returns:
        List of system metrics snapshots
    """
    try:
        metrics = await metrics_service.get_system_metrics_history(
            start_time=start_time,
            end_time=end_time,
            service_name=service_name,
            limit=limit,
        )

        return metrics
    except Exception as e:
        logger.error(f"Error retrieving system metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/agents/history")
async def get_agent_metrics_history(
    agent_id: Optional[str] = Query(None, description="UnifiedAgent ID filter"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(100, description="Maximum number of results"),
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> List[Dict[str, Any]]:
    """Retrieve agent metrics history.

    Args:
        Various filter parameters
        metrics_service: Metrics service dependency

    Returns:
        List of agent metrics snapshots
    """
    try:
        metrics = await metrics_service.get_agent_metrics_history(
            agent_id=agent_id, start_time=start_time, end_time=end_time, limit=limit
        )

        return metrics
    except Exception as e:
        logger.error(f"Error retrieving agent metrics history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/summary")
async def get_metrics_summary(
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    metrics_service: MetricsService = Depends(get_metrics_service),
) -> Dict[str, Any]:
    """Get metrics summary for the specified time period.

    Args:
        start_time: Optional start time filter
        end_time: Optional end time filter
        metrics_service: Metrics service dependency

    Returns:
        Metrics summary dictionary
    """
    try:
        summary = await metrics_service.get_metrics_summary(
            start_time=start_time, end_time=end_time
        )

        return summary
    except Exception as e:
        logger.error(f"Error retrieving metrics summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Alert Endpoints
@router.post("/alerts")
async def create_alert(
    alert_request: AlertRequest,
    alert_service: EnhancedAlertService = Depends(get_alert_service),
) -> Dict[str, Any]:
    """Create a new alert.

    Args:
        alert_request: Alert creation request
        alert_service: Alert service dependency

    Returns:
        Dictionary with alert creation result
    """
    try:
        alert_id = await alert_service.create_alert(
            title=alert_request.title,
            message=alert_request.message,
            level=alert_request.level,
            category=alert_request.category,
            source=alert_request.source,
            details=alert_request.details,
            labels=alert_request.labels,
            correlation_id=alert_request.correlation_id,
        )

        if alert_id:
            return {"alert_id": alert_id, "status": "created"}
        else:
            return {"status": "deduplicated", "message": "Alert was deduplicated"}
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_alerts(
    level: Optional[AlertLevel] = Query(None, description="Alert level filter"),
    category: Optional[AlertCategory] = Query(
        None, description="Alert category filter"
    ),
    source: Optional[AlertSource] = Query(None, description="Alert source filter"),
    acknowledged: Optional[bool] = Query(None, description="Acknowledged filter"),
    resolved: Optional[bool] = Query(None, description="Resolved filter"),
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    limit: int = Query(100, description="Maximum number of results"),
    alert_service: EnhancedAlertService = Depends(get_alert_service),
) -> List[Dict[str, Any]]:
    """Retrieve alerts with filtering.

    Args:
        Various filter parameters
        alert_service: Alert service dependency

    Returns:
        List of alerts
    """
    try:
        alerts = await alert_service.get_alerts(
            level=level,
            category=category,
            source=source,
            acknowledged=acknowledged,
            resolved=resolved,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        return alerts
    except Exception as e:
        logger.error(f"Error retrieving alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledge_request: AlertAcknowledgeRequest,
    alert_service: EnhancedAlertService = Depends(get_alert_service),
) -> Dict[str, str]:
    """Acknowledge an alert.

    Args:
        alert_id: Alert ID to acknowledge
        acknowledge_request: Acknowledgment request
        alert_service: Alert service dependency

    Returns:
        Dictionary with acknowledgment result
    """
    try:
        success = await alert_service.acknowledge_alert(
            alert_id=alert_id,
            acknowledged_by=acknowledge_request.acknowledged_by,
            notes=acknowledge_request.notes,
        )

        if success:
            return {"status": "acknowledged", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolve_request: AlertResolveRequest,
    alert_service: EnhancedAlertService = Depends(get_alert_service),
) -> Dict[str, str]:
    """Resolve an alert.

    Args:
        alert_id: Alert ID to resolve
        resolve_request: Resolution request
        alert_service: Alert service dependency

    Returns:
        Dictionary with resolution result
    """
    try:
        success = await alert_service.resolve_alert(
            alert_id=alert_id,
            resolved_by=resolve_request.resolved_by,
            resolution_notes=resolve_request.resolution_notes,
        )

        if success:
            return {"status": "resolved", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="Alert not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resolving alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts/summary")
async def get_alert_summary(
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    alert_service: EnhancedAlertService = Depends(get_alert_service),
) -> Dict[str, Any]:
    """Get alert summary statistics.

    Args:
        start_time: Optional start time filter
        end_time: Optional end time filter
        alert_service: Alert service dependency

    Returns:
        Alert summary dictionary
    """
    try:
        summary = await alert_service.get_alert_summary(
            start_time=start_time, end_time=end_time
        )

        return summary
    except Exception as e:
        logger.error(f"Error retrieving alert summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard Endpoints
@router.get("/dashboard/overview")
async def get_dashboard_overview(
    start_time: Optional[datetime] = Query(None, description="Start time filter"),
    end_time: Optional[datetime] = Query(None, description="End time filter"),
    metrics_service: MetricsService = Depends(get_metrics_service),
    alert_service: EnhancedAlertService = Depends(get_alert_service),
) -> Dict[str, Any]:
    """Get dashboard overview with metrics and alerts summary.

    Args:
        start_time: Optional start time filter
        end_time: Optional end time filter
        metrics_service: Metrics service dependency
        alert_service: Alert service dependency

    Returns:
        Dashboard overview dictionary
    """
    try:
        # Get metrics summary
        metrics_summary = await metrics_service.get_metrics_summary(
            start_time=start_time, end_time=end_time
        )

        # Get alert summary
        alert_summary = await alert_service.get_alert_summary(
            start_time=start_time, end_time=end_time
        )

        # Get recent system metrics
        recent_system_metrics = await metrics_service.get_system_metrics_history(
            start_time=start_time, end_time=end_time, limit=10
        )

        # Get recent alerts
        recent_alerts = await alert_service.get_alerts(
            start_time=start_time, end_time=end_time, limit=10
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics_summary": metrics_summary,
            "alert_summary": alert_summary,
            "recent_system_metrics": recent_system_metrics,
            "recent_alerts": recent_alerts,
        }
    except Exception as e:
        logger.error(f"Error retrieving dashboard overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))
