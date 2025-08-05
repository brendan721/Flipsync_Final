"""
Database-backed Workflow Manager for FlipSync Agentic System

This module provides database persistence for workflow state, enabling workflows
to survive system restarts and providing cross-session workflow coordination.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update

from fs_agt_clean.core.coordination.database_models import (
    WorkflowState,
)
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class DatabaseWorkflowManager:
    """Database-backed Workflow Manager with persistent workflow state.
    
    This class provides:
    - Persistent workflow state storage
    - Workflow step tracking and recovery
    - Agent handoff state persistence
    - Workflow result and metrics storage
    - Workflow continuation after system restart
    """
    
    def __init__(self, database: Database):
        """Initialize the database-backed workflow manager.
        
        Args:
            database: Database instance for persistence
        """
        self.database = database
        self.active_workflows: Dict[str, WorkflowState] = {}
        
        logger.info("Initialized DatabaseWorkflowManager")
    
    async def initialize(self) -> bool:
        """Initialize the database-backed workflow manager.
        
        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Load active workflows from database
            await self._load_active_workflows()
            
            logger.info("✅ DatabaseWorkflowManager initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize DatabaseWorkflowManager: {e}")
            return False
    
    async def start_workflow(
        self,
        workflow_id: str,
        workflow_type: str,
        workflow_name: str,
        workflow_config: Dict[str, Any],
        input_data: Dict[str, Any],
        participating_agents: List[str]
    ) -> bool:
        """Start a new workflow with database persistence.
        
        Args:
            workflow_id: Unique identifier for the workflow
            workflow_type: Type of workflow (sales_optimization, market_sync, etc.)
            workflow_name: Human-readable name for the workflow
            workflow_config: Configuration for the workflow
            input_data: Input data for the workflow
            participating_agents: List of agents participating in the workflow
            
        Returns:
            True if workflow was started successfully, False otherwise
        """
        try:
            async with self.database.get_session() as session:
                # Create workflow state record
                workflow_record = WorkflowState(
                    workflow_id=workflow_id,
                    workflow_type=workflow_type,
                    workflow_name=workflow_name,
                    workflow_config=workflow_config,
                    workflow_context={
                        "started_by": "system",
                        "start_time": datetime.now(timezone.utc).isoformat()
                    },
                    input_data=input_data,
                    participating_agents=participating_agents,
                    status="pending",
                    current_step="initialization",
                    step_index=0,
                    total_steps=len(participating_agents) if participating_agents else 1
                )
                
                session.add(workflow_record)
                await session.commit()
                
                # Cache the workflow state
                self.active_workflows[workflow_id] = workflow_record
                
                logger.info(f"Started workflow {workflow_id} ({workflow_type})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_id}: {e}")
            return False
    
    async def update_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        step_index: int,
        step_result: Dict[str, Any],
        current_agent: Optional[str] = None,
        progress_percentage: Optional[float] = None
    ) -> bool:
        """Update workflow step with database persistence.
        
        Args:
            workflow_id: Workflow identifier
            step_name: Name of the current step
            step_index: Index of the current step
            step_result: Result data from the step
            current_agent: Currently executing agent
            progress_percentage: Progress percentage (0.0 to 100.0)
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            async with self.database.get_session() as session:
                # Get current workflow state
                result = await session.execute(
                    select(WorkflowState).where(WorkflowState.workflow_id == workflow_id)
                )
                
                workflow_record = result.scalar_one_or_none()
                if not workflow_record:
                    logger.error(f"Workflow {workflow_id} not found")
                    return False
                
                # Update step history
                step_history = workflow_record.step_history or []
                step_history.append({
                    "step_name": step_name,
                    "step_index": step_index,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "agent": current_agent,
                    "result": step_result
                })
                
                # Update step results
                step_results = workflow_record.step_results or {}
                step_results[step_name] = step_result
                
                # Calculate progress if not provided
                if progress_percentage is None and workflow_record.total_steps > 0:
                    progress_percentage = (step_index + 1) / workflow_record.total_steps * 100
                
                # Update workflow record
                update_values = {
                    "current_step": step_name,
                    "step_index": step_index,
                    "step_history": step_history,
                    "step_results": step_results,
                    "last_updated": datetime.now(timezone.utc)
                }
                
                if current_agent:
                    update_values["current_agent"] = current_agent
                
                if progress_percentage is not None:
                    update_values["progress_percentage"] = min(100.0, max(0.0, progress_percentage))
                
                await session.execute(
                    update(WorkflowState)
                    .where(WorkflowState.workflow_id == workflow_id)
                    .values(**update_values)
                )
                
                await session.commit()
                
                # Update cached workflow state
                if workflow_id in self.active_workflows:
                    for key, value in update_values.items():
                        setattr(self.active_workflows[workflow_id], key, value)
                
                logger.debug(f"Updated workflow {workflow_id} step: {step_name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update workflow step for {workflow_id}: {e}")
            return False
    
    async def complete_workflow(
        self,
        workflow_id: str,
        final_result: Dict[str, Any],
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """Complete a workflow with database persistence.
        
        Args:
            workflow_id: Workflow identifier
            final_result: Final result data from the workflow
            success: Whether the workflow completed successfully
            error_message: Error message if workflow failed
            
        Returns:
            True if completion was successful, False otherwise
        """
        try:
            async with self.database.get_session() as session:
                # Calculate execution time
                result = await session.execute(
                    select(WorkflowState).where(WorkflowState.workflow_id == workflow_id)
                )
                
                workflow_record = result.scalar_one_or_none()
                if not workflow_record:
                    logger.error(f"Workflow {workflow_id} not found")
                    return False
                
                execution_time_ms = int(
                    (datetime.now(timezone.utc) - workflow_record.started_at).total_seconds() * 1000
                )
                
                # Update workflow record
                update_values = {
                    "status": "completed" if success else "failed",
                    "progress_percentage": 100.0 if success else workflow_record.progress_percentage,
                    "final_result": final_result,
                    "completed_at": datetime.now(timezone.utc),
                    "execution_time_ms": execution_time_ms,
                    "last_updated": datetime.now(timezone.utc)
                }
                
                if error_message:
                    update_values["error_message"] = error_message
                
                await session.execute(
                    update(WorkflowState)
                    .where(WorkflowState.workflow_id == workflow_id)
                    .values(**update_values)
                )
                
                await session.commit()
                
                # Remove from active workflows cache
                if workflow_id in self.active_workflows:
                    del self.active_workflows[workflow_id]
                
                logger.info(f"Completed workflow {workflow_id}: {success}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to complete workflow {workflow_id}: {e}")
            return False
    
    async def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow state from database.
        
        Args:
            workflow_id: Workflow identifier
            
        Returns:
            Workflow state data or None if not found
        """
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    select(WorkflowState).where(WorkflowState.workflow_id == workflow_id)
                )
                
                workflow_record = result.scalar_one_or_none()
                if not workflow_record:
                    return None
                
                return {
                    "workflow_id": workflow_record.workflow_id,
                    "workflow_type": workflow_record.workflow_type,
                    "workflow_name": workflow_record.workflow_name,
                    "status": workflow_record.status,
                    "current_step": workflow_record.current_step,
                    "step_index": workflow_record.step_index,
                    "total_steps": workflow_record.total_steps,
                    "progress_percentage": workflow_record.progress_percentage,
                    "participating_agents": workflow_record.participating_agents,
                    "current_agent": workflow_record.current_agent,
                    "step_history": workflow_record.step_history,
                    "step_results": workflow_record.step_results,
                    "started_at": workflow_record.started_at.isoformat(),
                    "completed_at": workflow_record.completed_at.isoformat() if workflow_record.completed_at else None,
                    "execution_time_ms": workflow_record.execution_time_ms,
                    "final_result": workflow_record.final_result,
                    "error_message": workflow_record.error_message
                }
                
        except Exception as e:
            logger.error(f"Failed to get workflow state for {workflow_id}: {e}")
            return None
    
    async def _load_active_workflows(self):
        """Load active workflows from database."""
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    select(WorkflowState).where(
                        WorkflowState.status.in_(["pending", "running", "paused"])
                    )
                )
                
                active_workflows = result.scalars().all()
                
                for workflow in active_workflows:
                    self.active_workflows[workflow.workflow_id] = workflow
                    logger.debug(f"Loaded active workflow: {workflow.workflow_id}")
                
                logger.info(f"Loaded {len(active_workflows)} active workflows")
                
        except Exception as e:
            logger.error(f"Failed to load active workflows: {e}")
