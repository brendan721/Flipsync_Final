"""
Coordinator component for the FlipSync application.

This module provides the coordinator component for FlipSync, which manages
agent registration, discovery, and task delegation. It enables hierarchical
coordination between agents, with executive agents delegating tasks to
specialist agents.

The coordinator is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling complex agent ecosystems
"""

from fs_agt_clean.core.coordination.coordinator.agent_registry import UnifiedAgentRegistry
from fs_agt_clean.core.coordination.coordinator.conflict_resolver import (
    Conflict,
    ConflictResolver,
    ConflictStatus,
    ConflictType,
    ResolutionStrategy,
)

# Re-export core components
from fs_agt_clean.core.coordination.coordinator.coordinator import (
    UnifiedAgentCapability,
    UnifiedAgentInfo,
    UnifiedAgentStatus,
    UnifiedAgentType,
    CoordinationError,
    Coordinator,
)
from fs_agt_clean.core.coordination.coordinator.in_memory_coordinator import (
    InMemoryCoordinator,
)
from fs_agt_clean.core.coordination.coordinator.result_aggregator import (
    AggregationStrategy,
    ResultAggregator,
)
from fs_agt_clean.core.coordination.coordinator.task_delegator import (
    Task,
    TaskDelegator,
    TaskPriority,
    TaskStatus,
)
