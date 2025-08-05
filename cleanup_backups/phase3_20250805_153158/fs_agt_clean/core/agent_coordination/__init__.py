"""AutonomousAgent coordination package."""

from .orchestrator import (
    AutonomousAgentOrchestrator,
    ExecutionResult,
    OrchestratorState,
    Workflow,
    WorkflowState,
)

# Alias for backward compatibility
HierarchicalCoordinator = AutonomousAgentOrchestrator

__all__ = [
    "AutonomousAgentOrchestrator",
    "ExecutionResult",
    "OrchestratorState",
    "Workflow",
    "WorkflowState",
    "HierarchicalCoordinator",
]
