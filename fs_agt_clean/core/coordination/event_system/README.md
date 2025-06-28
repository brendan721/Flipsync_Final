# Event System

The Event System is a core component of the FlipSync application that enables asynchronous, loosely-coupled communication between agents and components. It is a critical part of the interconnected agent vision.

## Overview

The Event System consists of the following components:

- **Events**: Discrete pieces of information that can be published and consumed
- **Event Bus**: Central component that routes events from publishers to subscribers
- **Publishers**: Components that publish events to the event bus
- **Subscribers**: Components that subscribe to events from the event bus

The Event System is designed to be:

- **Mobile-optimized**: Efficient event routing with minimal overhead
- **Vision-aligned**: Supporting all core vision elements
- **Robust**: Comprehensive error handling and recovery
- **Scalable**: Capable of handling high volumes of events

## Event Types

The Event System supports the following event types:

- **Command**: Directive to perform an action
- **Notification**: Information about a state change
- **Query**: Request for information
- **Response**: Reply to a query
- **Error**: Error notification

## Usage

### Creating an Event Bus

```python
from migration_plan.fs_clean.core.coordination.event_system import InMemoryEventBus, set_event_bus

# Create an event bus
event_bus = InMemoryEventBus(bus_id="my_event_bus")

# Set it as the singleton instance
set_event_bus(event_bus)
```

### Creating a Publisher

```python
from migration_plan.fs_clean.core.coordination.event_system import create_publisher

# Create a publisher
publisher = create_publisher(source_id="my_publisher")
```

### Creating a Subscriber

```python
from migration_plan.fs_clean.core.coordination.event_system import create_subscriber

# Create a subscriber
subscriber = create_subscriber(subscriber_id="my_subscriber")
```

### Publishing Events

```python
# Publish a command
await publisher.publish_command(
    command_name="do_something",
    parameters={"param1": "value1"},
    target="target_agent"
)

# Publish a notification
await publisher.publish_notification(
    notification_name="something_happened",
    data={"field1": "value1"}
)

# Publish a query
await publisher.publish_query(
    query_name="get_information",
    parameters={"param1": "value1"},
    target="target_agent"
)

# Publish a response
await publisher.publish_response(
    query_id="query_event_id",
    response_data={"result": "value"},
    is_success=True
)

# Publish an error
await publisher.publish_error(
    error_code="ERROR_CODE",
    error_message="Something went wrong",
    source_event_id="source_event_id",
    details={"field1": "value1"}
)
```

### Subscribing to Events

```python
from migration_plan.fs_clean.core.coordination.event_system import EventTypeFilter, EventNameFilter

# Define a handler for events
async def handle_command(event):
    print(f"Received command: {event.command_name}")
    print(f"Parameters: {event.parameters}")
    
    # Do something with the command
    result = process_command(event)
    
    # Send a response
    await publisher.publish_response(
        query_id=event.event_id,
        response_data={"result": result},
        is_success=True
    )

# Subscribe to commands
await subscriber.subscribe(
    filter=EventTypeFilter(event_types={EventType.COMMAND}),
    handler=handle_command
)

# Subscribe to specific commands
await subscriber.subscribe(
    filter=EventNameFilter(event_names={"do_something"}),
    handler=handle_command
)
```

### Using Subscription Filters

```python
from migration_plan.fs_clean.core.coordination.event_system import (
    EventTypeFilter, EventNameFilter, EventSourceFilter, EventTargetFilter,
    EventPriorityFilter, EventNamePatternFilter, CompositeFilter, CustomFilter
)

# Filter by event type
type_filter = EventTypeFilter(event_types={EventType.COMMAND})

# Filter by event name
name_filter = EventNameFilter(event_names={"do_something"})

# Filter by source
source_filter = EventSourceFilter(sources={"my_publisher"})

# Filter by target
target_filter = EventTargetFilter(targets={"target_agent"})

# Filter by priority
priority_filter = EventPriorityFilter(min_priority=EventPriority.HIGH)

# Filter by name pattern
pattern_filter = EventNamePatternFilter(patterns=["do_.*"])

# Composite filter (all filters must match)
composite_filter = CompositeFilter(
    filters=[type_filter, name_filter],
    require_all=True
)

# Composite filter (any filter can match)
any_filter = CompositeFilter(
    filters=[type_filter, name_filter],
    require_all=False
)

# Custom filter
async def custom_predicate(event):
    return event.command_name == "do_something" and event.parameters.get("param1") == "value1"

custom_filter = CustomFilter(predicate=custom_predicate)
```

### Managing Subscriptions

```python
# Subscribe to events
subscription_id = await subscriber.subscribe(
    filter=EventTypeFilter(event_types={EventType.COMMAND}),
    handler=handle_command
)

# Pause a subscription
await subscriber.pause_subscription(subscription_id)

# Resume a subscription
await subscriber.resume_subscription(subscription_id)

# Unsubscribe from events
await subscriber.unsubscribe(subscription_id)

# Get all subscriptions
subscriptions = await subscriber.get_subscriptions()

# Get subscriptions for a specific subscriber
subscriptions = await subscriber.get_subscriptions(subscriber_id="my_subscriber")
```

### Working with the Event Bus

```python
# Get an event by ID
event = await event_bus.get_event(event_id)

# Get events by criteria
events = await event_bus.get_events(
    event_type=EventType.COMMAND,
    source="my_publisher",
    target="target_agent",
    start_time=datetime.now() - timedelta(hours=1),
    end_time=datetime.now(),
    limit=100
)

# Replay events
await event_bus.replay_events(
    event_type=EventType.COMMAND,
    source="my_publisher",
    limit=100
)

# Get dead letter events
dead_letter_events = await event_bus.get_dead_letter_events()

# Retry a dead letter event
await event_bus.retry_dead_letter_event(event_id)

# Clear a dead letter event
await event_bus.clear_dead_letter_event(event_id)

# Get metrics
metrics = await event_bus.get_metrics()
```

## Vision Alignment

The Event System is designed to support FlipSync's vision elements:

### Interconnected Agent System

- **Event-Based Communication**: Enables asynchronous, loosely-coupled communication between agents
- **Correlation ID**: Tracks requests across multiple agents
- **Causation ID**: Establishes causal relationships between events
- **Event Replay**: Enables recovery and analysis of agent interactions

### Mobile-First Approach

- **Efficient Serialization**: Minimizes data transfer
- **Mobile Optimization**: Adapts behavior based on device capabilities
- **Offline Support**: Stores events for later delivery when offline
- **Battery Efficiency**: Minimizes battery usage

### Conversational Interface

- **Conversation Context**: Includes conversation ID in event metadata
- **User Context**: Includes user ID in event metadata
- **Intent Propagation**: Enables propagation of user intent across agents
- **Response Correlation**: Correlates responses with requests

### Intelligent Decision Making

- **Decision Context**: Includes decision ID in event metadata
- **Confidence Levels**: Includes confidence in event metadata
- **Feedback Loops**: Enables feedback on decision outcomes
- **Learning Events**: Supports events for learning and adaptation

## Implementation Details

### Event Metadata

Events include the following metadata:

- **Event ID**: Unique identifier for the event
- **Correlation ID**: ID for tracking related events
- **Causation ID**: ID of the event that caused this event
- **Event Type**: Type of the event (command, notification, query, response, error)
- **Event Name**: Name of the event
- **Version**: Version of the event schema
- **Source**: Source of the event (agent or component)
- **Target**: Target of the event (agent or component)
- **Priority**: Priority of the event
- **Created At**: Time the event was created
- **Published At**: Time the event was published
- **Expires At**: Time the event expires
- **Status**: Status of the event (created, published, delivered, processing, completed, failed, retrying)
- **Retry Count**: Number of retry attempts
- **Max Retries**: Maximum number of retry attempts
- **Mobile Optimization**: Flags for mobile optimization
- **Conversation Context**: IDs for conversation tracking
- **Decision Context**: IDs and metrics for decision tracking
- **Custom Metadata**: Custom metadata fields

### Event Bus Features

The Event Bus provides the following features:

- **Event Routing**: Routes events from publishers to subscribers
- **Event Persistence**: Stores events for later retrieval
- **Event Replay**: Replays events for recovery and analysis
- **Dead Letter Queue**: Stores events that could not be delivered
- **Retry Mechanism**: Retries failed deliveries
- **Metrics Collection**: Collects metrics on event processing
- **Mobile Optimization**: Optimizes for mobile devices

### Publisher Features

Publishers provide the following features:

- **Event Creation**: Creates events of different types
- **Event Publishing**: Publishes events to the event bus
- **Batch Publishing**: Publishes multiple events at once
- **Error Handling**: Handles errors during publishing

### Subscriber Features

Subscribers provide the following features:

- **Event Filtering**: Filters events based on criteria
- **Event Handling**: Handles events with custom handlers
- **Subscription Management**: Manages subscriptions (pause, resume, unsubscribe)
- **Concurrency Control**: Controls the number of concurrent event handlers
- **Error Handling**: Handles errors during event processing

## Best Practices

### Event Design

- **Keep Events Small**: Events should contain only the necessary information
- **Use Appropriate Event Types**: Use the right event type for the purpose
- **Include Correlation IDs**: Always include correlation IDs for tracking
- **Version Events**: Include version information for schema evolution
- **Use Meaningful Names**: Use clear, descriptive names for events

### Publishing

- **Set Source ID**: Always set the source ID for events
- **Set Appropriate Priority**: Use appropriate priority levels
- **Handle Errors**: Always handle errors during publishing
- **Use Batch Publishing**: Use batch publishing for high-volume scenarios
- **Set Expiration**: Set expiration times for time-sensitive events

### Subscribing

- **Use Specific Filters**: Use specific filters to receive only relevant events
- **Handle Errors**: Always handle errors during event processing
- **Limit Concurrency**: Set appropriate concurrency limits for handlers
- **Manage Subscriptions**: Properly manage subscriptions (pause, resume, unsubscribe)
- **Use Composite Filters**: Use composite filters for complex filtering

### Error Handling

- **Retry Failed Deliveries**: Retry failed deliveries with appropriate backoff
- **Monitor Dead Letter Queue**: Regularly check the dead letter queue
- **Log Errors**: Log errors with appropriate context
- **Set Max Retries**: Set appropriate maximum retry attempts
- **Handle Permanent Failures**: Have a strategy for handling permanent failures

## Mobile Optimization

The Event System includes several optimizations for mobile devices:

- **Efficient Serialization**: Minimizes data transfer
- **Compression**: Compresses events when appropriate
- **Batching**: Batches events for efficient transmission
- **Prioritization**: Prioritizes events based on importance
- **Offline Support**: Stores events for later delivery when offline
- **Battery Efficiency**: Minimizes battery usage by optimizing processing

## Testing

The Event System includes comprehensive tests:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test components working together
- **End-to-End Tests**: Test complete event flows
- **Performance Tests**: Test performance under load
- **Mobile Tests**: Test mobile optimizations

## Future Enhancements

Planned enhancements for the Event System:

- **Distributed Event Bus**: Support for distributed event processing
- **Event Schemas**: Schema validation for events
- **Event Versioning**: Better support for event schema evolution
- **Event Sourcing**: Support for event sourcing patterns
- **Event Store**: Persistent event store for long-term storage
- **Event Visualization**: Tools for visualizing event flows
- **Event Analytics**: Tools for analyzing event patterns
- **Event Monitoring**: Better monitoring and alerting for events
