# Decision Pipeline Component

The Decision Pipeline component is a core part of the FlipSync application that enables intelligent, adaptive decision making. It provides a structured approach to making decisions, incorporating multiple inputs and learning from outcomes.

## Overview

The Decision Pipeline consists of the following components:

- **Decision Maker**: Makes decisions based on context and options
- **Decision Validator**: Validates decisions against rules and constraints
- **Decision Tracker**: Tracks decision status and outcomes
- **Feedback Processor**: Processes feedback on decision outcomes
- **Learning Engine**: Learns from decision outcomes to improve future decisions

The Decision Pipeline is designed to be:

- **Mobile-optimized**: Efficient operation on mobile devices
- **Vision-aligned**: Supporting all core vision elements
- **Robust**: Comprehensive error handling and recovery
- **Scalable**: Capable of handling complex agent ecosystems

## Decision Maker

The Decision Maker component is responsible for making decisions based on context, options, and constraints. It evaluates options and selects the best one based on various factors.

### Decision Types

The Decision Pipeline supports the following decision types:

- **Action**: Decision to take an action
- **Recommendation**: Decision to recommend something
- **Optimization**: Decision to optimize something
- **Allocation**: Decision to allocate resources
- **Prioritization**: Decision to prioritize something
- **Scheduling**: Decision to schedule something
- **Selection**: Decision to select something
- **Classification**: Decision to classify something
- **Prediction**: Decision to predict something
- **Custom**: Custom decision type

### Decision Status

Decisions can have the following statuses:

- **Pending**: Decision is pending
- **Validating**: Decision is being validated
- **Approved**: Decision has been approved
- **Rejected**: Decision has been rejected
- **Executing**: Decision is being executed
- **Completed**: Decision has been completed
- **Failed**: Decision execution failed
- **Canceled**: Decision was canceled
- **Expired**: Decision has expired

## Decision Validator

The Decision Validator component is responsible for validating decisions against rules and constraints. It ensures that decisions are valid and can be executed.

### Built-in Validation Rules

The Decision Validator includes the following built-in validation rules:

- **Minimum Confidence**: Ensures that decisions have a minimum confidence level
- **Required Reasoning**: Ensures that decisions have adequate reasoning
- **Allowed Decision Types**: Restricts decisions to specific types
- **Battery Efficiency**: Ensures that decisions are battery-efficient
- **Network Efficiency**: Ensures that decisions are network-efficient

## Decision Tracker

The Decision Tracker component is responsible for tracking decisions and their outcomes. It maintains a history of decisions and provides metrics on decision quality.

### Decision Tracking

The Decision Tracker provides the following capabilities:

- **Decision History**: Maintains a history of all decisions
- **Status Tracking**: Tracks the status of decisions over time
- **Decision Metrics**: Provides metrics on decision quality and outcomes
- **Event Publication**: Publishes events when decisions are tracked or updated
- **Offline Tracking**: Supports tracking decisions when offline

### Decision Metrics

The Decision Tracker provides the following metrics:

- **Total Decisions**: Total number of decisions tracked
- **Decisions by Status**: Number of decisions in each status
- **Decisions by Type**: Number of decisions of each type
- **Average Confidence**: Average confidence level across all decisions

### Mobile Optimization

The Decision Tracker includes several optimizations for mobile devices:

- **Offline Tracking**: Decisions can be tracked offline and synchronized later
- **Efficient Storage**: Decisions are stored efficiently to minimize memory usage
- **Filtered Metrics**: Metrics can be filtered to reduce computation on mobile devices
- **Battery-Aware Event Publication**: Events are published only when necessary

## Feedback Processor

The Feedback Processor component is responsible for processing feedback on decision outcomes. It collects feedback and prepares it for learning.

### Feedback Processing

The Feedback Processor provides the following capabilities:

- **Feedback Collection**: Collects feedback on decision outcomes
- **Feedback Storage**: Stores feedback for later analysis
- **Feedback Retrieval**: Retrieves feedback by ID or filters
- **Feedback Statistics**: Provides statistics on feedback quality
- **Event Publication**: Publishes events when feedback is processed
- **Offline Processing**: Supports processing feedback when offline

### Feedback Data

Feedback data can include various metrics and comments:

- **Quality**: Rating of the decision quality
- **Relevance**: Rating of the decision relevance
- **Comments**: Textual feedback on the decision
- **Category**: Categorization of the feedback
- **User ID**: Identifier of the user providing feedback

### Mobile Optimization

The Feedback Processor includes several optimizations for mobile devices:

- **Offline Processing**: Feedback can be processed offline and synchronized later
- **Efficient Storage**: Feedback is stored efficiently to minimize memory usage
- **Filtered Retrieval**: Feedback can be filtered to reduce data transfer
- **Battery-Aware Event Publication**: Events are published only when necessary

## Learning Engine

The Learning Engine component is responsible for learning from decision outcomes and feedback. It adapts decision-making strategies based on past performance.

### Learning Capabilities

The Learning Engine provides the following capabilities:

- **Feedback Learning**: Learns from feedback on decision outcomes
- **Confidence Adjustment**: Adjusts confidence levels based on past performance
- **Decision Type Weighting**: Learns which decision types perform better
- **Learning Metrics**: Provides metrics on learning performance
- **Event Publication**: Publishes events when learning is completed
- **Learning Reset**: Supports resetting learning state

### Learning Metrics

The Learning Engine provides the following metrics:

- **Feedback Count**: Total number of feedback items processed
- **Learning Iterations**: Number of learning iterations performed
- **Confidence Adjustments**: Adjustments to confidence levels by decision type
- **Decision Type Weights**: Weights for different decision types
- **Last Learning Time**: When the last learning occurred

### Mobile Optimization

The Learning Engine includes several optimizations for mobile devices:

- **Battery-Efficient Learning**: Simplified learning algorithms when battery is low
- **Efficient Storage**: Learning data is stored efficiently to minimize memory usage
- **Incremental Learning**: Learning is performed incrementally to minimize resource usage
- **Battery-Aware Event Publication**: Events are published only when necessary

## Decision Pipeline

The Decision Pipeline component orchestrates the entire decision-making process, from making a decision to executing it and learning from the outcome. It combines all the other components into a cohesive workflow.

### Pipeline Workflow

The Decision Pipeline provides the following workflow:

1. **Decision Making**: Makes decisions based on context, options, and constraints
2. **Decision Validation**: Validates decisions against rules and constraints
3. **Decision Execution**: Executes decisions and tracks their status
4. **Feedback Processing**: Processes feedback on decision outcomes
5. **Learning**: Learns from feedback to improve future decisions

### Error Handling

The Decision Pipeline includes comprehensive error handling:

- **Decision Errors**: Specific error types for different failure scenarios
- **Error Recovery**: Graceful recovery from errors when possible
- **Error Reporting**: Detailed error messages for debugging
- **Error Logging**: Comprehensive logging of errors

### Mobile Optimization

The Decision Pipeline includes several optimizations for mobile devices:

- **Battery-Aware Decision Making**: Prioritizes battery-efficient decisions when battery is low
- **Network-Aware Decision Making**: Prioritizes network-efficient decisions when on cellular networks
- **Offline Execution**: Supports executing decisions when offline
- **Offline Feedback**: Supports processing feedback when offline
- **Battery-Efficient Learning**: Uses simplified learning algorithms when battery is low

## Usage

### Creating a Decision Pipeline

```python
from migration_plan.fs_clean.core.coordination.decision import (
    InMemoryDecisionMaker, RuleBasedValidator, InMemoryDecisionTracker,
    InMemoryFeedbackProcessor, InMemoryLearningEngine, StandardDecisionPipeline
)
from migration_plan.fs_clean.core.coordination.event_system import create_publisher

# Create a publisher for events
publisher = create_publisher(source_id="my_publisher")

# Create components
decision_maker = InMemoryDecisionMaker(maker_id="my_decision_maker")
decision_validator = RuleBasedValidator(validator_id="my_validator")
decision_tracker = InMemoryDecisionTracker(
    tracker_id="my_tracker",
    publisher=publisher
)
feedback_processor = InMemoryFeedbackProcessor(
    processor_id="my_processor",
    publisher=publisher
)
learning_engine = InMemoryLearningEngine(
    engine_id="my_engine",
    publisher=publisher
)

# Create the pipeline
pipeline = StandardDecisionPipeline(
    pipeline_id="my_pipeline",
    decision_maker=decision_maker,
    decision_validator=decision_validator,
    decision_tracker=decision_tracker,
    feedback_processor=feedback_processor,
    learning_engine=learning_engine,
    publisher=publisher
)

# Add validation rules
await decision_validator.add_built_in_rule("minimum_confidence", min_confidence=0.7)
await decision_validator.add_built_in_rule("required_reasoning", min_length=20)
```

### Using the Decision Pipeline

```python
# Define context and options
context = {
    "user_id": "user123",
    "scenario": "product_recommendation",
    "device_info": {
        "battery_level": 0.8,
        "network_type": "wifi"
    }
}

options = [
    {
        "id": "product1",
        "name": "Product 1",
        "value": 85,
        "battery_cost": 0.1,
        "network_cost": 0.2
    },
    {
        "id": "product2",
        "name": "Product 2",
        "value": 90,
        "battery_cost": 0.3,
        "network_cost": 0.4
    }
]

# Define constraints
constraints = {
    "min_value": 80,
    "max_battery_cost": 0.5
}

# 1. Make a decision
decision = await pipeline.make_decision(context, options, constraints)

# 2. Validate the decision
is_valid, messages = await pipeline.validate_decision(decision)

if not is_valid:
    print(f"Decision is invalid: {messages}")
    return

# 3. Execute the decision
result = await pipeline.execute_decision(decision)

if result:
    print(f"Decision executed: {decision.action}")

# 4. Process feedback
feedback_data = {
    "quality": 0.9,
    "relevance": 0.8,
    "comments": "Good decision",
    "outcome": "success"
}

await pipeline.process_feedback(decision.metadata.decision_id, feedback_data)

# 5. Get decision history
history = await pipeline.get_decision_history()
print(f"Decision history: {len(history)} decisions")
```

## Mobile Optimization

The Decision Pipeline includes several optimizations for mobile devices:

- **Efficient Decision Making**: Minimizes computational overhead
- **Battery-Aware Operation**: Adjusts complexity based on battery level
- **Offline Decision Making**: Enables decision making without network connectivity
- **Bandwidth-Aware Synchronization**: Minimizes data transfer for decision updates

### Battery Optimization

The Decision Maker considers battery level when making decisions:

- When battery level is low (<30%), it prioritizes options with lower battery cost
- It sets the `battery_efficient` flag on decisions to indicate battery efficiency
- The Decision Validator can enforce battery efficiency when required

### Network Optimization

The Decision Maker considers network conditions when making decisions:

- When on cellular networks, it prioritizes options with lower network cost
- It sets the `network_efficient` flag on decisions to indicate network efficiency
- The Decision Validator can enforce network efficiency when required

### Mobile Optimization Example

```python
# Mobile-optimized decision making
context = {
    "user_id": "user123",
    "scenario": "product_recommendation",
    "device_info": {
        "battery_level": 0.2,  # Low battery
        "network_type": "cellular"  # Cellular network
    }
}

# Make a battery and network efficient decision
decision = await pipeline.make_decision(context, options)

# Check efficiency flags
print(f"Battery efficient: {decision.battery_efficient}")
print(f"Network efficient: {decision.network_efficient}")

# Execute the decision offline
await pipeline.execute_decision(decision, offline=True)

# Process feedback offline with battery efficiency
feedback_data = {
    "quality": 0.9,
    "relevance": 0.8,
    "comments": "Good decision",
    "outcome": "success",
    "battery_level": 0.2
}

await pipeline.process_feedback(
    decision.metadata.decision_id,
    feedback_data,
    offline=True,
    battery_efficient=True
)

# Sync offline data when back online
await decision_tracker.sync_offline_decisions()
await feedback_processor.sync_offline_feedback()
```

## Vision Alignment

The Decision Pipeline supports FlipSync's vision elements:

### Interconnected Agent System

- **Coordinated Decision Making**: Enables coordinated decisions across agents
- **Decision Context**: Maintains decision context across agents
- **Decision Validation**: Ensures decisions align with system constraints
- **Decision Tracking**: Tracks decisions across the agent ecosystem

### Mobile-First Approach

- **Battery-Aware Decisions**: Optimizes decisions based on battery level
- **Network-Aware Decisions**: Optimizes decisions based on network conditions
- **Efficient Serialization**: Minimizes data transfer for decisions
- **Offline Decision Making**: Enables decisions without network connectivity

### Conversational Interface

- **Decision Context**: Provides decision context for conversations
- **Decision Reasoning**: Includes reasoning for decisions
- **Decision Alternatives**: Tracks alternative options for discussions
- **Decision Confidence**: Communicates confidence in decisions

### Intelligent Decision Making

- **Context-Aware Decisions**: Considers context in decision making
- **Confidence Levels**: Includes confidence in decisions
- **Learning from Feedback**: Adapts based on decision outcomes
- **Decision Validation**: Ensures decision quality
