"""Executive agents for FlipSync."""

from .resource_agent import ResourceUnifiedAgent

# StrategyUnifiedAgent removed - functionality integrated into ExecutiveAutonomousAgent

__all__ = [
    "ResourceUnifiedAgent",
    # "StrategyUnifiedAgent" - removed as part of 4+1 architecture cleanup
]
