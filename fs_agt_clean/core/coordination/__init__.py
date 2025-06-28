"""
Core Coordination Layer for the FlipSync application.

This module provides the core coordination layer for FlipSync, which enables
the interconnected agent vision. It provides the foundation for agent
communication, coordination, knowledge sharing, and decision making.

The core coordination layer consists of:
- Event System: Enables asynchronous, loosely-coupled communication between agents
- Coordinator: Manages agent registration, discovery, and task delegation
- Knowledge Repository: Provides shared knowledge storage and retrieval
- Decision Pipeline: Enables intelligent, adaptive decision making

The core coordination layer is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling complex agent ecosystems
"""

# Coordinator components
from fs_agt_clean.core.coordination.coordinator import (  # UnifiedAgent components; Task components; Result components; Conflict components; Coordinator implementation
    UnifiedAgentCapability,
    UnifiedAgentInfo,
    UnifiedAgentRegistry,
    UnifiedAgentStatus,
    UnifiedAgentType,
    AggregationStrategy,
    Conflict,
    ConflictResolver,
    ConflictStatus,
    ConflictType,
    CoordinationError,
    Coordinator,
    InMemoryCoordinator,
    ResolutionStrategy,
    ResultAggregator,
    Task,
    TaskDelegator,
    TaskPriority,
    TaskStatus,
)

# Re-export core components
from fs_agt_clean.core.coordination.event_system import (  # Event System; Subscription filters
    CommandEvent,
    CompositeFilter,
    CustomFilter,
    ErrorEvent,
    Event,
    EventBus,
    EventNameFilter,
    EventNamePatternFilter,
    EventPriority,
    EventPriorityFilter,
    EventPublisher,
    EventSourceFilter,
    EventStatus,
    EventSubscriber,
    EventTargetFilter,
    EventType,
    EventTypeFilter,
    InMemoryEventBus,
    NotificationEvent,
    QueryEvent,
    ResponseEvent,
    SubscriptionFilter,
    create_publisher,
    create_subscriber,
    get_event_bus,
    set_event_bus,
)

# Knowledge Repository components will be added here
# Decision Pipeline components will be added here
