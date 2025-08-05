# Knowledge Repository Component

The Knowledge Repository component is a core part of the FlipSync application that enables knowledge storage, retrieval, and sharing between agents. It provides vector-based knowledge storage, publish/subscribe knowledge sharing patterns, and mobile-optimized knowledge access.

## Overview

The Knowledge Repository consists of the following components:

- **Knowledge Repository**: Core interface for knowledge storage and retrieval
- **Vector Storage**: Stores and retrieves vector representations of knowledge
- **Embedding Provider**: Generates vector embeddings from knowledge content
- **Knowledge Publisher**: Publishes knowledge to the repository
- **Knowledge Subscriber**: Subscribes to knowledge updates
- **Knowledge Validator**: Validates knowledge before it's added to the repository
- **Knowledge Retriever**: Retrieves knowledge from the repository
- **Knowledge Cache**: Caches knowledge for efficient access and offline operation

The Knowledge Repository is designed to be:

- **Mobile-optimized**: Efficient operation on mobile devices
- **Vision-aligned**: Supporting all core vision elements
- **Robust**: Comprehensive error handling and recovery
- **Scalable**: Capable of handling large knowledge repositories

## Knowledge Items

Knowledge items are the core data structure of the Knowledge Repository. Each knowledge item has:

- **ID**: Unique identifier for the knowledge item
- **Type**: Type of knowledge (FACT, RULE, PROCEDURE, etc.)
- **Topic**: Topic or category of the knowledge
- **Content**: Content of the knowledge item
- **Vector**: Vector representation of the knowledge
- **Metadata**: Additional metadata about the knowledge
- **Source**: Source that created the knowledge
- **Timestamps**: Creation and update timestamps
- **Status**: Status of the knowledge item (DRAFT, ACTIVE, etc.)
- **Version**: Version number
- **Access Control**: Access control information
- **Tags**: Tags for categorizing the knowledge

## Vector Storage

The Vector Storage component stores and retrieves vector representations of knowledge items, enabling similarity search and other vector-based operations. It provides:

- **Vector Storage**: Stores vectors and metadata
- **Similarity Search**: Finds similar vectors
- **Indexing**: Efficient retrieval of vectors
- **Metadata Management**: Stores and retrieves metadata

## Embedding Provider

The Embedding Provider component generates vector embeddings from knowledge content, enabling similarity search and other vector-based operations. It provides:

- **Embedding Generation**: Generates embeddings from content
- **Multiple Providers**: Support for different embedding models
- **Dimensionality Management**: Handles high-dimensional vectors

## Knowledge Publisher

The Knowledge Publisher component publishes knowledge to the repository, including validation and notification. It provides:

- **Knowledge Publication**: Publishes knowledge items
- **Knowledge Update**: Updates existing knowledge items
- **Knowledge Deletion**: Deletes knowledge items
- **Batch Publication**: Publishes multiple knowledge items

## Knowledge Subscriber

The Knowledge Subscriber component subscribes to knowledge updates in the repository, including filtering and notification. It provides:

- **Subscription Management**: Manages subscriptions
- **Filtering**: Filters knowledge items by topic, source, type, etc.
- **Notification**: Notifies subscribers about knowledge updates

## Knowledge Validator

The Knowledge Validator component validates knowledge before it's added to the repository. It provides:

- **Schema Validation**: Validates knowledge against schemas
- **Content Validation**: Validates knowledge content
- **Source Validation**: Validates knowledge sources

## Knowledge Retriever

The Knowledge Retriever component retrieves knowledge from the repository, including similarity search and filtering. It provides:

- **Knowledge Retrieval**: Retrieves knowledge items
- **Similarity Search**: Finds similar knowledge items
- **Filtering**: Filters knowledge items by metadata
- **Query Processing**: Processes natural language queries

## Knowledge Cache

The Knowledge Cache component caches knowledge for efficient access and offline operation. It provides:

- **Caching**: Caches knowledge items
- **Cache Management**: Manages cache size and replacement
- **Offline Access**: Enables access to cached knowledge when offline
- **Synchronization**: Synchronizes cache with repository

## Usage

### Creating a Knowledge Repository

```python
from migration_plan.fs_clean.core.coordination.knowledge_repository import (
    InMemoryKnowledgeRepository
)

# Create a knowledge repository
repository = InMemoryKnowledgeRepository(repository_id="my_repository")

# Start the repository
await repository.start()
```

### Publishing Knowledge

```python
from migration_plan.fs_clean.core.coordination.knowledge_repository import (
    KnowledgeType
)

# Publish a knowledge item
knowledge_id = await repository.publish_knowledge(
    knowledge_type=KnowledgeType.FACT,
    topic="market/crypto/bitcoin",
    content={"price": 50000, "volume": 1000000},
    metadata={"timestamp": "2023-01-01T00:00:00"},
    source_id="market_agent",
    tags={"market", "crypto", "bitcoin"}
)
```

### Retrieving Knowledge

```python
# Get a knowledge item by ID
knowledge = await repository.get_knowledge(knowledge_id)

# Get knowledge items by topic
bitcoin_knowledge = await repository.get_knowledge_by_topic("market/crypto/bitcoin")

# Get knowledge items by type
facts = await repository.get_knowledge_by_type(KnowledgeType.FACT)

# Get knowledge items by tag
crypto_knowledge = await repository.get_knowledge_by_tag("crypto")

# Search for knowledge
results = await repository.search_knowledge("bitcoin", limit=10)
for result in results:
    print(f"{result.knowledge.topic}: {result.score}")
```

### Subscribing to Knowledge

```python
from migration_plan.fs_clean.core.coordination.knowledge_repository import (
    TopicFilter
)

# Define a handler for knowledge updates
async def handle_bitcoin_knowledge(knowledge):
    print(f"Received bitcoin knowledge: {knowledge.content}")

# Subscribe to bitcoin knowledge
subscription_id = await repository.subscribe(
    filter=TopicFilter(topics={"market/crypto/bitcoin"}),
    handler=handle_bitcoin_knowledge
)
```

### Updating Knowledge

```python
# Update a knowledge item
updated_id = await repository.update_knowledge(
    knowledge_id=knowledge_id,
    content={"price": 55000, "volume": 1200000},
    metadata={"timestamp": "2023-01-02T00:00:00"}
)
```

### Deleting Knowledge

```python
# Delete a knowledge item
deleted = await repository.delete_knowledge(knowledge_id)
```

## Mobile Optimization

The Knowledge Repository includes several optimizations for mobile devices:

- **Efficient Vector Storage**: Minimizes memory usage
- **Knowledge Caching**: Caches frequently accessed knowledge
- **Bandwidth-Aware Synchronization**: Minimizes network usage
- **Offline Access**: Enables operation without connectivity
- **Incremental Updates**: Minimizes data transfer

## Vision Alignment

The Knowledge Repository is designed to support FlipSync's vision elements:

### Interconnected Agent System

- **Knowledge Sharing**: Enables agents to share knowledge
- **Publish/Subscribe**: Facilitates knowledge distribution
- **Vector-Based Storage**: Enables semantic knowledge representation
- **Knowledge Validation**: Ensures knowledge quality

### Mobile-First Approach

- **Efficient Storage**: Minimizes memory usage
- **Bandwidth-Aware Synchronization**: Minimizes network usage
- **Offline Access**: Enables operation without connectivity
- **Incremental Updates**: Minimizes data transfer

### Conversational Interface

- **Knowledge Context**: Maintains context across conversations
- **Topic-Based Organization**: Organizes knowledge by topic
- **Natural Language Queries**: Enables conversational knowledge retrieval
- **Knowledge Versioning**: Tracks knowledge evolution

### Intelligent Decision Making

- **Vector-Based Knowledge**: Enables semantic understanding
- **Similarity Search**: Finds relevant knowledge
- **Knowledge Aggregation**: Combines knowledge from multiple sources
- **Knowledge Validation**: Ensures decision quality

## Implementation Details

### Event-Based Communication

The Knowledge Repository uses the Event System for communication between components and with agents. It publishes and subscribes to the following event types:

- **Knowledge Events**: Added, updated, deleted
- **Query Events**: Queries and responses
- **Subscription Events**: Subscriptions and notifications

### Mobile Optimization

The Knowledge Repository includes several optimizations for mobile devices:

- **Efficient Vector Storage**: Uses compact vector representations
- **Knowledge Caching**: Implements LRU caching
- **Bandwidth-Aware Synchronization**: Adapts to network conditions
- **Offline Access**: Enables operation without connectivity
- **Incremental Updates**: Implements delta updates

### Error Handling

The Knowledge Repository includes comprehensive error handling:

- **KnowledgeError**: Specialized error type for knowledge operations
- **VectorStorageError**: Specialized error type for vector storage operations
- **EmbeddingError**: Specialized error type for embedding operations
- **PublishError**: Specialized error type for publishing operations
- **ValidationError**: Specialized error type for validation operations

## Best Practices

### Knowledge Organization

- **Use Consistent Topics**: Organize knowledge with consistent topic hierarchies
- **Use Descriptive Tags**: Tag knowledge with descriptive tags
- **Include Metadata**: Add relevant metadata to knowledge items
- **Version Knowledge**: Update knowledge items when they change
- **Validate Knowledge**: Validate knowledge before publishing

### Knowledge Retrieval

- **Use Similarity Search**: Find relevant knowledge with similarity search
- **Filter Results**: Filter search results by metadata
- **Combine Approaches**: Use both search and filtering
- **Cache Frequent Queries**: Cache frequently accessed knowledge
- **Handle Offline Access**: Enable operation without connectivity

### Knowledge Subscription

- **Use Specific Filters**: Subscribe to specific knowledge
- **Handle Notifications**: Process knowledge notifications
- **Manage Subscriptions**: Unsubscribe when no longer needed
- **Handle Errors**: Handle subscription errors
- **Limit Subscriptions**: Avoid subscribing to too much knowledge

## Mobile Considerations

When using the Knowledge Repository on mobile devices, consider the following:

- **Memory Usage**: Minimize memory usage by limiting vector dimensions
- **Network Usage**: Minimize network usage by batching operations
- **Storage Usage**: Minimize storage usage by compressing knowledge
- **Battery Usage**: Minimize battery usage by optimizing operations
- **Offline Access**: Enable operation without connectivity
