"""
Orchestrator module for the FlipSync UnifiedAgentic System.
Re-export of the new canonical implementation in fs_agt/core/agent_coordination.
"""

from fs_agt_clean.core.agent_coordination import (
    UnifiedAgentOrchestrator,
    ExecutionResult,
    OrchestratorState,
    Workflow,
    WorkflowState,
)

__all__ = [
    "UnifiedAgentOrchestrator",
    "ExecutionResult",
    "OrchestratorState",
    "WorkflowState",
    "Workflow",
]
