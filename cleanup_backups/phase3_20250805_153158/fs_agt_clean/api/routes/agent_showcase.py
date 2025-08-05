"""
FlipSync Agent Showcase API Routes
Week 3: Frontend Integration Updates

API endpoints for controlling and monitoring the real-time agent showcase system.
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from fs_agt_clean.core.realtime.agent_showcase_system import get_agent_showcase_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/showcase", tags=["Agent Showcase"])


class ShowcaseStatusResponse(BaseModel):
    """Response model for showcase status."""
    is_running: bool
    agents_count: int
    services_count: int
    performance_metrics: Dict[str, Any]
    websocket_endpoint: str


class ShowcaseControlRequest(BaseModel):
    """Request model for showcase control."""
    action: str  # "start" or "stop"


@router.get("/status", response_model=ShowcaseStatusResponse)
async def get_showcase_status():
    """
    Get the current status of the real-time agent showcase system.
    
    Returns:
        ShowcaseStatusResponse: Current showcase status and metrics
    """
    try:
        showcase_system = get_agent_showcase_system()
        
        return ShowcaseStatusResponse(
            is_running=showcase_system.is_running,
            agents_count=4,
            services_count=24,
            performance_metrics=showcase_system.performance_metrics,
            websocket_endpoint="/ws/flipsync"
        )
        
    except Exception as e:
        logger.error(f"Error getting showcase status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get showcase status: {str(e)}"
        )


@router.post("/control")
async def control_showcase(request: ShowcaseControlRequest):
    """
    Control the real-time agent showcase system.
    
    Args:
        request: Control request with action ("start" or "stop")
        
    Returns:
        Dict: Operation result
    """
    try:
        showcase_system = get_agent_showcase_system()
        
        if request.action == "start":
            if showcase_system.is_running:
                return {
                    "success": True,
                    "message": "Showcase is already running",
                    "status": "running"
                }
            
            # Initialize if not already done
            if showcase_system.agent_manager is None:
                success = await showcase_system.initialize()
                if not success:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to initialize showcase system"
                    )
            
            # Start the showcase
            await showcase_system.start_showcase()
            
            return {
                "success": True,
                "message": "Real-time agent showcase started successfully",
                "status": "running",
                "agents_count": 4,
                "services_count": 24,
                "websocket_endpoint": "/ws/flipsync"
            }
            
        elif request.action == "stop":
            if not showcase_system.is_running:
                return {
                    "success": True,
                    "message": "Showcase is already stopped",
                    "status": "stopped"
                }
            
            # Stop the showcase
            await showcase_system.stop_showcase()
            
            return {
                "success": True,
                "message": "Real-time agent showcase stopped successfully",
                "status": "stopped",
                "performance_summary": showcase_system.performance_metrics
            }
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid action: {request.action}. Use 'start' or 'stop'"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling showcase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to control showcase: {str(e)}"
        )


@router.get("/metrics")
async def get_showcase_metrics():
    """
    Get detailed performance metrics from the showcase system.
    
    Returns:
        Dict: Detailed performance metrics
    """
    try:
        showcase_system = get_agent_showcase_system()
        
        return {
            "success": True,
            "is_running": showcase_system.is_running,
            "performance_metrics": showcase_system.performance_metrics,
            "system_info": {
                "agents_count": 4,
                "services_count": 24,
                "websocket_endpoint": "/ws/flipsync",
                "showcase_scenarios": len(showcase_system.showcase_scenarios)
            },
            "agent_types": ["market", "content", "logistics", "executive"],
            "service_categories": [
                "pricing_service",
                "content_generation", 
                "route_optimization",
                "strategic_planning",
                "competitor_analysis",
                "seo_optimization"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting showcase metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get showcase metrics: {str(e)}"
        )


@router.get("/scenarios")
async def get_showcase_scenarios():
    """
    Get available showcase scenarios.
    
    Returns:
        Dict: Available showcase scenarios
    """
    try:
        showcase_system = get_agent_showcase_system()
        
        return {
            "success": True,
            "scenarios": showcase_system.showcase_scenarios,
            "total_scenarios": len(showcase_system.showcase_scenarios)
        }
        
    except Exception as e:
        logger.error(f"Error getting showcase scenarios: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get showcase scenarios: {str(e)}"
        )


@router.post("/initialize")
async def initialize_showcase():
    """
    Initialize the showcase system without starting it.
    
    Returns:
        Dict: Initialization result
    """
    try:
        showcase_system = get_agent_showcase_system()
        
        if showcase_system.agent_manager is not None:
            return {
                "success": True,
                "message": "Showcase system is already initialized",
                "status": "initialized"
            }
        
        success = await showcase_system.initialize()
        
        if success:
            return {
                "success": True,
                "message": "Showcase system initialized successfully",
                "status": "initialized",
                "agents_count": 4,
                "services_count": 24
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize showcase system"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing showcase: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize showcase: {str(e)}"
        )
