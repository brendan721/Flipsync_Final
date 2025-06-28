"""
API routes for Market Synchronization Workflow.

This module provides REST API endpoints for the sophisticated multi-agent
market synchronization workflow with cross-platform inventory sync,
listing consistency management, conflict resolution, and sync monitoring.
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
from fs_agt_clean.services.workflows.market_synchronization import (
    ConflictResolutionStrategy,
    MarketSynchronizationRequest,
    MarketSynchronizationResult,
    MarketSynchronizationWorkflow,
    SyncScope,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/workflows/market-synchronization", tags=["Market Synchronization"])


# Pydantic Models for API
class SyncScopeModel(BaseModel):
    """Sync scope options."""
    inventory_only: str = Field(default="inventory_only", description="Sync inventory data only")
    listings_only: str = Field(default="listings_only", description="Sync listing data only")
    pricing_only: str = Field(default="pricing_only", description="Sync pricing data only")
    full_sync: str = Field(default="full_sync", description="Complete synchronization")


class ConflictResolutionStrategyModel(BaseModel):
    """Conflict resolution strategy options."""
    marketplace_priority: str = Field(default="marketplace_priority", description="Use marketplace priority")
    latest_update: str = Field(default="latest_update", description="Use latest update timestamp")
    manual_review: str = Field(default="manual_review", description="Require manual review")
    automated_merge: str = Field(default="automated_merge", description="Automated conflict merge")


class MarketSynchronizationRequestModel(BaseModel):
    """Request model for market synchronization."""
    
    sync_scope: str = Field(default="full_sync", description="Scope of synchronization")
    source_marketplaces: List[str] = Field(
        default=["ebay", "amazon"], 
        description="Source marketplaces for synchronization"
    )
    target_marketplaces: List[str] = Field(
        default=["ebay", "amazon"], 
        description="Target marketplaces for synchronization"
    )
    product_ids: Optional[List[str]] = Field(
        default=None, 
        description="Specific product IDs to sync (None for all products)"
    )
    conflict_resolution_strategy: str = Field(
        default="marketplace_priority", 
        description="Strategy for resolving data conflicts"
    )
    force_sync: bool = Field(default=False, description="Override conflict checks")
    dry_run: bool = Field(default=False, description="Preview changes without applying")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="Additional user context")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID for tracking")
    user_id: Optional[str] = Field(default=None, description="UnifiedUser ID for notifications")


class MarketSynchronizationResponseModel(BaseModel):
    """Response model for market synchronization."""
    
    workflow_id: str = Field(description="Unique workflow identifier")
    success: bool = Field(description="Whether the synchronization was successful")
    sync_scope: str = Field(description="Scope of synchronization performed")
    conflicts_detected: int = Field(description="Number of conflicts detected")
    conflicts_resolved: int = Field(description="Number of conflicts resolved")
    items_synchronized: int = Field(description="Number of items synchronized")
    marketplaces_updated: List[str] = Field(description="List of marketplaces updated")
    execution_time_seconds: float = Field(description="Total execution time in seconds")
    agents_involved: List[str] = Field(description="List of agents that participated")
    sync_summary: Dict[str, Any] = Field(description="Comprehensive sync summary")
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
    
    syncs_started: int = Field(description="Total synchronizations started")
    syncs_completed: int = Field(description="Total synchronizations completed")
    syncs_failed: int = Field(description="Total synchronizations failed")
    total_conflicts_resolved: int = Field(description="Total conflicts resolved")
    total_items_synchronized: int = Field(description="Total items synchronized")
    average_execution_time: float = Field(description="Average execution time in seconds")


@router.post("/synchronize", response_model=MarketSynchronizationResponseModel)
async def synchronize_marketplaces(
    request: MarketSynchronizationRequestModel,
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(get_orchestration_service),
):
    """
    Execute market synchronization workflow.
    
    Coordinates Inventory UnifiedAgent → Market UnifiedAgent → Executive UnifiedAgent → Logistics UnifiedAgent
    for cross-platform inventory sync, listing consistency, conflict resolution, and monitoring.
    """
    try:
        logger.info(f"Starting market synchronization workflow: {request.sync_scope}")
        
        # Create workflow service
        workflow_service = MarketSynchronizationWorkflow(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )
        
        # Convert API request to workflow request
        workflow_request = MarketSynchronizationRequest(
            sync_scope=SyncScope(request.sync_scope),
            source_marketplaces=request.source_marketplaces,
            target_marketplaces=request.target_marketplaces,
            product_ids=request.product_ids,
            conflict_resolution_strategy=ConflictResolutionStrategy(request.conflict_resolution_strategy),
            force_sync=request.force_sync,
            dry_run=request.dry_run,
            user_context=request.user_context,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )
        
        # Execute workflow
        result = await workflow_service.synchronize_marketplaces(workflow_request)
        
        # Convert result to API response
        return MarketSynchronizationResponseModel(
            workflow_id=result.workflow_id,
            success=result.success,
            sync_scope=result.sync_scope.value,
            conflicts_detected=result.conflicts_detected,
            conflicts_resolved=result.conflicts_resolved,
            items_synchronized=result.items_synchronized,
            marketplaces_updated=result.marketplaces_updated,
            execution_time_seconds=result.execution_time_seconds,
            agents_involved=result.agents_involved,
            sync_summary=result.sync_summary,
            error_message=result.error_message,
        )
        
    except Exception as e:
        logger.error(f"Market synchronization workflow failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market synchronization failed: {str(e)}"
        )


@router.get("/status/{workflow_id}", response_model=WorkflowStatusModel)
async def get_workflow_status(
    workflow_id: str,
    state_manager: StateManager = Depends(get_state_manager),
):
    """Get the status of a market synchronization workflow."""
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
    """Get market synchronization workflow metrics."""
    try:
        # Create workflow service to access metrics
        workflow_service = MarketSynchronizationWorkflow(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )
        
        metrics = workflow_service.get_workflow_metrics()
        
        return WorkflowMetricsModel(
            syncs_started=metrics.get("syncs_started", 0),
            syncs_completed=metrics.get("syncs_completed", 0),
            syncs_failed=metrics.get("syncs_failed", 0),
            total_conflicts_resolved=metrics.get("total_conflicts_resolved", 0),
            total_items_synchronized=metrics.get("total_items_synchronized", 0),
            average_execution_time=metrics.get("average_execution_time", 0.0),
        )
        
    except Exception as e:
        logger.error(f"Error getting workflow metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving workflow metrics: {str(e)}"
        )


@router.get("/sync-scopes", response_model=SyncScopeModel)
async def get_sync_scopes():
    """Get available synchronization scopes."""
    return SyncScopeModel()


@router.get("/conflict-resolution-strategies", response_model=ConflictResolutionStrategyModel)
async def get_conflict_resolution_strategies():
    """Get available conflict resolution strategies."""
    return ConflictResolutionStrategyModel()


@router.post("/dry-run", response_model=MarketSynchronizationResponseModel)
async def dry_run_synchronization(
    request: MarketSynchronizationRequestModel,
    agent_manager: RealUnifiedAgentManager = Depends(get_agent_manager),
    pipeline_controller: PipelineController = Depends(get_pipeline_controller),
    state_manager: StateManager = Depends(get_state_manager),
    orchestration_service: UnifiedAgentOrchestrationService = Depends(get_orchestration_service),
):
    """
    Execute a dry run of market synchronization workflow.
    
    Previews changes without applying them to marketplaces.
    """
    try:
        logger.info(f"Starting market synchronization dry run: {request.sync_scope}")
        
        # Force dry run mode
        request.dry_run = True
        
        # Create workflow service
        workflow_service = MarketSynchronizationWorkflow(
            agent_manager=agent_manager,
            pipeline_controller=pipeline_controller,
            state_manager=state_manager,
            orchestration_service=orchestration_service,
        )
        
        # Convert API request to workflow request
        workflow_request = MarketSynchronizationRequest(
            sync_scope=SyncScope(request.sync_scope),
            source_marketplaces=request.source_marketplaces,
            target_marketplaces=request.target_marketplaces,
            product_ids=request.product_ids,
            conflict_resolution_strategy=ConflictResolutionStrategy(request.conflict_resolution_strategy),
            force_sync=request.force_sync,
            dry_run=True,  # Force dry run
            user_context=request.user_context,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )
        
        # Execute dry run workflow
        result = await workflow_service.synchronize_marketplaces(workflow_request)
        
        # Convert result to API response
        return MarketSynchronizationResponseModel(
            workflow_id=result.workflow_id,
            success=result.success,
            sync_scope=result.sync_scope.value,
            conflicts_detected=result.conflicts_detected,
            conflicts_resolved=result.conflicts_resolved,
            items_synchronized=result.items_synchronized,
            marketplaces_updated=result.marketplaces_updated,
            execution_time_seconds=result.execution_time_seconds,
            agents_involved=result.agents_involved,
            sync_summary=result.sync_summary,
            error_message=result.error_message,
        )
        
    except Exception as e:
        logger.error(f"Market synchronization dry run failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Market synchronization dry run failed: {str(e)}"
        )
