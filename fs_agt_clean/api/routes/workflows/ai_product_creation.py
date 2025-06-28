"""
API endpoints for AI-Powered Product Creation Workflow.

This module provides REST API endpoints for the sophisticated multi-agent
product creation workflow that generates products from images.
"""

import asyncio
import base64
import logging
from typing import Dict, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from fs_agt_clean.core.agents.real_agent_manager import RealUnifiedAgentManager
from fs_agt_clean.core.pipeline.controller import PipelineController
from fs_agt_clean.core.state_management.state_manager import StateManager
from fs_agt_clean.services.agent_orchestration import UnifiedAgentOrchestrationService
from fs_agt_clean.services.workflows.ai_product_creation import (
    AIProductCreationWorkflow,
    ProductCreationRequest,
    ProductCreationResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows/ai-product-creation", tags=["AI Product Creation"])


class ProductCreationResponse(BaseModel):
    """Response model for product creation API."""
    
    success: bool
    workflow_id: str
    message: str
    data: Optional[Dict] = None
    error: Optional[str] = None


class WorkflowStatusResponse(BaseModel):
    """Response model for workflow status API."""
    
    workflow_id: str
    status: str
    progress: float
    current_step: str
    agents_involved: list
    execution_time: Optional[float] = None
    error: Optional[str] = None


# Dependency injection for workflow components
async def get_workflow_service() -> AIProductCreationWorkflow:
    """Get AI Product Creation Workflow service with dependencies."""
    try:
        # Initialize core components
        agent_manager = RealUnifiedAgentManager()
        await agent_manager.initialize()
        
        state_manager = StateManager()
        
        pipeline_controller = PipelineController(agent_manager=agent_manager)
        await pipeline_controller.setup_agent_communication_protocol()
        
        orchestration_service = UnifiedAgentOrchestrationService()
        
        # Create workflow service
        workflow_service = AIProductCreationWorkflow(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )
        
        return workflow_service
        
    except Exception as e:
        logger.error(f"Error initializing workflow service: {e}")
        raise HTTPException(status_code=500, detail="Failed to initialize workflow service")


@router.post("/create-from-image", response_model=ProductCreationResponse)
async def create_product_from_image(
    image: UploadFile = File(...),
    marketplace: str = Form("ebay"),
    target_category: Optional[str] = Form(None),
    optimization_focus: str = Form("conversion"),
    conversation_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    workflow_service: AIProductCreationWorkflow = Depends(get_workflow_service),
) -> ProductCreationResponse:
    """
    Create a product listing from an uploaded image using AI-powered workflow.
    
    This endpoint triggers the sophisticated multi-agent workflow:
    Market UnifiedAgent → Executive UnifiedAgent → Content UnifiedAgent → Logistics UnifiedAgent
    
    Args:
        image: Product image file
        marketplace: Target marketplace (ebay, amazon)
        target_category: Optional target category
        optimization_focus: Optimization focus (conversion, seo, profit)
        conversation_id: Optional conversation ID for WebSocket updates
        user_id: Optional user ID for notifications
        
    Returns:
        ProductCreationResponse with workflow results
    """
    try:
        logger.info(f"Starting AI product creation from image: {image.filename}")
        
        # Validate image file
        if not image.filename:
            raise HTTPException(status_code=400, detail="No image file provided")
        
        # Read image data
        image_data = await image.read()
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(image_data) > max_size:
            raise HTTPException(status_code=400, detail="Image file too large (max 10MB)")
        
        # Create workflow request
        request = ProductCreationRequest(
            image_data=image_data,
            image_filename=image.filename,
            marketplace=marketplace.lower(),
            target_category=target_category,
            optimization_focus=optimization_focus,
            conversation_id=conversation_id,
            user_id=user_id,
        )
        
        # Execute workflow
        result = await workflow_service.create_product_from_image(request)
        
        if result.success:
            return ProductCreationResponse(
                success=True,
                workflow_id=result.workflow_id,
                message="Product creation workflow completed successfully",
                data={
                    "product_data": result.product_data,
                    "market_analysis": result.market_analysis,
                    "content_generated": result.content_generated,
                    "logistics_plan": result.logistics_plan,
                    "listing_created": result.listing_created,
                    "listing_id": result.listing_id,
                    "execution_time": result.execution_time_seconds,
                    "agents_involved": result.agents_involved,
                },
            )
        else:
            return ProductCreationResponse(
                success=False,
                workflow_id=result.workflow_id,
                message="Product creation workflow failed",
                error=result.error_message,
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in product creation API: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/status/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    workflow_id: str,
    workflow_service: AIProductCreationWorkflow = Depends(get_workflow_service),
) -> WorkflowStatusResponse:
    """
    Get the status of a running or completed workflow.
    
    Args:
        workflow_id: Workflow ID to check status for
        
    Returns:
        WorkflowStatusResponse with current workflow status
    """
    try:
        logger.info(f"Getting workflow status for: {workflow_id}")
        
        # Get workflow state from state manager
        workflow_state = workflow_service.state_manager.get_state(workflow_id)
        
        if not workflow_state:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Calculate progress based on completed steps
        total_steps = 4  # market_analysis, executive_decision, content_generation, logistics_creation
        completed_steps = len(workflow_state.get("steps_completed", []))
        progress = (completed_steps / total_steps) * 100
        
        return WorkflowStatusResponse(
            workflow_id=workflow_id,
            status=workflow_state.get("status", "unknown"),
            progress=progress,
            current_step=workflow_state.get("current_step", "unknown"),
            agents_involved=workflow_state.get("agents_involved", []),
            execution_time=workflow_state.get("execution_time"),
            error=workflow_state.get("error"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/metrics", response_model=Dict)
async def get_workflow_metrics(
    workflow_service: AIProductCreationWorkflow = Depends(get_workflow_service),
) -> Dict:
    """
    Get workflow performance metrics.
    
    Returns:
        Dictionary with workflow performance metrics
    """
    try:
        logger.info("Getting workflow metrics")
        
        metrics = workflow_service.get_workflow_metrics()
        
        return {
            "success": True,
            "metrics": metrics,
            "timestamp": "2024-01-01T00:00:00Z",  # Would use actual timestamp
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/test-workflow", response_model=ProductCreationResponse)
async def test_workflow_with_sample_image(
    marketplace: str = Form("ebay"),
    workflow_service: AIProductCreationWorkflow = Depends(get_workflow_service),
) -> ProductCreationResponse:
    """
    Test the AI product creation workflow with a sample image.
    
    This endpoint is useful for testing the workflow without uploading an actual image.
    
    Args:
        marketplace: Target marketplace (ebay, amazon)
        
    Returns:
        ProductCreationResponse with workflow test results
    """
    try:
        logger.info("Testing AI product creation workflow with sample data")
        
        # Create sample image data (1x1 pixel PNG)
        sample_image_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )
        
        # Create test workflow request
        request = ProductCreationRequest(
            image_data=sample_image_data,
            image_filename="test_product.png",
            marketplace=marketplace.lower(),
            optimization_focus="conversion",
            conversation_id="test_conversation",
            user_id="test_user",
        )
        
        # Execute workflow
        result = await workflow_service.create_product_from_image(request)
        
        if result.success:
            return ProductCreationResponse(
                success=True,
                workflow_id=result.workflow_id,
                message="Test workflow completed successfully",
                data={
                    "test_mode": True,
                    "product_data": result.product_data,
                    "execution_time": result.execution_time_seconds,
                    "agents_involved": result.agents_involved,
                },
            )
        else:
            return ProductCreationResponse(
                success=False,
                workflow_id=result.workflow_id,
                message="Test workflow failed",
                error=result.error_message,
            )
            
    except Exception as e:
        logger.error(f"Error in test workflow API: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
