"""
AI Performance Monitoring API Routes for FlipSync.

Provides endpoints for monitoring AI system performance, health status,
and performance metrics.
"""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from fs_agt_clean.core.monitoring.ai_performance_monitor import (
    get_ai_health_status,
    get_ai_performance_monitor,
    get_ai_performance_summary,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def get_ai_health() -> Dict[str, Any]:
    """Get current AI system health status."""
    try:
        health_status = get_ai_health_status()
        return health_status
    except Exception as e:
        logger.error(f"Error getting AI health status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI health status")


@router.get("/performance")
async def get_ai_performance(
    last_n_requests: int = Query(
        default=100, ge=1, le=1000, description="Number of recent requests to analyze"
    )
) -> Dict[str, Any]:
    """Get AI performance summary for recent requests."""
    try:
        performance_summary = get_ai_performance_summary(last_n_requests)
        return performance_summary
    except Exception as e:
        logger.error(f"Error getting AI performance summary: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get AI performance summary"
        )


@router.get("/metrics")
async def get_ai_metrics(
    format: str = Query(default="json", description="Export format (json)")
) -> Dict[str, Any]:
    """Get detailed AI performance metrics."""
    try:
        monitor = get_ai_performance_monitor()

        if format == "json":
            metrics_json = monitor.export_metrics(format="json")
            return {"format": "json", "data": metrics_json}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except Exception as e:
        logger.error(f"Error exporting AI metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export AI metrics")


@router.get("/status")
async def get_ai_monitoring_status() -> Dict[str, Any]:
    """Get AI monitoring system status."""
    try:
        monitor = get_ai_performance_monitor()

        return {
            "monitoring_enabled": True,
            "metrics_count": len(monitor.metrics_history),
            "max_history": monitor.max_history,
            "alerts_enabled": monitor.alerts_enabled,
            "alert_thresholds": monitor.alert_thresholds,
            "last_updated": (
                monitor.metrics_history[-1].timestamp
                if monitor.metrics_history
                else None
            ),
        }
    except Exception as e:
        logger.error(f"Error getting AI monitoring status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get AI monitoring status"
        )


@router.post("/test")
async def test_ai_performance() -> Dict[str, Any]:
    """Test AI performance with a simple request."""
    try:
        import time

        from fs_agt_clean.core.ai.simple_llm_client import (
            ModelType,
            SimpleLLMClientFactory,
        )

        # Create a test client
        client = SimpleLLMClientFactory.create_ollama_client(
            model_type=ModelType.GEMMA_7B, temperature=0.7
        )

        # Test prompt
        test_prompt = "Hello, this is a test."

        # Measure performance
        start_time = time.time()
        try:
            response = await client.generate_response(prompt=test_prompt)
            success = True
            error_message = None
        except Exception as e:
            response = None
            success = False
            error_message = str(e)

        response_time = time.time() - start_time

        return {
            "test_completed": True,
            "success": success,
            "response_time": response_time,
            "error_message": error_message,
            "response_preview": response.content[:100] if response else None,
            "model": client.model,
            "provider": client.provider.value,
        }

    except Exception as e:
        logger.error(f"Error testing AI performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to test AI performance")


@router.delete("/metrics")
async def clear_ai_metrics() -> Dict[str, Any]:
    """Clear all stored AI performance metrics."""
    try:
        monitor = get_ai_performance_monitor()
        metrics_count = len(monitor.metrics_history)
        monitor.clear_metrics()

        return {
            "cleared": True,
            "metrics_cleared": metrics_count,
            "message": f"Cleared {metrics_count} performance metrics",
        }
    except Exception as e:
        logger.error(f"Error clearing AI metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear AI metrics")


@router.get("/alerts")
async def get_ai_alerts() -> Dict[str, Any]:
    """Get current AI alert configuration and recent alerts."""
    try:
        monitor = get_ai_performance_monitor()

        # Get recent failed requests as alerts
        recent_metrics = list(monitor.metrics_history)[-50:]  # Last 50 requests
        alerts = []

        for metrics in recent_metrics:
            if not metrics.success:
                alerts.append(
                    {
                        "timestamp": metrics.timestamp,
                        "type": "error",
                        "message": f"AI request failed: {metrics.error_message}",
                        "model": metrics.model_name,
                        "response_time": metrics.response_time,
                    }
                )
            elif (
                metrics.response_time
                >= monitor.alert_thresholds["response_time_critical"]
            ):
                alerts.append(
                    {
                        "timestamp": metrics.timestamp,
                        "type": "critical",
                        "message": f"Critical response time: {metrics.response_time:.1f}s",
                        "model": metrics.model_name,
                        "response_time": metrics.response_time,
                    }
                )
            elif (
                metrics.response_time
                >= monitor.alert_thresholds["response_time_warning"]
            ):
                alerts.append(
                    {
                        "timestamp": metrics.timestamp,
                        "type": "warning",
                        "message": f"Slow response time: {metrics.response_time:.1f}s",
                        "model": metrics.model_name,
                        "response_time": metrics.response_time,
                    }
                )

        return {
            "alert_thresholds": monitor.alert_thresholds,
            "alerts_enabled": monitor.alerts_enabled,
            "recent_alerts": alerts[-20:],  # Last 20 alerts
            "alert_count": len(alerts),
        }

    except Exception as e:
        logger.error(f"Error getting AI alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get AI alerts")
