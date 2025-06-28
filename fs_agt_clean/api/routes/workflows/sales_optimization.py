"""
Sales Optimization Workflow API endpoints for FlipSync.

This module provides REST API endpoints for the Sales Optimization Workflow,
enabling competitive analysis, pricing strategy, listing updates, and ROI optimization.
"""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from fs_agt_clean.core.agents.real_agent_manager import RealUnifiedAgentManager
from fs_agt_clean.core.pipeline.controller import PipelineController
from fs_agt_clean.core.state_management.state_manager import StateManager
from fs_agt_clean.services.agent_orchestration import UnifiedAgentOrchestrationService
from fs_agt_clean.services.workflows.sales_optimization import (
    SalesOptimizationRequest,
    SalesOptimizationResult,
    SalesOptimizationWorkflow,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows/sales-optimization", tags=["Sales Optimization"])


class SalesOptimizationRequestModel(BaseModel):
    """API model for sales optimization request."""
    
    product_id: str = Field(..., description="Product identifier for optimization")
    marketplace: str = Field(default="ebay", description="Target marketplace (ebay, amazon)")
    current_price: Optional[Decimal] = Field(None, description="Current product price")
    optimization_goals: List[str] = Field(
        default=["profit", "velocity"], 
        description="Optimization goals (profit, velocity, market_share)"
    )
    time_horizon: str = Field(
        default="30_days", 
        description="Time horizon for optimization (7_days, 30_days, 90_days)"
    )
    risk_tolerance: str = Field(
        default="moderate", 
        description="Risk tolerance level (conservative, moderate, aggressive)"
    )
    user_context: Dict[str, Any] = Field(default_factory=dict, description="Additional user context")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for WebSocket updates")
    user_id: Optional[str] = Field(None, description="UnifiedUser ID for notifications")


class SalesOptimizationResponseModel(BaseModel):
    """API model for sales optimization response."""
    
    workflow_id: str
    success: bool
    competitive_analysis: Dict[str, Any]
    pricing_strategy: Dict[str, Any]
    listing_updates: Dict[str, Any]
    performance_analytics: Dict[str, Any]
    roi_optimization: Dict[str, Any]
    recommendations_applied: bool
    estimated_impact: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time_seconds: float
    agents_involved: List[str]


class WorkflowStatusModel(BaseModel):
    """API model for workflow status."""
    
    workflow_id: str
    status: str
    current_step: Optional[str] = None
    steps_completed: List[str]
    agents_involved: List[str]
    execution_time: Optional[float] = None
    error_message: Optional[str] = None


class WorkflowMetricsModel(BaseModel):
    """API model for workflow metrics."""
    
    optimizations_started: int
    optimizations_completed: int
    optimizations_failed: int
    average_roi_improvement: float
    average_execution_time: float
    success_rate: float


# Global workflow service instance
_workflow_service: Optional[SalesOptimizationWorkflow] = None


async def get_workflow_service() -> SalesOptimizationWorkflow:
    """Get or create the sales optimization workflow service."""
    global _workflow_service
    
    if _workflow_service is None:
        # Initialize workflow dependencies
        agent_manager = RealUnifiedAgentManager()
        await agent_manager.initialize()
        
        pipeline_controller = PipelineController(agent_manager=agent_manager)
        await pipeline_controller.setup_agent_communication_protocol()
        
        state_manager = StateManager()
        orchestration_service = UnifiedAgentOrchestrationService()
        
        _workflow_service = SalesOptimizationWorkflow(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )
    
    return _workflow_service


@router.post("/optimize", response_model=SalesOptimizationResponseModel)
async def optimize_sales_performance(
    request: SalesOptimizationRequestModel,
    background_tasks: BackgroundTasks,
) -> SalesOptimizationResponseModel:
    """
    Execute sales optimization workflow for a product.
    
    This endpoint coordinates Market UnifiedAgent → Executive UnifiedAgent → Content UnifiedAgent → Logistics UnifiedAgent
    for comprehensive sales optimization with competitive analysis, pricing strategy,
    listing updates, and ROI optimization.
    """
    try:
        logger.info(f"Starting sales optimization for product {request.product_id}")
        
        # Get workflow service
        workflow_service = await get_workflow_service()
        
        # Convert API model to workflow request
        workflow_request = SalesOptimizationRequest(
            product_id=request.product_id,
            marketplace=request.marketplace,
            current_price=request.current_price,
            optimization_goals=request.optimization_goals,
            time_horizon=request.time_horizon,
            risk_tolerance=request.risk_tolerance,
            user_context=request.user_context,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )
        
        # Execute workflow
        result = await workflow_service.optimize_sales_performance(workflow_request)
        
        # Convert result to API response
        response = SalesOptimizationResponseModel(
            workflow_id=result.workflow_id,
            success=result.success,
            competitive_analysis=result.competitive_analysis,
            pricing_strategy=result.pricing_strategy,
            listing_updates=result.listing_updates,
            performance_analytics=result.performance_analytics,
            roi_optimization=result.roi_optimization,
            recommendations_applied=result.recommendations_applied,
            estimated_impact=result.estimated_impact,
            error_message=result.error_message,
            execution_time_seconds=result.execution_time_seconds,
            agents_involved=result.agents_involved,
        )
        
        logger.info(f"Sales optimization completed for workflow {result.workflow_id}")
        return response
        
    except Exception as e:
        logger.error(f"Sales optimization failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sales optimization failed: {str(e)}"
        )


@router.get("/status/{workflow_id}", response_model=WorkflowStatusModel)
async def get_workflow_status(workflow_id: str) -> WorkflowStatusModel:
    """Get the status of a sales optimization workflow."""
    try:
        workflow_service = await get_workflow_service()
        
        # Get workflow state from state manager
        workflow_state = workflow_service.state_manager.get_state(workflow_id)
        
        if not workflow_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return WorkflowStatusModel(
            workflow_id=workflow_id,
            status=workflow_state.get("status", "unknown"),
            current_step=workflow_state.get("current_step"),
            steps_completed=workflow_state.get("steps_completed", []),
            agents_involved=workflow_state.get("agents_involved", []),
            execution_time=workflow_state.get("execution_time"),
            error_message=workflow_state.get("error"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow status: {str(e)}"
        )


@router.get("/metrics", response_model=WorkflowMetricsModel)
async def get_workflow_metrics() -> WorkflowMetricsModel:
    """Get sales optimization workflow performance metrics."""
    try:
        workflow_service = await get_workflow_service()
        metrics = workflow_service.get_workflow_metrics()
        
        # Calculate success rate
        total_workflows = metrics["optimizations_started"]
        success_rate = (
            metrics["optimizations_completed"] / total_workflows * 100
            if total_workflows > 0 else 0.0
        )
        
        return WorkflowMetricsModel(
            optimizations_started=metrics["optimizations_started"],
            optimizations_completed=metrics["optimizations_completed"],
            optimizations_failed=metrics["optimizations_failed"],
            average_roi_improvement=metrics["average_roi_improvement"],
            average_execution_time=metrics["average_execution_time"],
            success_rate=success_rate,
        )
        
    except Exception as e:
        logger.error(f"Failed to get workflow metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow metrics: {str(e)}"
        )


@router.get("/templates")
async def get_workflow_templates() -> Dict[str, Any]:
    """Get available sales optimization workflow templates."""
    try:
        workflow_service = await get_workflow_service()
        orchestration_service = workflow_service.orchestration_service
        
        # Get sales optimization template
        template = orchestration_service.workflow_templates.get("sales_optimization")
        
        if not template:
            return {"error": "Sales optimization template not found"}
        
        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "agent_type": step.agent_type,
                    "dependencies": step.dependencies,
                    "timeout_seconds": step.timeout_seconds,
                }
                for step in template.steps
            ],
            "tags": template.tags,
        }
        
    except Exception as e:
        logger.error(f"Failed to get workflow templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workflow templates: {str(e)}"
        )
