# Knowledge Repository Sequence Diagrams

This document contains sequence diagrams for common knowledge repository flows in the FlipSync application.

## Knowledge Publication Flow

```mermaid
sequenceDiagram
    participant Agent
    participant KnowledgeRepository
    participant KnowledgeValidator
    participant EmbeddingProvider
    participant VectorStorage
    participant KnowledgeCache
    participant EventBus

    Agent->>KnowledgeRepository: publish_knowledge(type, topic, content)
    KnowledgeRepository->>KnowledgeValidator: validate(knowledge)
    KnowledgeValidator-->>KnowledgeRepository: validation result
    KnowledgeRepository->>EmbeddingProvider: get_embedding(content)
    EmbeddingProvider-->>KnowledgeRepository: vector embedding
    KnowledgeRepository->>VectorStorage: add_vector(item_id, vector, metadata)
    VectorStorage-->>KnowledgeRepository: storage result
    KnowledgeRepository->>KnowledgeCache: add(knowledge)
    KnowledgeCache-->>KnowledgeRepository: cache result
    KnowledgeRepository->>EventBus: publish knowledge_added event
    EventBus-->>Agent: notify of publication
    KnowledgeRepository-->>Agent: knowledge_id
```

## Knowledge Retrieval Flow

```mermaid
sequenceDiagram
    participant Agent
    participant KnowledgeRepository
    participant KnowledgeCache
    participant VectorStorage
    participant EventBus

    Agent->>KnowledgeRepository: get_knowledge(knowledge_id)
    KnowledgeRepository->>KnowledgeCache: get(knowledge_id)
    KnowledgeCache-->>KnowledgeRepository: cached knowledge (if available)
    
    alt Knowledge not in cache
        KnowledgeRepository->>VectorStorage: get_vector(knowledge_id)
        VectorStorage-->>KnowledgeRepository: vector and metadata
        KnowledgeRepository->>KnowledgeCache: add(knowledge)
        KnowledgeCache-->>KnowledgeRepository: cache result
    end
    
    KnowledgeRepository-->>Agent: knowledge item
```

## Knowledge Search Flow

```mermaid
sequenceDiagram
    participant Agent
    participant KnowledgeRepository
    participant EmbeddingProvider
    participant VectorStorage
    participant EventBus

    Agent->>KnowledgeRepository: search_knowledge(query, limit)
    KnowledgeRepository->>EmbeddingProvider: get_embedding(query)
    EmbeddingProvider-->>KnowledgeRepository: query vector
    KnowledgeRepository->>VectorStorage: search_by_vector(query_vector, limit)
    VectorStorage-->>KnowledgeRepository: similar vectors
    KnowledgeRepository->>KnowledgeRepository: get knowledge items
    KnowledgeRepository-->>Agent: search results
```

## Knowledge Subscription Flow

```mermaid
sequenceDiagram
    participant Agent
    participant KnowledgeRepository
    participant EventBus
    participant OtherAgent

    Agent->>KnowledgeRepository: subscribe(filter, handler)
    KnowledgeRepository-->>Agent: subscription_id
    
    OtherAgent->>KnowledgeRepository: publish_knowledge(type, topic, content)
    KnowledgeRepository->>EventBus: publish knowledge_added event
    EventBus-->>KnowledgeRepository: notify of new knowledge
    KnowledgeRepository->>KnowledgeRepository: check filter match
    KnowledgeRepository->>Agent: handler(knowledge)
```

## Knowledge Update Flow

```mermaid
sequenceDiagram
    participant Agent
    participant KnowledgeRepository
    participant KnowledgeValidator
    participant EmbeddingProvider
    participant VectorStorage
    participant KnowledgeCache
    participant EventBus

    Agent->>KnowledgeRepository: update_knowledge(knowledge_id, content)
    KnowledgeRepository->>KnowledgeRepository: get_knowledge(knowledge_id)
    KnowledgeRepository->>KnowledgeRepository: create updated version
    KnowledgeRepository->>KnowledgeValidator: validate(updated_knowledge)
    KnowledgeValidator-->>KnowledgeRepository: validation result
    KnowledgeRepository->>EmbeddingProvider: get_embedding(content)
    EmbeddingProvider-->>KnowledgeRepository: vector embedding
    KnowledgeRepository->>VectorStorage: add_vector(new_id, vector, metadata)
    VectorStorage-->>KnowledgeRepository: storage result
    KnowledgeRepository->>KnowledgeCache: add(updated_knowledge)
    KnowledgeCache-->>KnowledgeRepository: cache result
    KnowledgeRepository->>EventBus: publish knowledge_updated event
    EventBus-->>Agent: notify of update
    KnowledgeRepository-->>Agent: updated_knowledge_id
```

## Mobile-Optimized Knowledge Synchronization Flow

```mermaid
sequenceDiagram
    participant MobileAgent
    participant KnowledgeRepository
    participant KnowledgeCache
    participant NetworkMonitor
    participant EventBus

    MobileAgent->>NetworkMonitor: get_network_status()
    NetworkMonitor-->>MobileAgent: network status
    
    alt Good Network Conditions
        MobileAgent->>KnowledgeRepository: get_knowledge_updates(last_sync_time)
        KnowledgeRepository-->>MobileAgent: knowledge updates
        MobileAgent->>KnowledgeCache: add_batch(updates)
        KnowledgeCache-->>MobileAgent: cache result
    else Limited Network Conditions
        MobileAgent->>KnowledgeRepository: get_critical_updates(last_sync_time)
        KnowledgeRepository-->>MobileAgent: critical updates
        MobileAgent->>KnowledgeCache: add_batch(critical_updates)
        KnowledgeCache-->>MobileAgent: cache result
    else Offline
        MobileAgent->>KnowledgeCache: get_cached_knowledge()
        KnowledgeCache-->>MobileAgent: cached knowledge
    end
```

## Knowledge Query Flow

```mermaid
sequenceDiagram
    participant Agent
    participant KnowledgeRepository
    participant EventBus
    participant KnowledgeProviderAgent

    Agent->>EventBus: publish knowledge_query event
    EventBus-->>KnowledgeRepository: receive knowledge_query event
    KnowledgeRepository->>KnowledgeRepository: process query
    KnowledgeRepository->>EventBus: publish knowledge_query_response event
    EventBus-->>Agent: receive knowledge_query_response event
    
    alt Knowledge Not Found
        EventBus-->>KnowledgeProviderAgent: receive knowledge_query event
        KnowledgeProviderAgent->>KnowledgeProviderAgent: generate knowledge
        KnowledgeProviderAgent->>KnowledgeRepository: publish_knowledge(type, topic, content)
        KnowledgeRepository->>EventBus: publish knowledge_added event
        EventBus-->>Agent: receive knowledge_added event
    end
```

## Market Analysis Scenario

```mermaid
sequenceDiagram
    participant MarketAgent
    participant KnowledgeRepository
    participant AnalysisAgent
    participant ExecutiveAgent
    participant EventBus

    MarketAgent->>KnowledgeRepository: publish_knowledge(FACT, "market/crypto/bitcoin", data)
    KnowledgeRepository->>EventBus: publish knowledge_added event
    EventBus-->>AnalysisAgent: receive knowledge_added event
    AnalysisAgent->>KnowledgeRepository: get_knowledge(knowledge_id)
    KnowledgeRepository-->>AnalysisAgent: market data
    AnalysisAgent->>AnalysisAgent: analyze market data
    AnalysisAgent->>KnowledgeRepository: publish_knowledge(RELATION, "market/crypto/bitcoin/analysis", analysis)
    KnowledgeRepository->>EventBus: publish knowledge_added event
    EventBus-->>ExecutiveAgent: receive knowledge_added event
    ExecutiveAgent->>KnowledgeRepository: search_knowledge("bitcoin analysis")
    KnowledgeRepository-->>ExecutiveAgent: analysis results
    ExecutiveAgent->>ExecutiveAgent: make investment decision
```

## Mobile-Optimized Knowledge Access Scenario

```mermaid
sequenceDiagram
    participant MobileAgent
    participant KnowledgeRepository
    participant KnowledgeCache
    participant NetworkMonitor
    participant BatteryMonitor
    participant EventBus

    MobileAgent->>NetworkMonitor: get_network_status()
    NetworkMonitor-->>MobileAgent: limited connectivity
    MobileAgent->>BatteryMonitor: get_battery_level()
    BatteryMonitor-->>MobileAgent: low battery
    
    MobileAgent->>KnowledgeCache: get_cached_knowledge("market/crypto/bitcoin")
    KnowledgeCache-->>MobileAgent: cached knowledge
    
    MobileAgent->>KnowledgeRepository: get_critical_updates("market/crypto/bitcoin")
    KnowledgeRepository->>KnowledgeRepository: filter critical updates
    KnowledgeRepository-->>MobileAgent: compressed critical updates
    
    MobileAgent->>KnowledgeCache: update_cached_knowledge(updates)
    KnowledgeCache-->>MobileAgent: cache update result
    
    MobileAgent->>MobileAgent: process knowledge offline
```
