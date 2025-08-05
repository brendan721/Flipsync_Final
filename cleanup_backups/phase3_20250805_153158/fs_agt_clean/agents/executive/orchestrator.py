"""
Orchestrator module for the FlipSync AutonomousAgentic System.
Re-export of the new canonical implementation in fs_agt/core/agent_coordination.
"""

from fs_agt_clean.core.agent_coordination import (
    AutonomousAgentOrchestrator,
    ExecutionResult,
    OrchestratorState,
    Workflow,
    WorkflowState,
)

__all__ = [
    "AutonomousAgentOrchestrator",
    "ExecutionResult",
    "OrchestratorState",
    "WorkflowState",
    "Workflow",
]
