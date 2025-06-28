# Coordinator Component

The Coordinator component is a core part of the FlipSync application that enables hierarchical coordination between agents. It manages agent registration, discovery, task delegation, result aggregation, and conflict resolution.

## Overview

The Coordinator consists of the following components:

- **Agent Registry**: Manages agent registration, discovery, and health monitoring
- **Task Delegator**: Manages task delegation, tracking, and lifecycle management
- **Result Aggregator**: Manages result collection, validation, and aggregation
- **Conflict Resolver**: Manages conflict detection, classification, and resolution

The Coordinator is designed to be:

- **Mobile-optimized**: Efficient operation on mobile devices
- **Vision-aligned**: Supporting all core vision elements
- **Robust**: Comprehensive error handling and recovery
- **Scalable**: Capable of handling complex agent ecosystems

## Agent Registry

The Agent Registry manages agent registration, discovery, and health monitoring. It provides methods for registering agents, updating their status and capabilities, and finding agents based on various criteria.

### Agent Types

The Coordinator supports the following agent types:

- **Executive**: High-level decision-making agents
- **Specialist**: Domain-specific specialist agents
- **Utility**: Utility agents providing common services
- **Mobile**: Mobile-specific agents
- **System**: System-level agents

### Agent Capabilities

Agents can advertise their capabilities, which are used for task delegation and agent discovery. Capabilities have:

- **Name**: Unique identifier for the capability
- **Description**: Human-readable description
- **Parameters**: Parameters that the capability accepts
- **Constraints**: Constraints on the capability (e.g., rate limits)
- **Tags**: Tags for categorizing the capability

## Task Delegator

The Task Delegator manages task delegation, tracking, and lifecycle management. It provides methods for creating tasks, assigning them to agents, and tracking their status and results.

### Task Lifecycle

Tasks have a lifecycle from creation to completion or failure:

1. **Created**: Task has been created
2. **Assigned**: Task has been assigned to an agent
3. **Accepted**: Agent has accepted the task
4. **Processing**: Agent is processing the task
5. **Completed**: Task has been completed successfully
6. **Failed**: Task has failed
7. **Cancelled**: Task has been cancelled
8. **Timeout**: Task has timed out

### Task Decomposition

Complex tasks can be decomposed into subtasks, which are tracked and managed by the Task Delegator. When all subtasks are completed, the parent task is marked as completed.

## Result Aggregator

The Result Aggregator manages result collection, validation, and aggregation. It provides methods for collecting results from multiple agents and aggregating them into a single result.

### Aggregation Strategies

The Result Aggregator supports the following aggregation strategies:

- **Collect**: Simply collect all results
- **Majority**: Use the majority result
- **Weighted**: Weight results by source
- **First**: Use the first result
- **Last**: Use the last result
- **Custom**: Use a custom aggregation function

## Conflict Resolver

The Conflict Resolver manages conflict detection, classification, and resolution. It provides methods for detecting conflicts, analyzing them, and applying resolution strategies.

### Conflict Types

The Conflict Resolver supports the following conflict types:

- **Resource**: Conflict over a resource
- **Task**: Conflict between tasks
- **Agent**: Conflict between agents
- **Priority**: Conflict over priority
- **Authority**: Conflict over authority
- **Capability**: Conflict over capability
- **Data**: Conflict over data
- **Other**: Other type of conflict

### Resolution Strategies

The Conflict Resolver supports the following resolution strategies:

- **Priority**: Resolve based on priority
- **Authority**: Resolve based on authority
- **Consensus**: Resolve based on consensus
- **First**: Resolve in favor of the first entity
- **Last**: Resolve in favor of the last entity
- **Merge**: Merge conflicting entities
- **Cancel**: Cancel conflicting entities
- **Delegate**: Delegate to a higher authority
- **Custom**: Use a custom resolution strategy

## Usage

### Creating a Coordinator

```python
from migration_plan.fs_clean.core.coordination import InMemoryCoordinator

# Create a coordinator
coordinator = InMemoryCoordinator(coordinator_id="my_coordinator")

# Start the coordinator
await coordinator.start()
```

### Registering an Agent

```python
from migration_plan.fs_clean.core.coordination import AgentInfo, AgentType, AgentCapability

# Create agent info
agent_info = AgentInfo(
    agent_id="my_agent",
    agent_type=AgentType.SPECIALIST,
    name="My Agent",
    description="A specialist agent",
    capabilities=[
        AgentCapability(
            name="my_capability",
            description="A capability",
            parameters={"param1": "string"},
            tags={"tag1", "tag2"}
        )
    ]
)

# Register the agent
await coordinator.register_agent(agent_info)
```

### Finding Agents

```python
# Find agents by type
executive_agents = await coordinator.find_agents_by_type(AgentType.EXECUTIVE)

# Find agents by capability
capability = AgentCapability(name="my_capability")
agents = await coordinator.find_agents_by_capability(capability)

# Find agents by status
active_agents = await coordinator.find_agents_by_status(AgentStatus.ACTIVE)

# Get all agents
all_agents = await coordinator.get_all_agents()
```

### Delegating Tasks

```python
# Delegate a task to a specific agent
task_id = await coordinator.delegate_task(
    task_id="",  # Empty string to generate a new ID
    task_type="my_task",
    parameters={"param1": "value1"},
    target_agent_id="my_agent",
    priority=TaskPriority.HIGH.value,
    deadline=datetime.now() + timedelta(minutes=5)
)

# Delegate a task based on capability
task_id = await coordinator.delegate_task(
    task_id="",
    task_type="my_task",
    parameters={"param1": "value1"},
    required_capability=AgentCapability(name="my_capability"),
    priority=TaskPriority.HIGH.value
)
```

### Getting Task Status and Results

```python
# Get task status
status = await coordinator.get_task_status(task_id)

# Get task result
result = await coordinator.get_task_result(task_id)

# Get tasks assigned to an agent
agent_tasks = await coordinator.get_agent_tasks(agent_id)
```

### Resolving Conflicts

```python
# Resolve a conflict
await coordinator.resolve_conflict(
    conflict_id="my_conflict",
    resolution_strategy=ResolutionStrategy.PRIORITY.value,
    resolution_parameters={"priority_field": "priority"}
)
```

## Vision Alignment

The Coordinator is designed to support FlipSync's vision elements:

### Interconnected Agent System

- **Hierarchical Coordination**: Enables executive-to-specialist delegation
- **Agent Discovery**: Allows agents to find each other based on capabilities
- **Task Delegation**: Enables complex task decomposition and execution
- **Result Aggregation**: Combines results from multiple agents
- **Conflict Resolution**: Ensures harmonious operation of the agent ecosystem

### Mobile-First Approach

- **Efficient Operation**: Minimizes resource usage on mobile devices
- **Adaptive Behavior**: Adapts to device capabilities and state
- **Battery Awareness**: Considers battery usage in task delegation
- **Network Awareness**: Adapts to network conditions
- **Offline Support**: Enables operation without continuous connectivity

### Conversational Interface

- **Task Context**: Maintains context across agent interactions
- **Intent Propagation**: Propagates user intent through task delegation
- **Response Coordination**: Coordinates responses from multiple agents
- **Conversation Flow**: Manages complex conversation flows

### Intelligent Decision Making

- **Decision Context**: Maintains decision context across agents
- **Confidence Levels**: Incorporates confidence in decisions
- **Feedback Loops**: Learns from decision outcomes
- **Adaptation**: Adapts decision strategies based on feedback

## Implementation Details

### Event-Based Communication

The Coordinator uses the Event System for communication between components and with agents. It publishes and subscribes to the following event types:

- **Agent Events**: Registration, status updates, capability updates
- **Task Events**: Creation, assignment, status updates, completion
- **Result Events**: Result collection, aggregation
- **Conflict Events**: Detection, resolution

### Mobile Optimization

The Coordinator includes several optimizations for mobile devices:

- **Efficient Task Delegation**: Considers device capabilities and state
- **Battery-Aware Operation**: Minimizes battery usage
- **Network-Aware Communication**: Adapts to network conditions
- **Resource-Efficient Implementation**: Minimizes memory and CPU usage

### Error Handling

The Coordinator includes comprehensive error handling:

- **CoordinationError**: Specialized error type for coordination failures
- **Retry Mechanisms**: Automatic retry for transient failures
- **Graceful Degradation**: Continues operation despite partial failures
- **Error Reporting**: Detailed error reporting for debugging

## Best Practices

### Agent Design

- **Advertise Capabilities**: Agents should advertise their capabilities for discovery
- **Handle Task Lifecycle**: Agents should handle the complete task lifecycle
- **Report Status**: Agents should report their status regularly
- **Handle Errors**: Agents should handle errors gracefully

### Task Delegation

- **Use Capabilities**: Delegate tasks based on capabilities when possible
- **Set Priorities**: Set appropriate priorities for tasks
- **Set Deadlines**: Set deadlines for time-sensitive tasks
- **Decompose Complex Tasks**: Break down complex tasks into subtasks

### Conflict Resolution

- **Define Resolution Strategies**: Define appropriate resolution strategies for different conflict types
- **Handle Unresolvable Conflicts**: Have a strategy for handling unresolvable conflicts
- **Monitor Conflicts**: Regularly check for and resolve conflicts

## Mobile Considerations

When using the Coordinator on mobile devices, consider the following:

- **Battery Usage**: Minimize battery usage by optimizing task delegation
- **Network Usage**: Minimize network usage by batching communications
- **Storage Usage**: Minimize storage usage by cleaning up completed tasks
- **CPU Usage**: Minimize CPU usage by optimizing task processing
- **Memory Usage**: Minimize memory usage by limiting concurrent tasks
