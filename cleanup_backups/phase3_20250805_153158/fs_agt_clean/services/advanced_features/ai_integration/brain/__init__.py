"""Brain module for the FlipSync agent system."""

# Import actual brain components from current directory structure
from .decision_engine import Decision, DecisionEngine
from .memory.memory_manager import Memory, MemoryManager
from .workflow_engine import WorkflowEngine, WorkflowPattern

# Import strategy models if they exist
try:
    from .strategy.models import Strategy, StrategyResult

    STRATEGY_AVAILABLE = True
except ImportError:
    STRATEGY_AVAILABLE = False

    # Create placeholder classes
    class Strategy:
        pass

    class StrategyResult:
        pass


# Import coordination components if they exist
try:
    from fs_agt_clean.core.agent_coordination import (
        AutonomousAgentOrchestrator,
        Workflow,
        WorkflowState,
    )

    COORDINATION_AVAILABLE = True
except ImportError:
    COORDINATION_AVAILABLE = False

    # Create placeholder classes
    class AutonomousAgentOrchestrator:
        pass

    class Workflow:
        pass

    class WorkflowState:
        pass


__all__ = [
    "Decision",
    "DecisionEngine",
    "Memory",
    "MemoryManager",
    "WorkflowEngine",
    "WorkflowPattern",
    "Strategy",
    "StrategyResult",
    "AutonomousAgentOrchestrator",
    "Workflow",
    "WorkflowState",
]
