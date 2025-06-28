"""
Knowledge Repository component for the FlipSync application.

This module provides the knowledge repository component for FlipSync, which enables
knowledge storage, retrieval, and sharing between agents. It provides vector-based
knowledge storage, publish/subscribe knowledge sharing patterns, and mobile-optimized
knowledge access.

The knowledge repository is designed to be:
- Mobile-optimized: Efficient operation on mobile devices
- Vision-aligned: Supporting all core vision elements
- Robust: Comprehensive error handling and recovery
- Scalable: Capable of handling large knowledge repositories
"""

from fs_agt_clean.core.coordination.knowledge_repository.embedding_provider import (
    EmbeddingError,
    EmbeddingProvider,
    SimpleEmbeddingProvider,
)
from fs_agt_clean.core.coordination.knowledge_repository.in_memory_knowledge_repository import (
    InMemoryKnowledgeRepository,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_cache import (
    CacheStrategy,
    KnowledgeCache,
    LRUCache,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_filter import (
    AndFilter,
    CompositeFilter,
    KnowledgeFilter,
    NotFilter,
    OrFilter,
    SourceFilter,
    StatusFilter,
    TagFilter,
    TopicFilter,
    TypeFilter,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_publisher import (
    KnowledgePublisher,
    PublishError,
)

# Re-export core components
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_repository import (
    KnowledgeError,
    KnowledgeItem,
    KnowledgeRepository,
    KnowledgeStatus,
    KnowledgeType,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_retriever import (
    KnowledgeRetriever,
    MetadataFilter,
    QueryResult,
    SimilaritySearch,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_subscriber import (
    CustomFilter,
    KnowledgeSubscriber,
    SubscriptionFilter,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_validator import (
    KnowledgeValidator,
    SchemaValidator,
    ValidationError,
)
from fs_agt_clean.core.coordination.knowledge_repository.vector_storage import (
    InMemoryVectorStorage,
    VectorStorage,
    VectorStorageError,
)
