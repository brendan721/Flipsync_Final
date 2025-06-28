# Coordinator Sequence Diagrams

This document contains sequence diagrams for common coordination flows in the FlipSync application.

## Agent Registration Flow

```mermaid
sequenceDiagram
    participant Agent
    participant Coordinator
    participant AgentRegistry
    participant EventBus

    Agent->>Coordinator: register_agent(agent_info)
    Coordinator->>AgentRegistry: register_agent(agent_info)
    AgentRegistry->>AgentRegistry: Update agent status and last seen
    AgentRegistry->>EventBus: Publish agent_registered event
    EventBus-->>Agent: Notify of registration
    AgentRegistry-->>Coordinator: Registration result
    Coordinator-->>Agent: Registration result
```

## Task Delegation Flow

```mermaid
sequenceDiagram
    participant ExecutiveAgent
    participant Coordinator
    participant AgentRegistry
    participant TaskDelegator
    participant ResultAggregator
    participant SpecialistAgent
    participant EventBus

    ExecutiveAgent->>Coordinator: delegate_task(task_type, parameters, required_capability)
    Coordinator->>AgentRegistry: find_agents_by_capability(required_capability)
    AgentRegistry-->>Coordinator: matching_agents
    Coordinator->>Coordinator: select_agent_for_task(matching_agents)
    Coordinator->>TaskDelegator: create_task(task_type, parameters, agent_id)
    TaskDelegator->>EventBus: Publish task_created event
    TaskDelegator-->>Coordinator: task_id
    Coordinator->>TaskDelegator: assign_task(task_id, agent_id)
    TaskDelegator->>EventBus: Publish execute_task command
    EventBus-->>SpecialistAgent: Receive execute_task command
    TaskDelegator-->>Coordinator: assignment result
    Coordinator->>ResultAggregator: register_task(task_id)
    ResultAggregator-->>Coordinator: registration result
    Coordinator-->>ExecutiveAgent: task_id
```

## Task Execution Flow

```mermaid
sequenceDiagram
    participant SpecialistAgent
    participant EventBus
    participant Coordinator
    participant TaskDelegator
    participant ResultAggregator
    participant ExecutiveAgent

    SpecialistAgent->>SpecialistAgent: Process task
    SpecialistAgent->>EventBus: Publish task_completed event
    EventBus-->>TaskDelegator: Receive task_completed event
    TaskDelegator->>TaskDelegator: Update task status
    TaskDelegator->>EventBus: Publish task_status_updated event
    EventBus-->>ResultAggregator: Receive task_completed event
    ResultAggregator->>ResultAggregator: Add result
    ResultAggregator->>EventBus: Publish result_added event
    EventBus-->>ExecutiveAgent: Receive task_status_updated event
    ExecutiveAgent->>Coordinator: get_task_result(task_id)
    Coordinator->>TaskDelegator: get_task(task_id)
    TaskDelegator-->>Coordinator: task
    Coordinator->>ResultAggregator: aggregate_results(task_id)
    ResultAggregator-->>Coordinator: aggregated_result
    Coordinator-->>ExecutiveAgent: task_result
```

## Task Decomposition Flow

```mermaid
sequenceDiagram
    participant ExecutiveAgent
    participant Coordinator
    participant TaskDelegator
    participant ResultAggregator
    participant SpecialistAgent1
    participant SpecialistAgent2
    participant EventBus

    ExecutiveAgent->>Coordinator: delegate_task(task_type, parameters)
    Coordinator->>TaskDelegator: create_task(task_type, parameters)
    TaskDelegator-->>Coordinator: parent_task_id
    Coordinator-->>ExecutiveAgent: parent_task_id
    ExecutiveAgent->>TaskDelegator: decompose_task(parent_task_id, subtask_definitions)
    TaskDelegator->>TaskDelegator: Create subtasks
    TaskDelegator->>EventBus: Publish task_created events
    TaskDelegator-->>ExecutiveAgent: subtask_ids
    TaskDelegator->>EventBus: Publish execute_task commands
    EventBus-->>SpecialistAgent1: Receive execute_task command
    EventBus-->>SpecialistAgent2: Receive execute_task command
    SpecialistAgent1->>EventBus: Publish task_completed event
    SpecialistAgent2->>EventBus: Publish task_completed event
    EventBus-->>TaskDelegator: Receive task_completed events
    TaskDelegator->>TaskDelegator: Update subtask statuses
    TaskDelegator->>TaskDelegator: Check parent task completion
    TaskDelegator->>TaskDelegator: Update parent task status
    TaskDelegator->>EventBus: Publish task_status_updated event
    EventBus-->>ExecutiveAgent: Receive task_status_updated event
    ExecutiveAgent->>Coordinator: get_task_result(parent_task_id)
    Coordinator->>TaskDelegator: get_task(parent_task_id)
    TaskDelegator-->>Coordinator: parent_task
    Coordinator->>ResultAggregator: aggregate_results(parent_task_id)
    ResultAggregator-->>Coordinator: aggregated_result
    Coordinator-->>ExecutiveAgent: parent_task_result
```

## Conflict Resolution Flow

```mermaid
sequenceDiagram
    participant Agent1
    participant Agent2
    participant Coordinator
    participant ConflictResolver
    participant EventBus

    Agent1->>EventBus: Publish resource_request event
    Agent2->>EventBus: Publish resource_request event
    EventBus-->>Coordinator: Detect conflicting requests
    Coordinator->>ConflictResolver: detect_conflict(conflict_type, entities, description)
    ConflictResolver->>EventBus: Publish conflict_detected event
    ConflictResolver-->>Coordinator: conflict_id
    Coordinator->>ConflictResolver: resolve_conflict(conflict_id, strategy, parameters)
    ConflictResolver->>ConflictResolver: Apply resolution strategy
    ConflictResolver->>EventBus: Publish conflict_resolved event
    ConflictResolver-->>Coordinator: resolution_result
    Coordinator-->>Agent1: Notify of resolution
    Coordinator-->>Agent2: Notify of resolution
```

## Market Analysis Scenario

```mermaid
sequenceDiagram
    participant ExecutiveAgent
    participant Coordinator
    participant MarketDataAgent
    participant MarketAnalysisAgent
    participant EventBus

    ExecutiveAgent->>Coordinator: delegate_task(get_market_data, {market, symbol})
    Coordinator->>Coordinator: Find agent with market_data capability
    Coordinator->>EventBus: Publish execute_task command
    EventBus-->>MarketDataAgent: Receive execute_task command
    MarketDataAgent->>MarketDataAgent: Get market data
    MarketDataAgent->>EventBus: Publish task_completed event
    EventBus-->>Coordinator: Receive task_completed event
    Coordinator->>Coordinator: Update task status
    ExecutiveAgent->>Coordinator: get_task_result(market_data_task_id)
    Coordinator-->>ExecutiveAgent: market_data_result
    ExecutiveAgent->>Coordinator: delegate_task(analyze_market, {market, symbol})
    Coordinator->>Coordinator: Find agent with market_analysis capability
    Coordinator->>EventBus: Publish execute_task command
    EventBus-->>MarketAnalysisAgent: Receive execute_task command
    MarketAnalysisAgent->>MarketAnalysisAgent: Analyze market data
    MarketAnalysisAgent->>EventBus: Publish task_completed event
    EventBus-->>Coordinator: Receive task_completed event
    Coordinator->>Coordinator: Update task status
    ExecutiveAgent->>Coordinator: get_task_result(market_analysis_task_id)
    Coordinator-->>ExecutiveAgent: market_analysis_result
    ExecutiveAgent->>ExecutiveAgent: Make investment decision
    ExecutiveAgent->>EventBus: Publish investment_decision event
```

## Mobile-Optimized Coordination Flow

```mermaid
sequenceDiagram
    participant MobileAgent
    participant Coordinator
    participant AgentRegistry
    participant TaskDelegator
    participant EventBus

    MobileAgent->>Coordinator: register_agent(agent_info)
    Coordinator->>AgentRegistry: register_agent(agent_info)
    AgentRegistry->>EventBus: Publish agent_registered event
    AgentRegistry-->>Coordinator: Registration result
    Coordinator-->>MobileAgent: Registration result
    MobileAgent->>EventBus: Publish device_state event (battery=low)
    EventBus-->>Coordinator: Receive device_state event
    Coordinator->>Coordinator: Update agent metadata
    Coordinator->>TaskDelegator: delegate_task(task_type, parameters, target_agent_id)
    TaskDelegator->>TaskDelegator: Adjust task priority based on device state
    TaskDelegator->>EventBus: Publish execute_task command (low priority)
    EventBus-->>MobileAgent: Receive execute_task command
    MobileAgent->>MobileAgent: Process task (battery-efficient mode)
    MobileAgent->>EventBus: Publish task_completed event
    EventBus-->>Coordinator: Receive task_completed event
    Coordinator->>Coordinator: Update task status
```
