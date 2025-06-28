"""
UnifiedAgent orchestration for the FlipSync UnifiedAgentic System.

This module provides orchestration capabilities for coordinating multiple agents,
managing workflows, and facilitating decision making across the system.
It consolidates orchestration functionality from:
- fs_agt/services/orchestrator.py
- fs_agt/core/services/brain/orchestrator.py
- fs_agt/agents/executive/orchestrator.py
- fs_agt/core/brain/orchestrator.py

The UnifiedAgentOrchestrator class serves as the central coordination point for:
- UnifiedAgent registration and management
- Workflow creation and monitoring
- Decision making and strategy selection
- Event processing and distribution
- Metrics collection and reporting
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union
from uuid import UUID, uuid4

from fs_agt_clean.core.monitoring.alerts.manager import AlertManager
from fs_agt_clean.core.utils.config import get_settings
from fs_agt_clean.core.utils.metrics import MetricsMixin

if TYPE_CHECKING:
    from fs_agt_clean.core.agent_coordination.strategy_manager import (
        Strategy,
        StrategyManager,
    )
    from fs_agt_clean.core.decision_engine.decision_engine import DecisionEngine
    from fs_agt_clean.core.memory.memory_manager import MemoryManager


def get_context_key(context: Dict[str, Any]) -> str:
    """Generate a unique key for a context dictionary.

    Args:
        context: The context dictionary to generate a key for

    Returns:
        str: A unique hash key for the context
    """
    # Sort the dictionary to ensure consistent hashing
    context_str = json.dumps(context, sort_keys=True)
    return hashlib.md5(context_str.encode()).hexdigest()


class WorkflowState(Enum):
    """Possible states of a workflow"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class OrchestratorState:
    """Current state of the orchestrator."""

    active_strategies: Dict[str, UUID] = field(default_factory=dict)
    pending_decisions: List[str] = field(default_factory=list)
    last_update: datetime = field(default_factory=datetime.utcnow)
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Result of executing an orchestrated action."""

    decision_id: str
    strategy_id: UUID
    action: str
    context: Dict[str, Any]
    result: Dict[str, Any]
    success: bool
    metrics: Dict[str, float]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Workflow:
    """Workflow information."""

    workflow_id: str
    state: WorkflowState
    config: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    events: List[Dict[str, Any]] = field(default_factory=list)
    agents: Set[str] = field(default_factory=set)
    last_updated: datetime = field(default_factory=datetime.utcnow)


class UnifiedAgentOrchestrator(MetricsMixin):
    """
    Coordinates agent activities, workflows, and decisions.

    This is the central orchestration component that:
    - Manages agent registration and workflows
    - Coordinates decision making and strategy selection
    - Processes events and monitors system state
    - Collects metrics and provides reporting
    """

    def __init__(
        self,
        memory_manager: Optional["MemoryManager"] = None,
        decision_engine: Optional["DecisionEngine"] = None,
        strategy_manager: Optional["StrategyManager"] = None,
    ):
        """Initialize the orchestrator.

        Args:
            memory_manager: Optional memory manager instance
            decision_engine: Optional decision engine instance
            strategy_manager: Optional strategy manager instance
        """
        super().__init__()
        self.memory_manager = memory_manager
        self.decision_engine = decision_engine
        self.strategy_manager = strategy_manager
        self.state = OrchestratorState()
        self.alert_manager = AlertManager()
        self.settings = get_settings()
        self.agents: Dict[str, Any] = {}
        self.workflows: Dict[str, Workflow] = {}
        self.active_workflows: Set[str] = set()
        self.metrics: Dict[str, Any] = {
            "workflows_started": 0,
            "workflows_completed": 0,
            "workflows_failed": 0,
            "events_processed": 0,
        }
        self.logger = logging.getLogger(__name__)

    # UnifiedAgent Management Methods

    async def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register an agent with the orchestrator.

        Args:
            agent_id: Unique identifier for the agent
            agent: The agent instance to register

        Raises:
            ValueError: If an agent with the given ID is already registered
        """
        if agent_id in self.agents:
            raise ValueError(f"UnifiedAgent {agent_id} already registered")
        self.agents[agent_id] = {
            "instance": agent,
            "registered_at": datetime.utcnow(),
            "last_active": datetime.utcnow(),
            "workflows": set(),
        }
        self.logger.info(f"Registered agent: {agent_id}")

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the orchestrator.

        Args:
            agent_id: The agent ID to unregister

        Returns:
            bool: True if unregistered successfully, False if agent not found
        """
        if agent_id not in self.agents:
            return False

        # Remove agent from any workflows it's participating in
        for workflow_id in list(self.agents[agent_id]["workflows"]):
            if workflow_id in self.workflows:
                self.workflows[workflow_id].agents.remove(agent_id)

        del self.agents[agent_id]
        self.logger.info(f"Unregistered agent: {agent_id}")
        return True

    # Workflow Management Methods

    async def start_workflow(
        self, config: Dict[str, Any], workflow_id: Optional[str] = None
    ) -> str:
        """Start a new workflow with the given configuration.

        Args:
            config: Workflow configuration parameters
            workflow_id: Optional workflow ID (generated if not provided)

        Returns:
            str: The workflow ID

        Raises:
            ValueError: If a workflow with the given ID already exists
        """
        workflow_id = workflow_id or str(uuid4())

        if workflow_id in self.workflows:
            raise ValueError(f"Workflow {workflow_id} already exists")

        workflow = Workflow(
            workflow_id=workflow_id,
            state=WorkflowState.PENDING,
            config=config,
            started_at=datetime.utcnow(),
        )
        self.workflows[workflow_id] = workflow
        self.active_workflows.add(workflow_id)
        self.metrics["workflows_started"] += 1

        # Assign agents if available
        if self.agents:
            await self._assign_agents(workflow_id, config)
            workflow.state = WorkflowState.RUNNING

        self.logger.info(f"Started workflow: {workflow_id}")
        return workflow_id

    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get the workflow with the given ID.

        Args:
            workflow_id: The workflow ID to retrieve

        Returns:
            Optional[Workflow]: The workflow if found, None otherwise
        """
        return self.workflows.get(workflow_id)

    async def update_workflow_state(
        self, workflow_id: str, new_state: WorkflowState
    ) -> bool:
        """Update workflow state.

        Args:
            workflow_id: The workflow ID to update
            new_state: The new workflow state

        Returns:
            bool: True if updated successfully, False if workflow not found

        Raises:
            ValueError: If workflow not found
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        old_state = workflow.state
        workflow.state = new_state
        workflow.last_updated = datetime.utcnow()

        if new_state == WorkflowState.COMPLETED:
            workflow.completed_at = datetime.utcnow()
            self.metrics["workflows_completed"] += 1
            self.active_workflows.remove(workflow_id)
        elif new_state == WorkflowState.FAILED:
            workflow.completed_at = datetime.utcnow()
            self.metrics["workflows_failed"] += 1
            self.active_workflows.remove(workflow_id)
        elif new_state == WorkflowState.CANCELLED:
            workflow.completed_at = datetime.utcnow()
            self.active_workflows.remove(workflow_id)

        self.logger.info(
            f"Updated workflow {workflow_id} state: {old_state} -> {new_state}"
        )
        return True

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel the workflow with the given ID.

        Args:
            workflow_id: The workflow ID to cancel

        Returns:
            bool: True if cancelled successfully, False if workflow not found
        """
        if workflow_id not in self.workflows:
            return False

        return await self.update_workflow_state(workflow_id, WorkflowState.CANCELLED)

    async def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get current state of a workflow.

        Args:
            workflow_id: The workflow ID to query

        Returns:
            Optional[WorkflowState]: The workflow state if found, None otherwise
        """
        workflow = await self.get_workflow(workflow_id)
        return workflow.state if workflow else None

    async def get_active_workflows(self) -> List[str]:
        """Get list of active workflow IDs.

        Returns:
            List[str]: List of active workflow IDs
        """
        return list(self.active_workflows)

    async def cleanup_workflow(self, workflow_id: str) -> bool:
        """Clean up a completed workflow.

        Args:
            workflow_id: The workflow ID to clean up

        Returns:
            bool: True if cleaned up successfully, False if workflow not found

        Raises:
            ValueError: If workflow not found
            Exception: If workflow is still active
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        if workflow.state not in [
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
        ]:
            raise Exception(f"Cannot cleanup active workflow. State: {workflow.state}")

        # Remove workflow from agents
        for agent_id in workflow.agents:
            if agent_id in self.agents:
                self.agents[agent_id]["workflows"].remove(workflow_id)

        # Remove workflow
        del self.workflows[workflow_id]
        self.logger.info(f"Cleaned up workflow: {workflow_id}")
        return True

    # Event Processing Methods

    async def process_event(self, workflow_id: str, event: Dict[str, Any]) -> None:
        """Process an event in a workflow.

        Args:
            workflow_id: The workflow ID for the event
            event: The event data to process

        Raises:
            ValueError: If workflow not found
            Exception: If workflow is not in running state
        """
        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.workflows[workflow_id]
        if workflow.state != WorkflowState.RUNNING:
            raise Exception(f"Cannot process event. Workflow state: {workflow.state}")

        # Add event to workflow history
        workflow.events.append({"data": event, "timestamp": datetime.utcnow()})

        # Distribute event to all agents in the workflow
        for agent_id in workflow.agents:
            if agent_id in self.agents:
                agent = self.agents[agent_id]["instance"]
                await agent.process_event(event)
                self.agents[agent_id]["last_active"] = datetime.utcnow()

        workflow.last_updated = datetime.utcnow()
        self.metrics["events_processed"] += 1
        self.logger.debug(f"Processed event in workflow {workflow_id}")

    # Decision and Strategy Methods

    async def process_context(
        self,
        context: Dict[str, Any],
        available_actions: List[str],
        constraints: Optional[Dict[str, Any]] = None,
        strategy_tags: Optional[Set[str]] = None,
    ) -> Dict[str, Any]:
        """Process a context and make a decision.

        Args:
            context: The context to process
            available_actions: List of available actions
            constraints: Optional constraints on the decision
            strategy_tags: Optional strategy tags to filter by

        Returns:
            Dict[str, Any]: Decision result with decision_id

        Raises:
            Exception: If decision making fails
        """
        if not self.strategy_manager or not self.decision_engine:
            raise Exception(
                "Strategy manager and decision engine required for processing context"
            )

        start_time = datetime.utcnow()
        try:
            # Select strategy
            strategy = await self.strategy_manager.select_strategy(
                context=context, requirements=constraints, tags=strategy_tags
            )

            # Create default strategy if none found
            if not strategy:
                strategy = await self._create_default_strategy(
                    context, available_actions, strategy_tags or set()
                )

            # Associate strategy with context
            context_key = get_context_key(context)
            self.state.active_strategies[context_key] = strategy.strategy_id

            # Make decision
            decision = await self.decision_engine.make_decision(
                context=context,
                actions=available_actions,
                memory_context={"constraints": constraints},
            )

            # Track decision
            decision_id = f"decision_{datetime.utcnow().timestamp()}"
            self.state.pending_decisions.append(decision_id)

            # Update metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self.update_operation_metrics(
                operation="process_context",
                execution_time=execution_time,
                success=True,
                additional_metrics={
                    "strategy_id": str(strategy.strategy_id),
                    "decision_id": decision_id,
                    "confidence": (
                        decision["confidence"]
                        if isinstance(decision, dict)
                        else decision.confidence
                    ),
                },
            )

            return {**decision, "decision_id": decision_id}
        except Exception as e:
            self.logger.error(f"Error processing context: {e}")
            await self.update_operation_metrics(
                operation="process_context", execution_time=0.0, success=False
            )
            raise

    async def record_execution(self, result: ExecutionResult) -> None:
        """Record the result of executing a decision.

        Args:
            result: The execution result to record

        Raises:
            Exception: If recording fails
        """
        if not self.decision_engine:
            raise Exception("Decision engine required for recording execution")

        start_time = datetime.utcnow()
        try:
            # Remove from pending decisions
            if result.decision_id in self.state.pending_decisions:
                self.state.pending_decisions.remove(result.decision_id)

            # Learn from outcome
            await self.decision_engine.learn_from_outcome(
                decision_id=result.decision_id,
                outcome={
                    "action": result.action,
                    "context": result.context,
                    "result": result.result,
                    "success": result.success,
                    "performance": result.metrics.get("performance", 0.5),
                    "timestamp": result.timestamp,
                },
            )

            # Update metrics
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            await self.update_operation_metrics(
                operation="execution_result",
                execution_time=execution_time,
                success=result.success,
                additional_metrics=result.metrics,
            )

            self.logger.debug(
                f"Recorded execution result for decision {result.decision_id}"
            )
        except Exception as e:
            self.logger.error(f"Error recording execution result: {e}")
            await self.update_operation_metrics(
                operation="execution_result", execution_time=0.0, success=False
            )
            raise

    async def get_active_strategy(self, context: Dict[str, Any]) -> Optional[Any]:
        """Get the active strategy for a context.

        Args:
            context: The context to get strategy for

        Returns:
            Optional[Any]: The strategy if found, None otherwise
        """
        if not self.strategy_manager:
            return None

        context_key = get_context_key(context)
        strategy_id = self.state.active_strategies.get(context_key)

        if strategy_id:
            strategies = self.strategy_manager.strategies
            return strategies.get(strategy_id)

        return None

    # Metrics and Monitoring Methods

    async def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics.

        Returns:
            Dict[str, Any]: Dictionary of metrics
        """
        metrics = self.metrics.copy()
        metrics.update(
            {
                "active_workflows": len(self.active_workflows),
                "total_workflows": len(self.workflows),
                "registered_agents": len(self.agents),
                "pending_decisions": len(self.state.pending_decisions),
            }
        )

        return metrics

    # Private Helper Methods

    async def _create_default_strategy(
        self, context: Dict[str, Any], available_actions: List[str], tags: Set[str]
    ) -> Any:
        """Create a default strategy when none exists.

        Args:
            context: The context to create strategy for
            available_actions: List of available actions
            tags: Strategy tags

        Returns:
            Any: The created strategy

        Raises:
            Exception: If strategy manager is not available
        """
        if not self.strategy_manager:
            raise Exception("Strategy manager required for creating default strategy")

        return await self.strategy_manager.create_strategy(
            name=f"default_strategy_{datetime.utcnow().isoformat()}",
            description="Automatically created default strategy",
            rules={
                "min_confidence": 0.5,
                "max_attempts": 3,
                "allowed_actions": available_actions,
            },
            parameters={"learning_rate": 0.1, "exploration_rate": 0.2},
            tags=tags | {"type:default", "auto_created"},
        )

    def _combine_constraints(
        self, base_constraints: Optional[Dict[str, Any]], strategy_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine base constraints with strategy rules.

        Args:
            base_constraints: Base constraints
            strategy_rules: Strategy rules

        Returns:
            Dict[str, Any]: Combined constraints
        """
        constraints = base_constraints.copy() if base_constraints else {}

        for key, value in strategy_rules.items():
            if key not in constraints:
                constraints[key] = value

        return constraints

    async def _assign_agents(self, workflow_id: str, config: Dict[str, Any]) -> None:
        """Assign agents to a workflow based on configuration.

        Args:
            workflow_id: The workflow ID
            config: Workflow configuration

        Raises:
            Exception: If no available agents of required type
        """
        if workflow_id not in self.workflows:
            return

        workflow = self.workflows[workflow_id]

        for agent_type, enabled in config.items():
            if not enabled or not isinstance(enabled, bool):
                continue

            # Find available agents
            available_agents = [
                agent_id
                for agent_id, agent in self.agents.items()
                if agent_id.startswith(agent_type)
            ]

            if not available_agents:
                self.logger.warning(f"No available agents of type {agent_type}")
                continue

            # Assign agent to workflow
            agent_id = available_agents[0]
            workflow.agents.add(agent_id)
            self.agents[agent_id]["workflows"].add(workflow_id)
            self.logger.debug(f"Assigned agent {agent_id} to workflow {workflow_id}")
