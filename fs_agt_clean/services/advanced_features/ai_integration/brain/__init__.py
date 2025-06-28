"""Brain module for the FlipSync agent system."""

from fs_agt_clean.core.agent_coordination import (
    UnifiedAgentOrchestrator,
    Workflow,
    WorkflowState,
)
from fs_agt_clean.core.brain.decision import Decision, DecisionEngine
from fs_agt_clean.core.brain.strategy.models import Strategy, StrategyResult
from fs_agt_clean.core.brain.workflow_engine import WorkflowEngine

# Import at runtime to avoid circular import
# from fs_agt_clean.core.nlp.services.brain_service import BrainService

__all__ = [
    "UnifiedAgentOrchestrator",
    "Workflow",
    "WorkflowEngine",
    "WorkflowState",
    "Decision",
    "DecisionEngine",
    "Strategy",
    "StrategyResult",
]
