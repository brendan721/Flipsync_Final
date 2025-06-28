"""UnifiedAgent coordination package."""

from .orchestrator import (
    UnifiedAgentOrchestrator,
    ExecutionResult,
    OrchestratorState,
    Workflow,
    WorkflowState,
)

# Alias for backward compatibility
HierarchicalCoordinator = UnifiedAgentOrchestrator

__all__ = [
    "UnifiedAgentOrchestrator",
    "ExecutionResult",
    "OrchestratorState",
    "Workflow",
    "WorkflowState",
    "HierarchicalCoordinator",
]
