"""
Market Synchronization Workflow for FlipSync.

This module implements the sophisticated multi-agent workflow for market synchronization
with cross-platform inventory sync → listing consistency → conflict resolution coordination.

Workflow Steps:
1. Cross-Platform Inventory Sync (Inventory UnifiedAgent)
2. Listing Consistency Management (Market UnifiedAgent)
3. Conflict Resolution & Data Validation (Executive UnifiedAgent)
4. Sync Monitoring & Performance Analytics (Logistics UnifiedAgent)
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.core.agents.real_agent_manager import RealUnifiedAgentManager
from fs_agt_clean.core.pipeline.controller import PipelineController
from fs_agt_clean.core.state_management.state_manager import StateManager
from fs_agt_clean.core.websocket.events import (
    EventType,
    WorkflowEvent,
    create_workflow_event,
)
from fs_agt_clean.services.agent_orchestration import (
    UnifiedAgentOrchestrationService,
    WorkflowStatus,
)

logger = logging.getLogger(__name__)


class SyncScope(Enum):
    """Scope of synchronization operation."""

    INVENTORY_ONLY = "inventory_only"
    LISTINGS_ONLY = "listings_only"
    PRICING_ONLY = "pricing_only"
    FULL_SYNC = "full_sync"


class ConflictResolutionStrategy(Enum):
    """Strategy for resolving data conflicts."""

    MARKETPLACE_PRIORITY = "marketplace_priority"
    LATEST_UPDATE = "latest_update"
    MANUAL_REVIEW = "manual_review"
    AUTOMATED_MERGE = "automated_merge"


@dataclass
class MarketSynchronizationRequest:
    """Request for market synchronization workflow."""

    sync_scope: SyncScope = SyncScope.FULL_SYNC
    source_marketplaces: List[str] = field(default_factory=lambda: ["ebay", "amazon"])
    target_marketplaces: List[str] = field(default_factory=lambda: ["ebay", "amazon"])
    product_ids: Optional[List[str]] = None  # None means sync all products
    conflict_resolution_strategy: ConflictResolutionStrategy = (
        ConflictResolutionStrategy.MARKETPLACE_PRIORITY
    )
    force_sync: bool = False  # Override conflict checks
    dry_run: bool = False  # Preview changes without applying
    user_context: Dict[str, Any] = field(default_factory=dict)
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class MarketSynchronizationResult:
    """Result of market synchronization workflow."""

    workflow_id: str
    success: bool
    sync_scope: SyncScope
    inventory_sync_results: Dict[str, Any]
    listing_consistency_results: Dict[str, Any]
    conflict_resolution_results: Dict[str, Any]
    sync_monitoring_results: Dict[str, Any]
    conflicts_detected: int
    conflicts_resolved: int
    items_synchronized: int
    marketplaces_updated: List[str]
    sync_summary: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time_seconds: float = 0.0
    agents_involved: List[str] = field(default_factory=list)


class MarketSynchronizationWorkflow:
    """
    Sophisticated Market Synchronization Workflow.

    Coordinates Inventory UnifiedAgent → Market UnifiedAgent → Executive UnifiedAgent → Logistics UnifiedAgent
    for cross-platform inventory sync, listing consistency, conflict resolution, and monitoring.
    """

    def __init__(
        self,
        agent_manager: RealUnifiedAgentManager,
        pipeline_controller: PipelineController,
        state_manager: StateManager,
        orchestration_service: UnifiedAgentOrchestrationService,
    ):
        self.agent_manager = agent_manager
        self.pipeline_controller = pipeline_controller
        self.state_manager = state_manager
        self.orchestration_service = orchestration_service
        self.workflow_metrics = {
            "syncs_started": 0,
            "syncs_completed": 0,
            "syncs_failed": 0,
            "total_conflicts_resolved": 0,
            "total_items_synchronized": 0,
            "average_execution_time": 0.0,
        }

    async def synchronize_marketplaces(
        self, request: MarketSynchronizationRequest
    ) -> MarketSynchronizationResult:
        """
        Execute the complete market synchronization workflow.

        Args:
            request: Market synchronization request with scope and parameters

        Returns:
            MarketSynchronizationResult with complete workflow results
        """
        workflow_id = str(uuid4())
        start_time = time.time()

        try:
            logger.info(f"Starting market synchronization workflow {workflow_id}")
            self.workflow_metrics["syncs_started"] += 1

            # Initialize workflow state
            workflow_state = {
                "workflow_id": workflow_id,
                "status": "started",
                "request": {
                    "sync_scope": request.sync_scope.value,
                    "source_marketplaces": request.source_marketplaces,
                    "target_marketplaces": request.target_marketplaces,
                    "conflict_resolution_strategy": request.conflict_resolution_strategy.value,
                    "force_sync": request.force_sync,
                    "dry_run": request.dry_run,
                },
                "steps_completed": [],
                "current_step": "inventory_sync",
                "agents_involved": [],
                "start_time": datetime.now(timezone.utc).isoformat(),
            }

            await self.state_manager.set_state(workflow_id, workflow_state)

            # Send workflow started event
            if request.conversation_id:
                workflow_event = create_workflow_event(
                    event_type=EventType.WORKFLOW_STARTED,
                    workflow_id=workflow_id,
                    workflow_type="market_synchronization",
                    participating_agents=[
                        "inventory",
                        "market",
                        "executive",
                        "logistics",
                    ],
                    status="started",
                    conversation_id=request.conversation_id,
                )
                await self._notify_workflow_progress(workflow_event, request.user_id)

            # Step 1: Inventory UnifiedAgent - Cross-Platform Inventory Sync
            inventory_sync_results = await self._execute_inventory_sync_step(
                workflow_id, request, workflow_state
            )

            # Step 2: Market UnifiedAgent - Listing Consistency Management
            listing_consistency_results = await self._execute_listing_consistency_step(
                workflow_id, request, inventory_sync_results, workflow_state
            )

            # Step 3: Executive UnifiedAgent - Conflict Resolution & Data Validation
            conflict_resolution_results = await self._execute_conflict_resolution_step(
                workflow_id,
                request,
                inventory_sync_results,
                listing_consistency_results,
                workflow_state,
            )

            # Step 4: Logistics UnifiedAgent - Sync Monitoring & Performance Analytics
            sync_monitoring_results = await self._execute_sync_monitoring_step(
                workflow_id,
                request,
                inventory_sync_results,
                listing_consistency_results,
                conflict_resolution_results,
                workflow_state,
            )

            # Calculate sync summary
            sync_summary = await self._calculate_sync_summary(
                request,
                inventory_sync_results,
                listing_consistency_results,
                conflict_resolution_results,
                sync_monitoring_results,
            )

            # Finalize workflow
            execution_time = time.time() - start_time
            workflow_state["status"] = "completed"
            workflow_state["execution_time"] = execution_time
            await self.state_manager.set_state(workflow_id, workflow_state)

            # Send completion event
            if request.conversation_id:
                completion_event = create_workflow_event(
                    event_type=EventType.WORKFLOW_COMPLETED,
                    workflow_id=workflow_id,
                    workflow_type="market_synchronization",
                    participating_agents=workflow_state["agents_involved"],
                    status="completed",
                    conversation_id=request.conversation_id,
                )
                await self._notify_workflow_progress(completion_event, request.user_id)

            self.workflow_metrics["syncs_completed"] += 1
            self._update_average_execution_time(execution_time)
            self._update_sync_metrics(sync_summary)

            return MarketSynchronizationResult(
                workflow_id=workflow_id,
                success=True,
                sync_scope=request.sync_scope,
                inventory_sync_results=inventory_sync_results,
                listing_consistency_results=listing_consistency_results,
                conflict_resolution_results=conflict_resolution_results,
                sync_monitoring_results=sync_monitoring_results,
                conflicts_detected=sync_summary.get("conflicts_detected", 0),
                conflicts_resolved=sync_summary.get("conflicts_resolved", 0),
                items_synchronized=sync_summary.get("items_synchronized", 0),
                marketplaces_updated=sync_summary.get("marketplaces_updated", []),
                sync_summary=sync_summary,
                execution_time_seconds=execution_time,
                agents_involved=workflow_state["agents_involved"],
            )

        except Exception as e:
            logger.error(f"Market synchronization workflow {workflow_id} failed: {e}")
            self.workflow_metrics["syncs_failed"] += 1

            # Update workflow state with error
            workflow_state["status"] = "failed"
            workflow_state["error"] = str(e)
            await self.state_manager.set_state(workflow_id, workflow_state)

            return MarketSynchronizationResult(
                workflow_id=workflow_id,
                success=False,
                sync_scope=request.sync_scope,
                inventory_sync_results={},
                listing_consistency_results={},
                conflict_resolution_results={},
                sync_monitoring_results={},
                conflicts_detected=0,
                conflicts_resolved=0,
                items_synchronized=0,
                marketplaces_updated=[],
                sync_summary={},
                error_message=str(e),
                execution_time_seconds=time.time() - start_time,
                agents_involved=workflow_state.get("agents_involved", []),
            )

    async def _execute_inventory_sync_step(
        self,
        workflow_id: str,
        request: MarketSynchronizationRequest,
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute inventory synchronization step using Inventory UnifiedAgent."""
        try:
            logger.info(f"Executing inventory sync step for workflow {workflow_id}")

            # Get inventory agent
            inventory_agent = await self._get_agent_by_type("inventory")
            if not inventory_agent:
                # Fallback to logistics agent with inventory capabilities
                inventory_agent = await self._get_agent_by_type("logistics")

            if not inventory_agent:
                raise ValueError("No inventory or logistics agent available for sync")

            workflow_state["agents_involved"].append(inventory_agent.agent_id)

            # Prepare inventory sync parameters
            sync_params = {
                "source_marketplaces": request.source_marketplaces,
                "target_marketplaces": request.target_marketplaces,
                "product_ids": request.product_ids,
                "sync_scope": request.sync_scope.value,
                "force_sync": request.force_sync,
                "dry_run": request.dry_run,
                "workflow_id": workflow_id,
            }

            # Execute inventory sync through agent coordination
            if hasattr(inventory_agent, "synchronize_inventory"):
                sync_result = await inventory_agent.synchronize_inventory(**sync_params)
            else:
                # Fallback to generic agent task execution
                sync_result = await self.agent_manager.execute_agent_task(
                    inventory_agent.agent_id,
                    {
                        "task": "inventory_synchronization",
                        "parameters": sync_params,
                        "workflow_context": {
                            "workflow_id": workflow_id,
                            "step": "inventory_sync",
                        },
                    },
                )

            # Process sync results
            inventory_sync_results = {
                "agent_id": inventory_agent.agent_id,
                "sync_status": sync_result.get("status", "completed"),
                "items_processed": sync_result.get("items_processed", 0),
                "items_synchronized": sync_result.get("items_synchronized", 0),
                "sync_conflicts": sync_result.get("conflicts", []),
                "marketplace_updates": sync_result.get("marketplace_updates", {}),
                "sync_errors": sync_result.get("errors", []),
                "execution_time": sync_result.get("execution_time", 0),
                "dry_run_preview": (
                    sync_result.get("dry_run_preview", {}) if request.dry_run else {}
                ),
            }

            # Update workflow state
            workflow_state["steps_completed"].append("inventory_sync")
            workflow_state["current_step"] = "listing_consistency"
            await self.state_manager.set_state(workflow_id, workflow_state)

            logger.info(f"Inventory sync step completed for workflow {workflow_id}")
            return inventory_sync_results

        except Exception as e:
            logger.error(f"Inventory sync step failed for workflow {workflow_id}: {e}")
            raise

    async def _execute_listing_consistency_step(
        self,
        workflow_id: str,
        request: MarketSynchronizationRequest,
        inventory_sync_results: Dict[str, Any],
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute listing consistency management step using Market UnifiedAgent."""
        try:
            logger.info(
                f"Executing listing consistency step for workflow {workflow_id}"
            )

            # Get market agent
            market_agent = await self._get_agent_by_type("market")
            if not market_agent:
                raise ValueError("No market agent available for listing consistency")

            workflow_state["agents_involved"].append(market_agent.agent_id)

            # Prepare listing consistency parameters
            consistency_params = {
                "marketplaces": request.target_marketplaces,
                "inventory_sync_data": inventory_sync_results,
                "product_ids": request.product_ids,
                "sync_scope": request.sync_scope.value,
                "dry_run": request.dry_run,
                "workflow_id": workflow_id,
            }

            # Execute listing consistency check through agent coordination
            if hasattr(market_agent, "ensure_listing_consistency"):
                consistency_result = await market_agent.ensure_listing_consistency(
                    **consistency_params
                )
            else:
                # Fallback to generic agent task execution
                consistency_result = await self.agent_manager.execute_agent_task(
                    market_agent.agent_id,
                    {
                        "task": "listing_consistency_management",
                        "parameters": consistency_params,
                        "workflow_context": {
                            "workflow_id": workflow_id,
                            "step": "listing_consistency",
                        },
                    },
                )

            # Process consistency results
            listing_consistency_results = {
                "agent_id": market_agent.agent_id,
                "consistency_status": consistency_result.get("status", "completed"),
                "listings_checked": consistency_result.get("listings_checked", 0),
                "inconsistencies_found": consistency_result.get(
                    "inconsistencies_found", 0
                ),
                "inconsistencies_resolved": consistency_result.get(
                    "inconsistencies_resolved", 0
                ),
                "marketplace_discrepancies": consistency_result.get(
                    "marketplace_discrepancies", {}
                ),
                "listing_updates_applied": consistency_result.get(
                    "listing_updates_applied", []
                ),
                "consistency_score": consistency_result.get("consistency_score", 100.0),
                "execution_time": consistency_result.get("execution_time", 0),
            }

            # Update workflow state
            workflow_state["steps_completed"].append("listing_consistency")
            workflow_state["current_step"] = "conflict_resolution"
            await self.state_manager.set_state(workflow_id, workflow_state)

            logger.info(
                f"Listing consistency step completed for workflow {workflow_id}"
            )
            return listing_consistency_results

        except Exception as e:
            logger.error(
                f"Listing consistency step failed for workflow {workflow_id}: {e}"
            )
            raise

    async def _execute_conflict_resolution_step(
        self,
        workflow_id: str,
        request: MarketSynchronizationRequest,
        inventory_sync_results: Dict[str, Any],
        listing_consistency_results: Dict[str, Any],
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute conflict resolution and data validation step using Executive UnifiedAgent."""
        try:
            logger.info(
                f"Executing conflict resolution step for workflow {workflow_id}"
            )

            # Get executive agent
            executive_agent = await self._get_agent_by_type("executive")
            if not executive_agent:
                raise ValueError("No executive agent available for conflict resolution")

            workflow_state["agents_involved"].append(executive_agent.agent_id)

            # Collect all conflicts from previous steps
            all_conflicts = []
            all_conflicts.extend(inventory_sync_results.get("sync_conflicts", []))
            all_conflicts.extend(
                listing_consistency_results.get(
                    "marketplace_discrepancies", {}
                ).values()
            )

            # Prepare conflict resolution parameters
            resolution_params = {
                "conflicts": all_conflicts,
                "resolution_strategy": request.conflict_resolution_strategy.value,
                "marketplaces": request.target_marketplaces,
                "inventory_data": inventory_sync_results,
                "listing_data": listing_consistency_results,
                "force_resolution": request.force_sync,
                "dry_run": request.dry_run,
                "workflow_id": workflow_id,
            }

            # Execute conflict resolution through agent coordination
            if hasattr(executive_agent, "resolve_marketplace_conflicts"):
                resolution_result = await executive_agent.resolve_marketplace_conflicts(
                    **resolution_params
                )
            else:
                # Fallback to generic agent task execution
                resolution_result = await self.agent_manager.execute_agent_task(
                    executive_agent.agent_id,
                    {
                        "task": "conflict_resolution_and_validation",
                        "parameters": resolution_params,
                        "workflow_context": {
                            "workflow_id": workflow_id,
                            "step": "conflict_resolution",
                        },
                    },
                )

            # Process resolution results
            conflict_resolution_results = {
                "agent_id": executive_agent.agent_id,
                "resolution_status": resolution_result.get("status", "completed"),
                "conflicts_detected": len(all_conflicts),
                "conflicts_resolved": resolution_result.get("conflicts_resolved", 0),
                "conflicts_pending": resolution_result.get("conflicts_pending", 0),
                "resolution_decisions": resolution_result.get(
                    "resolution_decisions", []
                ),
                "data_validation_results": resolution_result.get(
                    "data_validation_results", {}
                ),
                "marketplace_updates_required": resolution_result.get(
                    "marketplace_updates_required", []
                ),
                "execution_time": resolution_result.get("execution_time", 0),
            }

            # Update workflow state
            workflow_state["steps_completed"].append("conflict_resolution")
            workflow_state["current_step"] = "sync_monitoring"
            await self.state_manager.set_state(workflow_id, workflow_state)

            logger.info(
                f"Conflict resolution step completed for workflow {workflow_id}"
            )
            return conflict_resolution_results

        except Exception as e:
            logger.error(
                f"Conflict resolution step failed for workflow {workflow_id}: {e}"
            )
            raise

    async def _execute_sync_monitoring_step(
        self,
        workflow_id: str,
        request: MarketSynchronizationRequest,
        inventory_sync_results: Dict[str, Any],
        listing_consistency_results: Dict[str, Any],
        conflict_resolution_results: Dict[str, Any],
        workflow_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute sync monitoring and performance analytics step using Logistics UnifiedAgent."""
        try:
            logger.info(f"Executing sync monitoring step for workflow {workflow_id}")

            # Get logistics agent
            logistics_agent = await self._get_agent_by_type("logistics")
            if not logistics_agent:
                raise ValueError("No logistics agent available for sync monitoring")

            workflow_state["agents_involved"].append(logistics_agent.agent_id)

            # Prepare monitoring parameters
            monitoring_params = {
                "workflow_id": workflow_id,
                "sync_scope": request.sync_scope.value,
                "marketplaces": request.target_marketplaces,
                "inventory_results": inventory_sync_results,
                "consistency_results": listing_consistency_results,
                "resolution_results": conflict_resolution_results,
                "start_time": workflow_state.get("start_time"),
                "dry_run": request.dry_run,
            }

            # Execute sync monitoring through agent coordination
            if hasattr(logistics_agent, "monitor_sync_performance"):
                monitoring_result = await logistics_agent.monitor_sync_performance(
                    **monitoring_params
                )
            else:
                # Fallback to generic agent task execution
                monitoring_result = await self.agent_manager.execute_agent_task(
                    logistics_agent.agent_id,
                    {
                        "task": "sync_monitoring_and_analytics",
                        "parameters": monitoring_params,
                        "workflow_context": {
                            "workflow_id": workflow_id,
                            "step": "sync_monitoring",
                        },
                    },
                )

            # Process monitoring results
            sync_monitoring_results = {
                "agent_id": logistics_agent.agent_id,
                "monitoring_status": monitoring_result.get("status", "completed"),
                "sync_performance_metrics": monitoring_result.get(
                    "performance_metrics", {}
                ),
                "marketplace_health_status": monitoring_result.get(
                    "marketplace_health", {}
                ),
                "sync_quality_score": monitoring_result.get(
                    "sync_quality_score", 100.0
                ),
                "performance_recommendations": monitoring_result.get(
                    "performance_recommendations", []
                ),
                "sync_completion_rate": monitoring_result.get(
                    "sync_completion_rate", 100.0
                ),
                "error_analysis": monitoring_result.get("error_analysis", {}),
                "execution_time": monitoring_result.get("execution_time", 0),
            }

            # Update workflow state
            workflow_state["steps_completed"].append("sync_monitoring")
            workflow_state["current_step"] = "completed"
            await self.state_manager.set_state(workflow_id, workflow_state)

            logger.info(f"Sync monitoring step completed for workflow {workflow_id}")
            return sync_monitoring_results

        except Exception as e:
            logger.error(f"Sync monitoring step failed for workflow {workflow_id}: {e}")
            raise

    async def _calculate_sync_summary(
        self,
        request: MarketSynchronizationRequest,
        inventory_sync_results: Dict[str, Any],
        listing_consistency_results: Dict[str, Any],
        conflict_resolution_results: Dict[str, Any],
        sync_monitoring_results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculate comprehensive sync summary from all workflow steps."""
        try:
            # Calculate total items synchronized
            items_synchronized = inventory_sync_results.get("items_synchronized", 0)

            # Calculate total conflicts
            conflicts_detected = conflict_resolution_results.get(
                "conflicts_detected", 0
            )
            conflicts_resolved = conflict_resolution_results.get(
                "conflicts_resolved", 0
            )

            # Determine marketplaces updated
            marketplaces_updated = []
            marketplace_updates = inventory_sync_results.get("marketplace_updates", {})
            for marketplace, updates in marketplace_updates.items():
                if updates and len(updates) > 0:
                    marketplaces_updated.append(marketplace)

            # Calculate overall sync quality
            consistency_score = listing_consistency_results.get(
                "consistency_score", 100.0
            )
            sync_quality_score = sync_monitoring_results.get(
                "sync_quality_score", 100.0
            )
            overall_quality = (consistency_score + sync_quality_score) / 2

            # Calculate sync efficiency
            total_execution_time = (
                inventory_sync_results.get("execution_time", 0)
                + listing_consistency_results.get("execution_time", 0)
                + conflict_resolution_results.get("execution_time", 0)
                + sync_monitoring_results.get("execution_time", 0)
            )

            sync_efficiency = (
                items_synchronized / max(total_execution_time, 1)
                if items_synchronized > 0
                else 0
            )

            return {
                "sync_scope": request.sync_scope.value,
                "source_marketplaces": request.source_marketplaces,
                "target_marketplaces": request.target_marketplaces,
                "items_synchronized": items_synchronized,
                "conflicts_detected": conflicts_detected,
                "conflicts_resolved": conflicts_resolved,
                "marketplaces_updated": marketplaces_updated,
                "overall_sync_quality": overall_quality,
                "sync_efficiency_items_per_second": sync_efficiency,
                "total_execution_time": total_execution_time,
                "dry_run": request.dry_run,
                "sync_success_rate": (
                    (conflicts_resolved / max(conflicts_detected, 1)) * 100
                    if conflicts_detected > 0
                    else 100.0
                ),
            }

        except Exception as e:
            logger.error(f"Error calculating sync summary: {e}")
            return {
                "sync_scope": request.sync_scope.value,
                "items_synchronized": 0,
                "conflicts_detected": 0,
                "conflicts_resolved": 0,
                "marketplaces_updated": [],
                "error": str(e),
            }

    async def _get_agent_by_type(self, agent_type: str):
        """Get an agent instance by type from the agent manager."""
        try:
            # Use the orchestration service's agent registry
            if hasattr(self.orchestration_service, "agent_registry"):
                for (
                    agent_id,
                    agent,
                ) in self.orchestration_service.agent_registry.items():
                    if agent_type.lower() in agent_id.lower():
                        return agent

            # Fallback to agent manager
            available_agents = self.agent_manager.get_available_agents()
            for agent_id in available_agents:
                if agent_type.lower() in agent_id.lower():
                    return self.agent_manager.agents.get(agent_id)

            logger.warning(f"No agent found for type: {agent_type}")
            return None

        except Exception as e:
            logger.error(f"Error getting agent by type {agent_type}: {e}")
            return None

    async def _notify_workflow_progress(
        self, event: WorkflowEvent, user_id: Optional[str] = None
    ):
        """Send workflow progress notification via WebSocket."""
        try:
            from fs_agt_clean.core.websocket.manager import websocket_manager

            message = {
                "type": "workflow_progress",
                "data": {
                    "event_id": event.event_id,
                    "workflow_id": event.data.workflow_id,
                    "workflow_type": event.data.workflow_type,
                    "status": event.data.status,
                    "participating_agents": event.data.participating_agents,
                    "timestamp": event.timestamp.isoformat(),
                },
            }

            if user_id:
                await websocket_manager.send_to_user(user_id, message)
            else:
                await websocket_manager.broadcast(message)

        except Exception as e:
            logger.error(f"Error sending workflow progress notification: {e}")

    def _update_average_execution_time(self, execution_time: float):
        """Update the average execution time metric."""
        try:
            current_avg = self.workflow_metrics["average_execution_time"]
            completed_count = self.workflow_metrics["syncs_completed"]

            if completed_count <= 1:
                self.workflow_metrics["average_execution_time"] = execution_time
            else:
                # Calculate running average
                new_avg = (
                    (current_avg * (completed_count - 1)) + execution_time
                ) / completed_count
                self.workflow_metrics["average_execution_time"] = new_avg

        except Exception as e:
            logger.error(f"Error updating average execution time: {e}")

    def _update_sync_metrics(self, sync_summary: Dict[str, Any]):
        """Update workflow metrics with sync results."""
        try:
            self.workflow_metrics["total_conflicts_resolved"] += sync_summary.get(
                "conflicts_resolved", 0
            )
            self.workflow_metrics["total_items_synchronized"] += sync_summary.get(
                "items_synchronized", 0
            )

        except Exception as e:
            logger.error(f"Error updating sync metrics: {e}")

    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get current workflow metrics."""
        return self.workflow_metrics.copy()
