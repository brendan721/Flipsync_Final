"""Executive agents for FlipSync."""

from .resource_agent import ResourceAutonomousAgent

# StrategyAutonomousAgent removed - functionality integrated into ExecutiveAutonomousAgent

__all__ = [
    "ResourceAutonomousAgent",
    # "StrategyAutonomousAgent" - removed as part of 4+1 architecture cleanup
]
