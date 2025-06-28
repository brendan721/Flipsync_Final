"""
Real-time UnifiedAgent Status Dashboard API routes for FlipSync Frontend Integration.

This module provides API endpoints for the real-time dashboard with comprehensive
agent monitoring, workflow progress visualization, and performance metrics.

Features:
- Real-time dashboard data endpoints
- WebSocket dashboard connections for live updates
- Integration with existing API endpoints and WebSocket chat system
- Comprehensive agent status monitoring
- Workflow progress visualization
- Performance metrics and system health monitoring
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from fs_agt_clean.api.dependencies.dependencies import (
    get_agent_manager,
    get_orchestration_service,
    get_pipeline_controller,
    get_state_manager,
)
from fs_agt_clean.core.agents.real_agent_manager import RealUnifiedAgentManager
from fs_agt_clean.core.pipeline.controller import PipelineController
from fs_agt_clean.core.state_management.state_manager import StateManager
from fs_agt_clean.services.agent_orchestration import UnifiedAgentOrchestrationService
from fs_agt_clean.services.dashboard.real_time_dashboard import (
    UnifiedAgentStatusMetrics,
    DashboardUpdate,
    RealTimeDashboardService,
    SystemPerformanceMetrics,
    WorkflowProgressMetrics,
)

logger = logging.getLogger(__name__)

# Initialize router with v1 prefix for dashboard endpoints
router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/status", response_model=Dict[str, Any])
async def get_dashboard_status(
    include_agents: bool = Query(default=True, description="Include agent metrics"),
    include_workflows: bool = Query(
        default=True, description="Include workflow metrics"
    ),
    include_system: bool = Query(default=True, description="Include system metrics"),
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(
        get_orchestration_service
    ),
):
    """
    Get current dashboard status with comprehensive metrics.

    This endpoint provides:
    - Real-time agent status and health metrics
    - Active workflow progress and completion status
    - System performance metrics and health indicators
    - Integration with existing enhanced agent status endpoint
    """
    try:
        logger.info("Dashboard status request received")

        # Create dashboard service
        dashboard_service = RealTimeDashboardService(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )

        # Start dashboard service temporarily
        await dashboard_service.start_dashboard_service()

        # Wait for initial metrics collection
        await asyncio.sleep(2)

        # Get current dashboard state
        dashboard_update = await dashboard_service.get_current_dashboard_state()

        # Build response based on requested components
        response_data = {
            "timestamp": dashboard_update.timestamp,
            "update_type": "status_request",
            "dashboard_active": True,
            "clients_connected": len(dashboard_service.dashboard_clients),
        }

        if include_agents and dashboard_update.agent_metrics:
            response_data["agent_metrics"] = {
                "total_agents": len(dashboard_update.agent_metrics),
                "agents_by_type": {},
                "agents_by_status": {},
                "average_health_score": 0.0,
                "average_utilization": 0.0,
                "agents": [agent.dict() for agent in dashboard_update.agent_metrics],
            }

            # Calculate agent statistics
            total_health = 0.0
            total_utilization = 0.0

            for agent in dashboard_update.agent_metrics:
                # Count by type
                agent_type = agent.agent_type
                response_data["agent_metrics"]["agents_by_type"][agent_type] = (
                    response_data["agent_metrics"]["agents_by_type"].get(agent_type, 0)
                    + 1
                )

                # Count by status
                status = agent.status
                response_data["agent_metrics"]["agents_by_status"][status] = (
                    response_data["agent_metrics"]["agents_by_status"].get(status, 0)
                    + 1
                )

                # Accumulate for averages
                total_health += agent.health_score
                total_utilization += agent.utilization_percentage

            # Calculate averages
            agent_count = len(dashboard_update.agent_metrics)
            if agent_count > 0:
                response_data["agent_metrics"]["average_health_score"] = (
                    total_health / agent_count
                )
                response_data["agent_metrics"]["average_utilization"] = (
                    total_utilization / agent_count
                )

        if include_workflows and dashboard_update.workflow_metrics:
            response_data["workflow_metrics"] = {
                "total_workflows": len(dashboard_update.workflow_metrics),
                "workflows_by_status": {},
                "workflows_by_type": {},
                "average_progress": 0.0,
                "workflows": [
                    workflow.dict() for workflow in dashboard_update.workflow_metrics
                ],
            }

            # Calculate workflow statistics
            total_progress = 0.0

            for workflow in dashboard_update.workflow_metrics:
                # Count by status
                status = workflow.status
                response_data["workflow_metrics"]["workflows_by_status"][status] = (
                    response_data["workflow_metrics"]["workflows_by_status"].get(
                        status, 0
                    )
                    + 1
                )

                # Count by type
                workflow_type = workflow.workflow_type
                response_data["workflow_metrics"]["workflows_by_type"][
                    workflow_type
                ] = (
                    response_data["workflow_metrics"]["workflows_by_type"].get(
                        workflow_type, 0
                    )
                    + 1
                )

                # Accumulate progress
                total_progress += workflow.progress_percentage

            # Calculate average progress
            workflow_count = len(dashboard_update.workflow_metrics)
            if workflow_count > 0:
                response_data["workflow_metrics"]["average_progress"] = (
                    total_progress / workflow_count
                )

        if include_system and dashboard_update.system_metrics:
            response_data["system_metrics"] = dashboard_update.system_metrics.dict()

        # Include alerts
        if dashboard_update.alerts:
            response_data["alerts"] = dashboard_update.alerts

        # Include metadata
        response_data["metadata"] = dashboard_update.metadata

        # Stop dashboard service
        await dashboard_service.stop_dashboard_service()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "dashboard_status": response_data,
            },
        )

    except Exception as e:
        logger.error(f"Dashboard status request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Dashboard status request failed: {str(e)}",
            },
        )


@router.get("/agents", response_model=Dict[str, Any])
async def get_agent_dashboard_metrics(
    agent_type: Optional[str] = Query(default=None, description="Filter by agent type"),
    status: Optional[str] = Query(default=None, description="Filter by agent status"),
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(
        get_orchestration_service
    ),
):
    """
    Get detailed agent metrics for dashboard visualization.

    This endpoint provides:
    - Detailed agent status and health information
    - UnifiedAgent utilization and performance metrics
    - Task completion statistics
    - Error rates and response times
    """
    try:
        logger.info(
            f"UnifiedAgent dashboard metrics request: type={agent_type}, status={status}"
        )

        # Create dashboard service
        dashboard_service = RealTimeDashboardService(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )

        # Start dashboard service temporarily
        await dashboard_service.start_dashboard_service()
        await asyncio.sleep(2)

        # Get current dashboard state
        dashboard_update = await dashboard_service.get_current_dashboard_state()

        if not dashboard_update.agent_metrics:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "agent_metrics": {
                        "total_agents": 0,
                        "filtered_agents": 0,
                        "agents": [],
                    },
                },
            )

        # Filter agents based on query parameters
        filtered_agents = dashboard_update.agent_metrics

        if agent_type:
            filtered_agents = [
                agent for agent in filtered_agents if agent.agent_type == agent_type
            ]

        if status:
            filtered_agents = [
                agent for agent in filtered_agents if agent.status == status
            ]

        # Calculate summary statistics
        total_tasks = sum(agent.tasks_completed for agent in filtered_agents)
        total_errors = sum(agent.error_count for agent in filtered_agents)
        avg_response_time = (
            sum(agent.average_response_time for agent in filtered_agents)
            / len(filtered_agents)
            if filtered_agents
            else 0.0
        )
        avg_health_score = (
            sum(agent.health_score for agent in filtered_agents) / len(filtered_agents)
            if filtered_agents
            else 0.0
        )

        # Stop dashboard service before returning
        await dashboard_service.stop_dashboard_service()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "agent_metrics": {
                    "total_agents": len(dashboard_update.agent_metrics),
                    "filtered_agents": len(filtered_agents),
                    "summary": {
                        "total_tasks_completed": total_tasks,
                        "total_errors": total_errors,
                        "average_response_time": avg_response_time,
                        "average_health_score": avg_health_score,
                    },
                    "agents": [agent.dict() for agent in filtered_agents],
                },
            },
        )

    except Exception as e:
        logger.error(f"UnifiedAgent dashboard metrics request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"UnifiedAgent metrics request failed: {str(e)}",
            },
        )


@router.get("/workflows", response_model=Dict[str, Any])
async def get_workflow_dashboard_metrics(
    workflow_type: Optional[str] = Query(
        default=None, description="Filter by workflow type"
    ),
    status: Optional[str] = Query(
        default=None, description="Filter by workflow status"
    ),
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(
        get_orchestration_service
    ),
):
    """
    Get detailed workflow metrics for dashboard visualization.

    This endpoint provides:
    - Active workflow progress and status
    - Workflow execution times and completion rates
    - UnifiedAgent coordination statistics
    - Workflow performance metrics
    """
    try:
        logger.info(
            f"Workflow dashboard metrics request: type={workflow_type}, status={status}"
        )

        # Create dashboard service
        dashboard_service = RealTimeDashboardService(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )

        # Start dashboard service temporarily
        await dashboard_service.start_dashboard_service()
        await asyncio.sleep(3)

        # Get current dashboard state
        dashboard_update = await dashboard_service.get_current_dashboard_state()

        if not dashboard_update.workflow_metrics:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "workflow_metrics": {
                        "total_workflows": 0,
                        "filtered_workflows": 0,
                        "workflows": [],
                    },
                },
            )

        # Filter workflows based on query parameters
        filtered_workflows = dashboard_update.workflow_metrics

        if workflow_type:
            filtered_workflows = [
                wf for wf in filtered_workflows if wf.workflow_type == workflow_type
            ]

        if status:
            filtered_workflows = [
                wf for wf in filtered_workflows if wf.status == status
            ]

        # Calculate summary statistics
        avg_progress = (
            sum(wf.progress_percentage for wf in filtered_workflows)
            / len(filtered_workflows)
            if filtered_workflows
            else 0.0
        )
        avg_execution_time = (
            sum(wf.execution_time_seconds for wf in filtered_workflows)
            / len(filtered_workflows)
            if filtered_workflows
            else 0.0
        )
        total_agents_involved = len(
            set(agent for wf in filtered_workflows for agent in wf.agents_involved)
        )

        # Stop dashboard service before returning
        await dashboard_service.stop_dashboard_service()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "workflow_metrics": {
                    "total_workflows": len(dashboard_update.workflow_metrics),
                    "filtered_workflows": len(filtered_workflows),
                    "summary": {
                        "average_progress": avg_progress,
                        "average_execution_time": avg_execution_time,
                        "total_agents_involved": total_agents_involved,
                    },
                    "workflows": [workflow.dict() for workflow in filtered_workflows],
                },
            },
        )

    except Exception as e:
        logger.error(f"Workflow dashboard metrics request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Workflow metrics request failed: {str(e)}",
            },
        )


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_dashboard_metrics(
    time_range: str = Query(
        default="1h", description="Time range for metrics (1h, 6h, 24h)"
    ),
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(
        get_orchestration_service
    ),
):
    """
    Get system performance metrics for dashboard monitoring.

    This endpoint provides:
    - System resource utilization (CPU, memory)
    - API response time statistics
    - UnifiedAgent coordination performance
    - Error rates and system health indicators
    """
    try:
        logger.info(f"Performance dashboard metrics request: time_range={time_range}")

        # Create dashboard service
        dashboard_service = RealTimeDashboardService(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )

        # Start dashboard service temporarily
        await dashboard_service.start_dashboard_service()
        await asyncio.sleep(6)  # Wait for system metrics collection

        # Get current dashboard state
        dashboard_update = await dashboard_service.get_current_dashboard_state()

        if not dashboard_update.system_metrics:
            return JSONResponse(
                status_code=200,
                content={
                    "success": True,
                    "performance_metrics": {
                        "current_metrics": None,
                        "historical_data": [],
                    },
                },
            )

        # Get historical metrics based on time range
        historical_metrics = dashboard_service.metrics_history

        # Filter based on time range (simplified for demo)
        if time_range == "1h":
            historical_metrics = historical_metrics[
                -12:
            ]  # Last 12 entries (1 hour at 5min intervals)
        elif time_range == "6h":
            historical_metrics = historical_metrics[-72:]  # Last 72 entries
        elif time_range == "24h":
            historical_metrics = historical_metrics  # All available data

        # Calculate performance trends
        if len(historical_metrics) > 1:
            recent_metrics = historical_metrics[-5:]  # Last 5 entries
            avg_api_response = sum(
                m.average_api_response_time for m in recent_metrics
            ) / len(recent_metrics)
            avg_agent_response = sum(
                m.average_agent_response_time for m in recent_metrics
            ) / len(recent_metrics)
            avg_error_rate = sum(m.error_rate for m in recent_metrics) / len(
                recent_metrics
            )
        else:
            avg_api_response = dashboard_update.system_metrics.average_api_response_time
            avg_agent_response = (
                dashboard_update.system_metrics.average_agent_response_time
            )
            avg_error_rate = dashboard_update.system_metrics.error_rate

        # Stop dashboard service before returning
        await dashboard_service.stop_dashboard_service()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "performance_metrics": {
                    "current_metrics": dashboard_update.system_metrics.dict(),
                    "time_range": time_range,
                    "historical_data": [
                        metrics.dict() for metrics in historical_metrics
                    ],
                    "trends": {
                        "average_api_response_time": avg_api_response,
                        "average_agent_response_time": avg_agent_response,
                        "average_error_rate": avg_error_rate,
                    },
                    "performance_indicators": {
                        "api_performance": (
                            "good"
                            if avg_api_response < 1.0
                            else "degraded" if avg_api_response < 2.0 else "poor"
                        ),
                        "agent_performance": (
                            "good"
                            if avg_agent_response < 1.5
                            else "degraded" if avg_agent_response < 3.0 else "poor"
                        ),
                        "system_health": (
                            "healthy"
                            if avg_error_rate < 5.0
                            else "warning" if avg_error_rate < 10.0 else "critical"
                        ),
                    },
                },
            },
        )

    except Exception as e:
        logger.error(f"Performance dashboard metrics request failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Performance metrics request failed: {str(e)}",
            },
        )


@router.websocket("/ws")
async def websocket_dashboard_endpoint(
    websocket: WebSocket,
    client_id: str,
):
    """
    WebSocket endpoint for real-time dashboard updates.

    This endpoint provides:
    - Real-time agent status updates
    - Live workflow progress monitoring
    - System performance metrics streaming
    - Integration with existing WebSocket chat system
    - Automatic client registration and cleanup

    Query Parameters:
    - client_id: Unique client identifier for dashboard connection
    """
    try:
        # Accept WebSocket connection
        await websocket.accept()

        # Create dashboard service for WebSocket connection
        from fs_agt_clean.api.dependencies.dependencies import (
            get_agent_manager,
            get_pipeline_controller,
            get_state_manager,
            get_orchestration_service,
        )

        agent_manager = await get_agent_manager()
        pipeline_controller = await get_pipeline_controller()
        state_manager = await get_state_manager()
        orchestration_service = await get_orchestration_service()

        dashboard_service = RealTimeDashboardService(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )

        # Start dashboard service
        await dashboard_service.start_dashboard_service()

        # Register dashboard client
        await dashboard_service.register_dashboard_client(client_id)

        logger.info(f"Dashboard WebSocket client connected: {client_id}")

        try:
            # Keep connection alive and handle messages
            while True:
                # Wait for messages from client (ping/pong, configuration updates, etc.)
                try:
                    # Set a timeout to periodically check connection
                    message = await asyncio.wait_for(
                        websocket.receive_text(), timeout=30.0
                    )

                    # Handle client messages
                    try:
                        message_data = json.loads(message)
                        message_type = message_data.get("type", "unknown")

                        if message_type == "ping":
                            # Respond to ping with pong
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "pong",
                                        "timestamp": datetime.now(
                                            timezone.utc
                                        ).isoformat(),
                                        "client_id": client_id,
                                    }
                                )
                            )

                        elif message_type == "configure":
                            # Handle dashboard configuration updates
                            config = message_data.get("config", {})
                            logger.info(
                                f"Dashboard configuration update from {client_id}: {config}"
                            )

                            # Send acknowledgment
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "type": "config_ack",
                                        "timestamp": datetime.now(
                                            timezone.utc
                                        ).isoformat(),
                                        "client_id": client_id,
                                        "config": config,
                                    }
                                )
                            )

                        else:
                            logger.warning(
                                f"Unknown message type from dashboard client {client_id}: {message_type}"
                            )

                    except json.JSONDecodeError:
                        logger.warning(
                            f"Invalid JSON from dashboard client {client_id}: {message}"
                        )

                except asyncio.TimeoutError:
                    # Send periodic ping to keep connection alive
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "ping",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                                "server": "dashboard",
                            }
                        )
                    )

        except WebSocketDisconnect:
            logger.info(f"Dashboard WebSocket client disconnected: {client_id}")

    except Exception as e:
        logger.error(f"Dashboard WebSocket error for client {client_id}: {e}")

    finally:
        # Cleanup: unregister dashboard client
        await dashboard_service.unregister_dashboard_client(client_id)
        await dashboard_service.stop_dashboard_service()
        logger.info(f"Dashboard client cleanup completed: {client_id}")


@router.get("/health")
async def get_dashboard_health(
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(
        get_orchestration_service
    ),
):
    """
    Get dashboard service health status.

    This endpoint provides:
    - Dashboard service operational status
    - Connected clients count
    - Background task status
    - Integration health with core services
    """
    try:
        # Create dashboard service
        dashboard_service = RealTimeDashboardService(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )

        # Start dashboard service temporarily
        await dashboard_service.start_dashboard_service()
        await asyncio.sleep(2)

        # Get current dashboard state
        dashboard_update = await dashboard_service.get_current_dashboard_state()

        # Check service health
        service_health = {
            "dashboard_service": "operational",
            "connected_clients": len(dashboard_service.dashboard_clients),
            "background_tasks": len(dashboard_service._background_tasks),
            "metrics_collection": (
                "active" if dashboard_service.metrics_history else "inactive"
            ),
            "last_update": dashboard_update.timestamp,
            "agent_integration": (
                "connected" if dashboard_update.agent_metrics else "disconnected"
            ),
            "workflow_integration": (
                "connected" if dashboard_update.workflow_metrics else "disconnected"
            ),
            "system_metrics": (
                "available" if dashboard_update.system_metrics else "unavailable"
            ),
        }

        # Determine overall health status
        overall_status = "healthy"
        if not dashboard_update.agent_metrics or not dashboard_update.system_metrics:
            overall_status = "degraded"
        if len(dashboard_service._background_tasks) == 0:
            overall_status = "critical"

        # Stop dashboard service before returning
        await dashboard_service.stop_dashboard_service()

        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "dashboard_health": {
                    "overall_status": overall_status,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "service_details": service_health,
                    "uptime_info": {
                        "service_started": True,
                        "metrics_collected": len(dashboard_service.metrics_history),
                        "agents_monitored": len(dashboard_service.agent_metrics_cache),
                        "workflows_tracked": len(dashboard_service.active_workflows),
                    },
                },
            },
        )

    except Exception as e:
        logger.error(f"Dashboard health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Dashboard health check failed: {str(e)}",
            },
        )
