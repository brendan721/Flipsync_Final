"""
API routes for Conversational Interface Workflow.

This module provides REST API endpoints for the sophisticated multi-agent
conversational interface workflow with intent recognition, agent routing,
response generation, and personalized aggregation.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

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
from fs_agt_clean.services.workflows.conversational_interface import (
    ConversationMode,
    ConversationalInterfaceRequest,
    ConversationalInterfaceResult,
    ConversationalInterfaceWorkflow,
    ResponseStyle,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflows/conversational-interface", tags=["Conversational Interface"])


# Pydantic Models for API
class ConversationModeModel(BaseModel):
    """Conversation mode options."""
    single_query: str = Field(default="single_query", description="Single query response")
    multi_turn: str = Field(default="multi_turn", description="Multi-turn conversation")
    workflow_guided: str = Field(default="workflow_guided", description="Workflow-guided interaction")
    contextual_assistance: str = Field(default="contextual_assistance", description="Contextual assistance")


class ResponseStyleModel(BaseModel):
    """Response style options."""
    concise: str = Field(default="concise", description="Concise responses")
    detailed: str = Field(default="detailed", description="Detailed responses")
    technical: str = Field(default="technical", description="Technical responses")
    business_focused: str = Field(default="business_focused", description="Business-focused responses")


class ConversationalInterfaceRequestModel(BaseModel):
    """Request model for conversational interface."""
    
    user_message: str = Field(description="UnifiedUser message to process")
    conversation_mode: str = Field(
        default="single_query", 
        description="Mode of conversation interaction"
    )
    response_style: str = Field(
        default="business_focused", 
        description="Style of response generation"
    )
    conversation_history: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Previous conversation history"
    )
    user_context: Dict[str, Any] = Field(
        default_factory=dict, 
        description="UnifiedUser context and preferences"
    )
    personalization_preferences: Dict[str, Any] = Field(
        default_factory=dict, 
        description="UnifiedUser personalization preferences"
    )
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for tracking")
    user_id: Optional[str] = Field(default=None, description="UnifiedUser ID for notifications")


class ConversationalInterfaceResponseModel(BaseModel):
    """Response model for conversational interface."""
    
    workflow_id: str = Field(description="Unique workflow identifier")
    success: bool = Field(description="Whether the conversation processing was successful")
    conversation_mode: str = Field(description="Mode of conversation used")
    final_response: str = Field(description="Final aggregated response")
    confidence_score: float = Field(description="Overall confidence score (0.0-1.0)")
    agents_consulted: List[str] = Field(description="List of agents consulted")
    personalization_applied: Dict[str, Any] = Field(description="Personalization features applied")
    follow_up_suggestions: List[str] = Field(description="Suggested follow-up questions")
    execution_time_seconds: float = Field(description="Total execution time in seconds")
    agents_involved: List[str] = Field(description="List of agents that participated")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class WorkflowStatusModel(BaseModel):
    """Workflow status model."""
    
    workflow_id: str = Field(description="Workflow identifier")
    status: str = Field(description="Current workflow status")
    current_step: str = Field(description="Current workflow step")
    steps_completed: List[str] = Field(description="List of completed steps")
    agents_involved: List[str] = Field(description="List of participating agents")
    start_time: str = Field(description="Workflow start time")
    execution_time: Optional[float] = Field(default=None, description="Execution time if completed")


class WorkflowMetricsModel(BaseModel):
    """Workflow metrics model."""
    
    conversations_started: int = Field(description="Total conversations started")
    conversations_completed: int = Field(description="Total conversations completed")
    conversations_failed: int = Field(description="Total conversations failed")
    total_agents_consulted: int = Field(description="Total agents consulted")
    average_confidence_score: float = Field(description="Average confidence score")
    average_execution_time: float = Field(description="Average execution time in seconds")


@router.post("/process", response_model=ConversationalInterfaceResponseModel)
async def process_conversation(
    request: ConversationalInterfaceRequestModel,
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(get_orchestration_service),
):
    """
    Process conversational interface workflow.
    
    Coordinates Communication UnifiedAgent → Executive UnifiedAgent → Specialized UnifiedAgents → Content UnifiedAgent
    for intent recognition, agent routing, response generation, and personalized aggregation.
    """
    try:
        logger.info(f"Starting conversational interface workflow: {request.user_message[:50]}...")
        
        # Create workflow service
        workflow_service = ConversationalInterfaceWorkflow(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )
        
        # Convert API request to workflow request
        workflow_request = ConversationalInterfaceRequest(
            user_message=request.user_message,
            conversation_mode=ConversationMode(request.conversation_mode),
            response_style=ResponseStyle(request.response_style),
            conversation_history=request.conversation_history,
            user_context=request.user_context,
            personalization_preferences=request.personalization_preferences,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )
        
        # Execute workflow
        result = await workflow_service.process_conversation(workflow_request)
        
        # Convert result to API response
        return ConversationalInterfaceResponseModel(
            workflow_id=result.workflow_id,
            success=result.success,
            conversation_mode=result.conversation_mode.value,
            final_response=result.final_response,
            confidence_score=result.confidence_score,
            agents_consulted=result.agents_consulted,
            personalization_applied=result.personalization_applied,
            follow_up_suggestions=result.follow_up_suggestions,
            execution_time_seconds=result.execution_time_seconds,
            agents_involved=result.agents_involved,
            error_message=result.error_message,
        )
        
    except Exception as e:
        logger.error(f"Conversational interface workflow failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Conversational interface processing failed: {str(e)}"
        )


@router.get("/status/{workflow_id}", response_model=WorkflowStatusModel)
async def get_workflow_status(
    workflow_id: str,
    state_manager: StateManager = Depends(get_state_manager),
):
    """Get the status of a conversational interface workflow."""
    try:
        workflow_state = state_manager.get_state(workflow_id)
        
        if not workflow_state:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return WorkflowStatusModel(
            workflow_id=workflow_id,
            status=workflow_state.get("status", "unknown"),
            current_step=workflow_state.get("current_step", "unknown"),
            steps_completed=workflow_state.get("steps_completed", []),
            agents_involved=workflow_state.get("agents_involved", []),
            start_time=workflow_state.get("start_time", ""),
            execution_time=workflow_state.get("execution_time"),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving workflow status: {str(e)}"
        )


@router.get("/metrics", response_model=WorkflowMetricsModel)
async def get_workflow_metrics(
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(get_orchestration_service),
):
    """Get conversational interface workflow metrics."""
    try:
        # Create workflow service to access metrics
        workflow_service = ConversationalInterfaceWorkflow(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )
        
        metrics = workflow_service.get_workflow_metrics()
        
        return WorkflowMetricsModel(
            conversations_started=metrics.get("conversations_started", 0),
            conversations_completed=metrics.get("conversations_completed", 0),
            conversations_failed=metrics.get("conversations_failed", 0),
            total_agents_consulted=metrics.get("total_agents_consulted", 0),
            average_confidence_score=metrics.get("average_confidence_score", 0.0),
            average_execution_time=metrics.get("average_execution_time", 0.0),
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving workflow metrics: {str(e)}"
        )


@router.get("/conversation-modes", response_model=ConversationModeModel)
async def get_conversation_modes():
    """Get available conversation modes."""
    return ConversationModeModel()


@router.get("/response-styles", response_model=ResponseStyleModel)
async def get_response_styles():
    """Get available response styles."""
    return ResponseStyleModel()


@router.post("/chat", response_model=ConversationalInterfaceResponseModel)
async def chat_interface(
    request: ConversationalInterfaceRequestModel,
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(get_orchestration_service),
):
    """
    Simplified chat interface endpoint.
    
    Provides a streamlined interface for conversational interactions with automatic
    conversation mode and response style selection based on user context.
    """
    try:
        logger.info(f"Processing chat message: {request.user_message[:50]}...")
        
        # Auto-select conversation mode based on context
        if len(request.conversation_history) > 0:
            request.conversation_mode = "multi_turn"
        else:
            request.conversation_mode = "single_query"
        
        # Auto-select response style based on user context
        if request.user_context.get("technical_user", False):
            request.response_style = "technical"
        elif request.user_context.get("business_user", True):
            request.response_style = "business_focused"
        else:
            request.response_style = "detailed"
        
        # Process through main workflow
        return await process_conversation(
            request, agent_manager, pipeline_controller, state_manager, orchestration_service
        )
        
    except Exception as e:
        logger.error(f"Chat interface failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )
