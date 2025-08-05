"""
FlipSync Operational Monitoring API Routes
Week 4: Production Deployment & Operational Excellence - Objective 3

API endpoints for controlling and monitoring operational monitoring & alerting system.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from fs_agt_clean.core.monitoring.operational_monitoring_system import (
    get_operational_monitoring_system,
    AlertSeverity,
    MonitoringStatus
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/monitoring", tags=["Operational Monitoring"])


class MonitoringRequest(BaseModel):
    """Request model for monitoring operations."""
    action: str  # "start", "stop", "status", "configure"
    component_id: Optional[str] = None
    component_type: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class MonitoringStatusResponse(BaseModel):
    """Response model for monitoring status."""
    is_active: bool
    monitored_components: int
    healthy_components: int
    degraded_components: int
    unhealthy_components: int
    active_alerts: int
    monitoring_overhead_ms: float
    alerting_response_ms: float


@router.get("/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status():
    """
    Get the current status of operational monitoring system.
    
    Returns:
        MonitoringStatusResponse: Current monitoring status
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        # Get monitoring report
        monitoring_report = monitoring_system.get_monitoring_report()
        
        # Extract key metrics
        summary = monitoring_report["monitoring_summary"]
        performance = monitoring_report["performance_metrics"]
        health = monitoring_report["health_status"]
        alerts = monitoring_report["alert_statistics"]
        
        return MonitoringStatusResponse(
            is_active=summary["is_active"],
            monitored_components=summary["total_components"],
            healthy_components=health["healthy_components"],
            degraded_components=health["degraded_components"],
            unhealthy_components=health["unhealthy_components"],
            active_alerts=alerts["active_alerts"],
            monitoring_overhead_ms=max(
                performance["agent_monitoring_avg_ms"],
                performance["service_monitoring_avg_ms"]
            ),
            alerting_response_ms=performance["consensus_alerting_avg_ms"]
        )
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring status: {str(e)}"
        )


@router.post("/start")
async def start_monitoring():
    """
    Start the operational monitoring system.
    
    Returns:
        Dict: Monitoring start result
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        if monitoring_system.is_monitoring_active:
            return {
                "success": True,
                "message": "Monitoring system is already active",
                "status": "running"
            }
        
        success = await monitoring_system.initialize()
        
        if success:
            return {
                "success": True,
                "message": "Operational monitoring system started successfully",
                "monitoring_targets": {
                    "agents": len(monitoring_system.monitored_agents),
                    "services": len(monitoring_system.monitored_services),
                    "total_components": len(monitoring_system.monitored_agents) + len(monitoring_system.monitored_services)
                },
                "performance_targets": {
                    "monitoring_overhead_ms": monitoring_system.monitoring_overhead_target_ms,
                    "alerting_response_ms": monitoring_system.alerting_response_target_ms
                },
                "features": {
                    "real_time_monitoring": "Enabled",
                    "automated_recovery": "Enabled",
                    "consensus_alerting": "Enabled",
                    "websocket_integration": "Enabled"
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start monitoring system"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/stop")
async def stop_monitoring():
    """
    Stop the operational monitoring system.
    
    Returns:
        Dict: Monitoring stop result
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        if not monitoring_system.is_monitoring_active:
            return {
                "success": True,
                "message": "Monitoring system is already stopped",
                "status": "stopped"
            }
        
        await monitoring_system.stop_monitoring()
        
        return {
            "success": True,
            "message": "Operational monitoring system stopped successfully",
            "status": "stopped"
        }
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.get("/report")
async def get_monitoring_report():
    """
    Get comprehensive monitoring report.
    
    Returns:
        Dict: Detailed monitoring report
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        monitoring_report = monitoring_system.get_monitoring_report()
        
        # Add additional analysis
        performance = monitoring_report["performance_metrics"]
        targets_analysis = {
            "monitoring_overhead_status": "EXCELLENT" if performance["targets_met"]["monitoring_overhead"] else "NEEDS_IMPROVEMENT",
            "alerting_response_status": "EXCELLENT" if performance["targets_met"]["alerting_response"] else "NEEDS_IMPROVEMENT",
            "overall_performance": "EXCELLENT" if all(performance["targets_met"].values()) else "GOOD"
        }
        
        return {
            "success": True,
            "monitoring_report": monitoring_report,
            "performance_analysis": targets_analysis,
            "recommendations": [
                "✅ All monitoring targets met - system operating optimally" if targets_analysis["overall_performance"] == "EXCELLENT"
                else "⚠️ Some performance targets not met - review system load and optimization"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring report: {str(e)}"
        )


@router.get("/health")
async def get_component_health():
    """
    Get health status of all monitored components.
    
    Returns:
        Dict: Component health status
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        # Get current health status
        agent_health = {}
        service_health = {}
        
        for component_id, status in monitoring_system.current_health_status.items():
            if component_id in monitoring_system.monitored_agents:
                agent_health[component_id] = {
                    "status": status.value,
                    "component_type": "agent",
                    "monitoring_target": monitoring_system.monitored_agents[component_id].dict()
                }
            elif component_id in monitoring_system.monitored_services:
                service_health[component_id] = {
                    "status": status.value,
                    "component_type": "service",
                    "monitoring_target": monitoring_system.monitored_services[component_id].dict()
                }
        
        # Get recent health metrics
        recent_metrics = []
        for metric in list(monitoring_system.health_metrics)[-50:]:  # Last 50 metrics
            recent_metrics.append({
                "component_id": metric.component_id,
                "component_type": metric.component_type,
                "metric_name": metric.metric_name,
                "value": metric.value,
                "threshold": metric.threshold,
                "status": metric.status.value,
                "timestamp": metric.timestamp.isoformat()
            })
        
        return {
            "success": True,
            "agent_health": agent_health,
            "service_health": service_health,
            "health_summary": {
                "total_agents": len(agent_health),
                "total_services": len(service_health),
                "healthy_agents": sum(1 for h in agent_health.values() if h["status"] == "healthy"),
                "healthy_services": sum(1 for h in service_health.values() if h["status"] == "healthy")
            },
            "recent_metrics": recent_metrics
        }
        
    except Exception as e:
        logger.error(f"Error getting component health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get component health: {str(e)}"
        )


@router.get("/alerts")
async def get_alerts():
    """
    Get current alerts and alert history.
    
    Returns:
        Dict: Alert information
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        # Get active alerts
        active_alerts = []
        for alert in monitoring_system.active_alerts.values():
            active_alerts.append({
                "alert_id": alert.alert_id,
                "component_id": alert.component_id,
                "component_type": alert.component_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved
            })
        
        # Get recent alert history
        recent_alerts = []
        for alert in list(monitoring_system.alert_history)[-20:]:  # Last 20 alerts
            recent_alerts.append({
                "alert_id": alert.alert_id,
                "component_id": alert.component_id,
                "component_type": alert.component_type,
                "severity": alert.severity.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            })
        
        # Calculate alert statistics
        severity_counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
        for alert in monitoring_system.alert_history:
            severity_counts[alert.severity.value] += 1
        
        return {
            "success": True,
            "active_alerts": active_alerts,
            "recent_alerts": recent_alerts,
            "alert_statistics": {
                "total_active": len(active_alerts),
                "total_generated": len(monitoring_system.alert_history),
                "severity_distribution": severity_counts
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.get("/performance")
async def get_monitoring_performance():
    """
    Get monitoring system performance metrics.
    
    Returns:
        Dict: Performance metrics
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        # Calculate performance statistics
        agent_monitoring_times = monitoring_system.monitoring_performance.get("agent_monitoring", [])
        service_monitoring_times = monitoring_system.monitoring_performance.get("service_monitoring", [])
        consensus_times = list(monitoring_system.consensus_times)
        
        def calculate_stats(times):
            if not times:
                return {"avg": 0, "min": 0, "max": 0, "count": 0}
            return {
                "avg": sum(times) / len(times),
                "min": min(times),
                "max": max(times),
                "count": len(times)
            }
        
        return {
            "success": True,
            "performance_metrics": {
                "agent_monitoring": calculate_stats(agent_monitoring_times),
                "service_monitoring": calculate_stats(service_monitoring_times),
                "consensus_alerting": calculate_stats(consensus_times)
            },
            "performance_targets": {
                "monitoring_overhead_ms": monitoring_system.monitoring_overhead_target_ms,
                "alerting_response_ms": monitoring_system.alerting_response_target_ms
            },
            "target_compliance": {
                "monitoring_overhead_met": (
                    calculate_stats(agent_monitoring_times)["avg"] <= monitoring_system.monitoring_overhead_target_ms and
                    calculate_stats(service_monitoring_times)["avg"] <= monitoring_system.monitoring_overhead_target_ms
                ),
                "alerting_response_met": calculate_stats(consensus_times)["avg"] <= monitoring_system.alerting_response_target_ms
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting monitoring performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring performance: {str(e)}"
        )


@router.get("/components")
async def get_monitored_components():
    """
    Get list of all monitored components and their configuration.
    
    Returns:
        Dict: Monitored components information
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        # Get agent information
        agents_info = {}
        for agent_id, target in monitoring_system.monitored_agents.items():
            agents_info[agent_id] = {
                "component_type": "agent",
                "health_check_interval_ms": target.health_check_interval_ms,
                "performance_thresholds": target.performance_thresholds,
                "alert_thresholds": target.alert_thresholds,
                "recovery_procedures": target.recovery_procedures,
                "current_status": monitoring_system.current_health_status.get(agent_id, MonitoringStatus.HEALTHY).value
            }
        
        # Get service information
        services_info = {}
        for service_id, target in monitoring_system.monitored_services.items():
            services_info[service_id] = {
                "component_type": "service",
                "health_check_interval_ms": target.health_check_interval_ms,
                "performance_thresholds": target.performance_thresholds,
                "alert_thresholds": target.alert_thresholds,
                "recovery_procedures": target.recovery_procedures,
                "current_status": monitoring_system.current_health_status.get(service_id, MonitoringStatus.HEALTHY).value
            }
        
        return {
            "success": True,
            "monitored_agents": agents_info,
            "monitored_services": services_info,
            "summary": {
                "total_agents": len(agents_info),
                "total_services": len(services_info),
                "total_components": len(agents_info) + len(services_info)
            },
            "monitoring_configuration": monitoring_system.monitoring_config
        }
        
    except Exception as e:
        logger.error(f"Error getting monitored components: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitored components: {str(e)}"
        )


@router.post("/test-monitoring")
async def test_monitoring_system():
    """
    Test the monitoring system with sample operations.
    
    Returns:
        Dict: Test results
    """
    try:
        monitoring_system = get_operational_monitoring_system()
        
        if not monitoring_system.is_monitoring_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitoring system is not active. Start monitoring first."
            )
        
        # Wait for a few monitoring cycles to collect data
        await asyncio.sleep(3)
        
        # Get current performance metrics
        monitoring_report = monitoring_system.get_monitoring_report()
        performance = monitoring_report["performance_metrics"]
        
        # Analyze test results
        test_results = {
            "monitoring_overhead_test": {
                "agent_monitoring_ms": performance["agent_monitoring_avg_ms"],
                "service_monitoring_ms": performance["service_monitoring_avg_ms"],
                "target_ms": monitoring_system.monitoring_overhead_target_ms,
                "target_met": performance["targets_met"]["monitoring_overhead"]
            },
            "alerting_response_test": {
                "consensus_alerting_ms": performance["consensus_alerting_avg_ms"],
                "target_ms": monitoring_system.alerting_response_target_ms,
                "target_met": performance["targets_met"]["alerting_response"]
            },
            "component_coverage_test": {
                "monitored_agents": len(monitoring_system.monitored_agents),
                "monitored_services": len(monitoring_system.monitored_services),
                "expected_agents": 4,
                "expected_services": 24,
                "coverage_complete": len(monitoring_system.monitored_agents) >= 4 and len(monitoring_system.monitored_services) >= 24
            }
        }
        
        # Calculate overall test result
        all_tests_passed = (
            test_results["monitoring_overhead_test"]["target_met"] and
            test_results["alerting_response_test"]["target_met"] and
            test_results["component_coverage_test"]["coverage_complete"]
        )
        
        return {
            "success": True,
            "test_summary": {
                "overall_result": "PASSED" if all_tests_passed else "PARTIAL",
                "monitoring_overhead_status": "PASSED" if test_results["monitoring_overhead_test"]["target_met"] else "FAILED",
                "alerting_response_status": "PASSED" if test_results["alerting_response_test"]["target_met"] else "FAILED",
                "component_coverage_status": "PASSED" if test_results["component_coverage_test"]["coverage_complete"] else "FAILED"
            },
            "test_results": test_results,
            "recommendations": [
                "✅ All monitoring tests passed - system ready for production" if all_tests_passed
                else "⚠️ Some tests failed - review system configuration and performance"
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing monitoring system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test monitoring system: {str(e)}"
        )
