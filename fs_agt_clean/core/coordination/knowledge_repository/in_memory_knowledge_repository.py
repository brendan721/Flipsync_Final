"""
In-memory implementation of the Knowledge Repository.

This module provides an in-memory implementation of the Knowledge Repository
interface, suitable for testing and small-scale deployments.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from fs_agt_clean.core.coordination.event_system import (
    Event,
    EventNameFilter,
    EventPriority,
    EventType,
    create_publisher,
    create_subscriber,
)
from fs_agt_clean.core.coordination.knowledge_repository.embedding_provider import (
    EmbeddingError,
    EmbeddingProvider,
    SimpleEmbeddingProvider,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_cache import (
    CacheStrategy,
    KnowledgeCache,
    LRUCache,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_publisher import (
    KnowledgePublisher,
    PublishError,
)
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
    KnowledgeHandler,
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
from fs_agt_clean.core.monitoring import get_logger


class InMemoryKnowledgeRepository(
    KnowledgeRepository, KnowledgePublisher, KnowledgeSubscriber, KnowledgeRetriever
):
    """
    In-memory implementation of the Knowledge Repository.

    This implementation stores knowledge items in memory, providing
    efficient access and vector-based search capabilities.
    """

    def __init__(
        self,
        repository_id: str,
        vector_storage: Optional[VectorStorage] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        validator: Optional[KnowledgeValidator] = None,
        cache: Optional[KnowledgeCache] = None,
    ):
        """
        Initialize an in-memory knowledge repository.

        Args:
            repository_id: Unique identifier for this repository
            vector_storage: Vector storage for knowledge items
            embedding_provider: Provider for generating embeddings
            validator: Validator for knowledge items
            cache: Cache for knowledge items
        """
        self.repository_id = repository_id
        self.logger = get_logger(f"knowledge_repository.{repository_id}")

        # Create publisher and subscriber for event-based communication
        self.publisher = create_publisher(
            source_id=f"knowledge_repository.{repository_id}"
        )
        self.subscriber = create_subscriber(
            subscriber_id=f"knowledge_repository.{repository_id}"
        )

        # Create or use provided components
        self.vector_storage = vector_storage or InMemoryVectorStorage(
            storage_id=f"{repository_id}.storage"
        )
        self.embedding_provider = embedding_provider or SimpleEmbeddingProvider(
            provider_id=f"{repository_id}.embeddings"
        )
        self.validator = validator or SchemaValidator(
            validator_id=f"{repository_id}.validator"
        )
        self.cache = cache or LRUCache(cache_id=f"{repository_id}.cache")

        # Initialize storage
        self.knowledge_items: Dict[str, KnowledgeItem] = {}
        self.version_history: Dict[str, List[str]] = {}

        # Initialize indexes
        self.topic_index: Dict[str, Set[str]] = {}
        self.type_index: Dict[KnowledgeType, Set[str]] = {}
        self.source_index: Dict[str, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        self.status_index: Dict[KnowledgeStatus, Set[str]] = {}

        # Initialize subscriptions
        self.subscriptions: Dict[str, Tuple[SubscriptionFilter, KnowledgeHandler]] = {}
        self.subscription_counter = 0

        # Initialize event subscription IDs
        self.event_subscription_ids: List[str] = []

    async def start(self) -> None:
        """
        Start the knowledge repository.
        """
        # Subscribe to events
        await self._subscribe_to_events()

        self.logger.info(f"Knowledge repository started: {self.repository_id}")

    async def stop(self) -> None:
        """
        Stop the knowledge repository.
        """
        # Unsubscribe from events
        for subscription_id in self.event_subscription_ids:
            await self.subscriber.unsubscribe(subscription_id)

        self.event_subscription_ids = []

        self.logger.info(f"Knowledge repository stopped: {self.repository_id}")

    async def add_knowledge(self, knowledge: KnowledgeItem) -> str:
        """
        Add a knowledge item to the repository.

        Args:
            knowledge: The knowledge item to add

        Returns:
            ID of the added knowledge item

        Raises:
            KnowledgeError: If the knowledge item cannot be added
        """
        try:
            # Check if the knowledge item already exists
            if knowledge.knowledge_id in self.knowledge_items:
                raise KnowledgeError(
                    f"Knowledge item already exists: {knowledge.knowledge_id}",
                    knowledge_id=knowledge.knowledge_id,
                )

            # Validate the knowledge item
            try:
                await self.validator.validate(knowledge)
            except ValidationError as e:
                raise KnowledgeError(
                    f"Knowledge item validation failed: {str(e)}",
                    knowledge_id=knowledge.knowledge_id,
                    cause=e,
                )

            # Generate an embedding if not provided
            if knowledge.vector is None:
                try:
                    knowledge.vector = await self.embedding_provider.get_embedding(
                        knowledge.content
                    )
                except EmbeddingError as e:
                    raise KnowledgeError(
                        f"Failed to generate embedding: {str(e)}",
                        knowledge_id=knowledge.knowledge_id,
                        cause=e,
                    )

            # Add the vector to the vector storage
            try:
                await self.vector_storage.add_vector(
                    item_id=knowledge.knowledge_id,
                    vector=knowledge.vector,
                    metadata={
                        "topic": knowledge.topic,
                        "type": knowledge.knowledge_type.name,
                        "source_id": knowledge.source_id,
                        "tags": list(knowledge.tags),
                    },
                )
            except VectorStorageError as e:
                raise KnowledgeError(
                    f"Failed to add vector: {str(e)}",
                    knowledge_id=knowledge.knowledge_id,
                    cause=e,
                )

            # Store the knowledge item
            self.knowledge_items[knowledge.knowledge_id] = knowledge

            # Update indexes
            self._update_indexes(knowledge)

            # Add to version history
            if knowledge.previous_version_id:
                if knowledge.previous_version_id not in self.version_history:
                    self.version_history[knowledge.previous_version_id] = []
                self.version_history[knowledge.previous_version_id].append(
                    knowledge.knowledge_id
                )

            # Add to cache
            await self.cache.add(knowledge)

            # Notify subscribers
            await self._notify_subscribers(knowledge)

            # Publish event
            await self._publish_knowledge_added_event(knowledge)

            self.logger.info(
                f"Added knowledge item: {knowledge.knowledge_id} ({knowledge.topic})"
            )

            return knowledge.knowledge_id
        except KnowledgeError:
            # Re-raise knowledge errors
            raise
        except Exception as e:
            error_msg = f"Failed to add knowledge item: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(
                error_msg, knowledge_id=knowledge.knowledge_id, cause=e
            )

    async def update_knowledge(self, knowledge: KnowledgeItem) -> str:
        """
        Update a knowledge item in the repository.

        Args:
            knowledge: The updated knowledge item

        Returns:
            ID of the updated knowledge item

        Raises:
            KnowledgeError: If the knowledge item cannot be updated
        """
        try:
            # Check if the knowledge item exists
            if knowledge.previous_version_id not in self.knowledge_items:
                raise KnowledgeError(
                    f"Knowledge item not found: {knowledge.previous_version_id}",
                    knowledge_id=knowledge.previous_version_id,
                )

            # Validate the knowledge item
            try:
                await self.validator.validate(knowledge)
            except ValidationError as e:
                raise KnowledgeError(
                    f"Knowledge item validation failed: {str(e)}",
                    knowledge_id=knowledge.knowledge_id,
                    cause=e,
                )

            # Generate an embedding if not provided
            if knowledge.vector is None:
                try:
                    knowledge.vector = await self.embedding_provider.get_embedding(
                        knowledge.content
                    )
                except EmbeddingError as e:
                    raise KnowledgeError(
                        f"Failed to generate embedding: {str(e)}",
                        knowledge_id=knowledge.knowledge_id,
                        cause=e,
                    )

            # Add the vector to the vector storage
            try:
                await self.vector_storage.add_vector(
                    item_id=knowledge.knowledge_id,
                    vector=knowledge.vector,
                    metadata={
                        "topic": knowledge.topic,
                        "type": knowledge.knowledge_type.name,
                        "source_id": knowledge.source_id,
                        "tags": list(knowledge.tags),
                    },
                )
            except VectorStorageError as e:
                raise KnowledgeError(
                    f"Failed to add vector: {str(e)}",
                    knowledge_id=knowledge.knowledge_id,
                    cause=e,
                )

            # Store the knowledge item
            self.knowledge_items[knowledge.knowledge_id] = knowledge

            # Update indexes
            self._update_indexes(knowledge)

            # Add to version history
            if knowledge.previous_version_id not in self.version_history:
                self.version_history[knowledge.previous_version_id] = []
            self.version_history[knowledge.previous_version_id].append(
                knowledge.knowledge_id
            )

            # Add to cache
            await self.cache.add(knowledge)

            # Notify subscribers
            await self._notify_subscribers(knowledge)

            # Publish event
            await self._publish_knowledge_updated_event(knowledge)

            self.logger.info(
                f"Updated knowledge item: {knowledge.knowledge_id} ({knowledge.topic})"
            )

            return knowledge.knowledge_id
        except KnowledgeError:
            # Re-raise knowledge errors
            raise
        except Exception as e:
            error_msg = f"Failed to update knowledge item: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(
                error_msg, knowledge_id=knowledge.knowledge_id, cause=e
            )

    async def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """
        Get a knowledge item by ID.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            The knowledge item, or None if not found

        Raises:
            KnowledgeError: If the knowledge item cannot be retrieved
        """
        try:
            # Try to get from cache first
            knowledge = await self.cache.get(knowledge_id)
            if knowledge:
                return knowledge

            # Get from storage
            knowledge = self.knowledge_items.get(knowledge_id)

            # If found, add to cache
            if knowledge:
                await self.cache.add(knowledge)

            return knowledge
        except Exception as e:
            error_msg = f"Failed to get knowledge item {knowledge_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, knowledge_id=knowledge_id, cause=e)

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge item from the repository.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            True if the knowledge item was deleted

        Raises:
            KnowledgeError: If the knowledge item cannot be deleted
        """
        try:
            # Check if the knowledge item exists
            knowledge = self.knowledge_items.get(knowledge_id)
            if not knowledge:
                return False

            # Remove from storage
            del self.knowledge_items[knowledge_id]

            # Remove from vector storage
            try:
                await self.vector_storage.delete_vector(knowledge_id)
            except VectorStorageError as e:
                self.logger.warning(
                    f"Failed to delete vector for {knowledge_id}: {str(e)}"
                )

            # Remove from indexes
            self._remove_from_indexes(knowledge)

            # Remove from cache
            await self.cache.remove(knowledge_id)

            # Publish event
            await self._publish_knowledge_deleted_event(knowledge)

            self.logger.info(f"Deleted knowledge item: {knowledge_id}")

            return True
        except Exception as e:
            error_msg = f"Failed to delete knowledge item {knowledge_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, knowledge_id=knowledge_id, cause=e)

    async def get_knowledge_by_topic(self, topic: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by topic.

        Args:
            topic: Topic to search for

        Returns:
            List of knowledge items with the specified topic

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Try to get from cache first
            cached_items = await self.cache.get_by_topic(topic)
            if cached_items:
                return cached_items

            # Get from index
            knowledge_ids = self.topic_index.get(topic, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = f"Failed to get knowledge items by topic {topic}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    async def get_knowledge_by_type(
        self, knowledge_type: KnowledgeType
    ) -> List[KnowledgeItem]:
        """
        Get knowledge items by type.

        Args:
            knowledge_type: Type to search for

        Returns:
            List of knowledge items with the specified type

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Try to get from cache first
            cached_items = await self.cache.get_by_type(knowledge_type)
            if cached_items:
                return cached_items

            # Get from index
            knowledge_ids = self.type_index.get(knowledge_type, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = (
                f"Failed to get knowledge items by type {knowledge_type.name}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    async def get_knowledge_by_source(self, source_id: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by source.

        Args:
            source_id: Source ID to search for

        Returns:
            List of knowledge items from the specified source

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Get from index
            knowledge_ids = self.source_index.get(source_id, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = f"Failed to get knowledge items by source {source_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    async def get_knowledge_by_tag(self, tag: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of knowledge items with the specified tag

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Try to get from cache first
            cached_items = await self.cache.get_by_tag(tag)
            if cached_items:
                return cached_items

            # Get from index
            knowledge_ids = self.tag_index.get(tag, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = f"Failed to get knowledge items by tag {tag}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    async def get_knowledge_by_status(
        self, status: KnowledgeStatus
    ) -> List[KnowledgeItem]:
        """
        Get knowledge items by status.

        Args:
            status: Status to search for

        Returns:
            List of knowledge items with the specified status

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Try to get from cache first
            cached_items = await self.cache.get_by_status(status)
            if cached_items:
                return cached_items

            # Get from index
            knowledge_ids = self.status_index.get(status, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = (
                f"Failed to get knowledge items by status {status.name}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    async def search_knowledge(
        self, query: str, limit: int = 10
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        Search for knowledge items by similarity to a query.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of (knowledge item, similarity score) tuples

        Raises:
            KnowledgeError: If the search cannot be performed
        """
        try:
            # Generate an embedding for the query
            try:
                query_vector = await self.embedding_provider.get_embedding(query)
            except EmbeddingError as e:
                raise KnowledgeError(
                    f"Failed to generate embedding for query: {str(e)}", cause=e
                )

            # Search by vector
            try:
                results = await self.vector_storage.search_by_vector(
                    query_vector, limit
                )
            except VectorStorageError as e:
                raise KnowledgeError(f"Failed to search by vector: {str(e)}", cause=e)

            # Get knowledge items
            items = []
            for knowledge_id, score in results:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append((knowledge, score))

            return items
        except KnowledgeError:
            # Re-raise knowledge errors
            raise
        except Exception as e:
            error_msg = f"Failed to search knowledge: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    async def similar_knowledge(
        self, knowledge_id: str, limit: int = 10
    ) -> List[Tuple[KnowledgeItem, float]]:
        """
        Find knowledge items similar to a given knowledge item.

        Args:
            knowledge_id: ID of the knowledge item
            limit: Maximum number of results

        Returns:
            List of (knowledge item, similarity score) tuples

        Raises:
            KnowledgeError: If the similarity search cannot be performed
        """
        try:
            # Check if the knowledge item exists
            knowledge = await self.get_knowledge(knowledge_id)
            if not knowledge:
                raise KnowledgeError(
                    f"Knowledge item not found: {knowledge_id}",
                    knowledge_id=knowledge_id,
                )

            # Search by vector
            try:
                results = await self.vector_storage.search_by_id(knowledge_id, limit)
            except VectorStorageError as e:
                raise KnowledgeError(
                    f"Failed to search by ID: {str(e)}",
                    knowledge_id=knowledge_id,
                    cause=e,
                )

            # Get knowledge items
            items = []
            for similar_id, score in results:
                similar_knowledge = self.knowledge_items.get(similar_id)
                if similar_knowledge:
                    items.append((similar_knowledge, score))

            return items
        except KnowledgeError:
            # Re-raise knowledge errors
            raise
        except Exception as e:
            error_msg = f"Failed to find similar knowledge for {knowledge_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, knowledge_id=knowledge_id, cause=e)

    async def get_knowledge_version_history(
        self, knowledge_id: str
    ) -> List[KnowledgeItem]:
        """
        Get the version history of a knowledge item.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            List of knowledge items representing the version history

        Raises:
            KnowledgeError: If the version history cannot be retrieved
        """
        try:
            # Check if the knowledge item exists
            knowledge = await self.get_knowledge(knowledge_id)
            if not knowledge:
                raise KnowledgeError(
                    f"Knowledge item not found: {knowledge_id}",
                    knowledge_id=knowledge_id,
                )

            # Get version history
            history = [knowledge]

            # Get previous versions
            current = knowledge
            while current.previous_version_id:
                previous = await self.get_knowledge(current.previous_version_id)
                if previous:
                    history.append(previous)
                    current = previous
                else:
                    break

            # Get next versions
            next_versions = self.version_history.get(knowledge_id, [])
            for next_id in next_versions:
                next_knowledge = await self.get_knowledge(next_id)
                if next_knowledge:
                    history.append(next_knowledge)

            # Sort by version
            history.sort(key=lambda k: k.version)

            return history
        except KnowledgeError:
            # Re-raise knowledge errors
            raise
        except Exception as e:
            error_msg = f"Failed to get version history for {knowledge_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, knowledge_id=knowledge_id, cause=e)

    async def get_all_knowledge(self) -> List[KnowledgeItem]:
        """
        Get all knowledge items in the repository.

        Returns:
            List of all knowledge items

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Return a copy of all items
            return list(self.knowledge_items.values())
        except Exception as e:
            error_msg = f"Failed to get all knowledge items: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    # KnowledgePublisher methods

    async def publish_knowledge(
        self,
        knowledge_type: KnowledgeType,
        topic: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
        source_id: Optional[str] = None,
        access_control: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """
        Publish a knowledge item to the repository.

        Args:
            knowledge_type: Type of knowledge
            topic: Topic or category of the knowledge
            content: Content of the knowledge item
            metadata: Additional metadata about the knowledge
            source_id: ID of the source that created the knowledge
            access_control: Access control information
            tags: Tags for categorizing the knowledge

        Returns:
            ID of the published knowledge item

        Raises:
            PublishError: If the knowledge item cannot be published
        """
        try:
            # Create a knowledge item
            knowledge = KnowledgeItem.create(
                knowledge_type=knowledge_type,
                topic=topic,
                content=content,
                metadata=metadata,
                source_id=source_id,
                access_control=access_control,
                tags=tags,
            )

            # Add the knowledge item to the repository
            try:
                knowledge_id = await self.add_knowledge(knowledge)
                return knowledge_id
            except KnowledgeError as e:
                raise PublishError(
                    f"Failed to add knowledge item: {str(e)}",
                    knowledge_id=knowledge.knowledge_id,
                    cause=e,
                )
        except PublishError:
            # Re-raise publish errors
            raise
        except Exception as e:
            error_msg = f"Failed to publish knowledge item: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise PublishError(error_msg, cause=e)

    async def update_knowledge_by_id(
        self,
        knowledge_id: str,
        content: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: Optional[KnowledgeStatus] = None,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """
        Update a knowledge item in the repository by ID.

        Args:
            knowledge_id: ID of the knowledge item
            content: New content
            metadata: New or updated metadata
            status: New status
            tags: New or updated tags

        Returns:
            ID of the updated knowledge item

        Raises:
            PublishError: If the knowledge item cannot be updated
        """
        try:
            # Get the knowledge item
            knowledge = await self.get_knowledge(knowledge_id)
            if not knowledge:
                raise PublishError(
                    f"Knowledge item not found: {knowledge_id}",
                    knowledge_id=knowledge_id,
                )

            # Create an updated version
            updated = knowledge.update(
                content=content, metadata=metadata, status=status, tags=tags
            )

            # Add the updated knowledge item to the repository
            try:
                updated_id = await self.add_knowledge(updated)
                return updated_id
            except KnowledgeError as e:
                raise PublishError(
                    f"Failed to update knowledge item: {str(e)}",
                    knowledge_id=updated.knowledge_id,
                    cause=e,
                )
        except PublishError:
            # Re-raise publish errors
            raise
        except Exception as e:
            error_msg = f"Failed to update knowledge item {knowledge_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise PublishError(error_msg, knowledge_id=knowledge_id, cause=e)

    async def delete_knowledge_by_id(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge item from the repository by ID.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            True if the knowledge item was deleted

        Raises:
            PublishError: If the knowledge item cannot be deleted
        """
        try:
            # Delete the knowledge item
            try:
                # Check if the knowledge item exists
                knowledge = self.knowledge_items.get(knowledge_id)
                if not knowledge:
                    return False

                # Remove from storage
                del self.knowledge_items[knowledge_id]

                # Remove from vector storage
                try:
                    await self.vector_storage.delete_vector(knowledge_id)
                except VectorStorageError as e:
                    self.logger.warning(
                        f"Failed to delete vector for {knowledge_id}: {str(e)}"
                    )

                # Remove from indexes
                self._remove_from_indexes(knowledge)

                # Remove from cache
                await self.cache.remove(knowledge_id)

                # Publish event
                await self._publish_knowledge_deleted_event(knowledge)

                self.logger.info(f"Deleted knowledge item: {knowledge_id}")

                return True
            except KnowledgeError as e:
                raise PublishError(
                    f"Failed to delete knowledge item: {str(e)}",
                    knowledge_id=knowledge_id,
                    cause=e,
                )
        except PublishError:
            # Re-raise publish errors
            raise
        except Exception as e:
            error_msg = f"Failed to delete knowledge item {knowledge_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise PublishError(error_msg, knowledge_id=knowledge_id, cause=e)

    async def publish_batch(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        Publish multiple knowledge items to the repository.

        Args:
            items: List of knowledge items to publish

        Returns:
            List of IDs of the published knowledge items

        Raises:
            PublishError: If the knowledge items cannot be published
        """
        try:
            # Publish each item
            knowledge_ids = []
            for item in items:
                try:
                    knowledge_id = await self.publish_knowledge(
                        knowledge_type=item.get("knowledge_type"),
                        topic=item.get("topic"),
                        content=item.get("content"),
                        metadata=item.get("metadata"),
                        source_id=item.get("source_id"),
                        access_control=item.get("access_control"),
                        tags=item.get("tags"),
                    )
                    knowledge_ids.append(knowledge_id)
                except PublishError as e:
                    self.logger.warning(f"Failed to publish item: {str(e)}")
                    knowledge_ids.append(None)

            return knowledge_ids
        except Exception as e:
            error_msg = f"Failed to publish batch: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise PublishError(error_msg, cause=e)

    # KnowledgeSubscriber methods

    async def subscribe(
        self, filter: Optional[SubscriptionFilter], handler: KnowledgeHandler
    ) -> str:
        """
        Subscribe to knowledge updates.

        Args:
            filter: Filter for knowledge items
            handler: Handler for knowledge notifications

        Returns:
            Subscription ID
        """
        # Generate a subscription ID
        subscription_id = f"sub_{self.subscription_counter}"
        self.subscription_counter += 1

        # Store the subscription
        self.subscriptions[subscription_id] = (filter, handler)

        self.logger.debug(f"Added subscription: {subscription_id}")

        return subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from knowledge updates.

        Args:
            subscription_id: ID of the subscription

        Returns:
            True if the subscription was removed
        """
        # Remove the subscription
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            self.logger.debug(f"Removed subscription: {subscription_id}")
            return True

        return False

    async def get_subscriptions(self) -> List[Dict[str, Any]]:
        """
        Get all subscriptions for this subscriber.

        Returns:
            List of subscription information
        """
        # Return subscription information
        return [
            {
                "subscription_id": subscription_id,
                "filter": filter.__class__.__name__ if filter else None,
            }
            for subscription_id, (filter, _) in self.subscriptions.items()
        ]

    # KnowledgeRetriever methods

    async def get_knowledge(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """
        Get a knowledge item by ID.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            The knowledge item, or None if not found
        """
        try:
            # Try to get from cache first
            knowledge = await self.cache.get(knowledge_id)
            if knowledge:
                return knowledge

            # Get from storage
            knowledge = self.knowledge_items.get(knowledge_id)

            # If found, add to cache
            if knowledge:
                await self.cache.add(knowledge)

            return knowledge
        except Exception as e:
            error_msg = f"Failed to get knowledge item {knowledge_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return None

    async def get_knowledge_by_topic(self, topic: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by topic.

        Args:
            topic: Topic to search for

        Returns:
            List of knowledge items with the specified topic
        """
        try:
            # Try to get from cache first
            cached_items = await self.cache.get_by_topic(topic)
            if cached_items:
                return cached_items

            # Get from index
            knowledge_ids = self.topic_index.get(topic, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = f"Failed to get knowledge items by topic {topic}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return []

    async def get_knowledge_by_type(
        self, knowledge_type: KnowledgeType
    ) -> List[KnowledgeItem]:
        """
        Get knowledge items by type.

        Args:
            knowledge_type: Type to search for

        Returns:
            List of knowledge items with the specified type
        """
        try:
            # Try to get from cache first
            cached_items = await self.cache.get_by_type(knowledge_type)
            if cached_items:
                return cached_items

            # Get from index
            knowledge_ids = self.type_index.get(knowledge_type, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = (
                f"Failed to get knowledge items by type {knowledge_type.name}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            return []

    async def get_knowledge_by_source(self, source_id: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by source.

        Args:
            source_id: Source ID to search for

        Returns:
            List of knowledge items from the specified source
        """
        try:
            # Get from index
            knowledge_ids = self.source_index.get(source_id, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = f"Failed to get knowledge items by source {source_id}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return []

    async def get_knowledge_by_tag(self, tag: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by tag.

        Args:
            tag: Tag to search for

        Returns:
            List of knowledge items with the specified tag
        """
        try:
            # Try to get from cache first
            cached_items = await self.cache.get_by_tag(tag)
            if cached_items:
                return cached_items

            # Get from index
            knowledge_ids = self.tag_index.get(tag, set())

            # Get knowledge items
            items = []
            for knowledge_id in knowledge_ids:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    items.append(knowledge)
                    # Add to cache
                    await self.cache.add(knowledge)

            return items
        except Exception as e:
            error_msg = f"Failed to get knowledge items by tag {tag}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return []

    async def search_knowledge(self, query: str, limit: int = 10) -> List[QueryResult]:
        """
        Search for knowledge items by similarity to a query.

        Args:
            query: Query string
            limit: Maximum number of results

        Returns:
            List of query results
        """
        try:
            # Generate an embedding for the query
            try:
                query_vector = await self.embedding_provider.get_embedding(query)
            except EmbeddingError as e:
                self.logger.error(f"Failed to generate embedding for query: {str(e)}")
                return []

            # Search by vector
            try:
                results = await self.vector_storage.search_by_vector(
                    query_vector, limit
                )
            except VectorStorageError as e:
                self.logger.error(f"Failed to search by vector: {str(e)}")
                return []

            # Get knowledge items
            query_results = []
            for knowledge_id, score in results:
                knowledge = self.knowledge_items.get(knowledge_id)
                if knowledge:
                    query_results.append(QueryResult(knowledge=knowledge, score=score))

            return query_results
        except Exception as e:
            self.logger.error(f"Failed to search knowledge: {str(e)}")
            return []

    async def filter_knowledge(
        self, filter: MetadataFilter, limit: Optional[int] = None
    ) -> List[KnowledgeItem]:
        """
        Filter knowledge items based on metadata.

        Args:
            filter: Metadata filter
            limit: Maximum number of results

        Returns:
            List of knowledge items matching the filter
        """
        try:
            # Get all knowledge items
            all_items = await self.get_all_knowledge()

            # Filter items
            filtered_items = [item for item in all_items if filter.matches(item)]

            # Limit results if specified
            if limit is not None:
                filtered_items = filtered_items[:limit]

            return filtered_items
        except Exception as e:
            self.logger.error(f"Failed to filter knowledge: {str(e)}")
            return []

    async def search_and_filter(
        self, query: str, filter: MetadataFilter, limit: int = 10
    ) -> List[QueryResult]:
        """
        Search for knowledge items and filter the results.

        Args:
            query: Query string
            filter: Metadata filter
            limit: Maximum number of results

        Returns:
            List of query results
        """
        try:
            # Search by similarity
            search_results = await self.search_knowledge(
                query, limit * 2
            )  # Get more results to filter

            # Filter results
            filtered_results = [
                result for result in search_results if filter.matches(result.knowledge)
            ]

            # Limit results
            return filtered_results[:limit]
        except Exception as e:
            self.logger.error(f"Failed to search and filter knowledge: {str(e)}")
            return []

    # Helper methods

    def _update_indexes(self, knowledge: KnowledgeItem) -> None:
        """
        Update indexes for a knowledge item.

        Args:
            knowledge: Knowledge item to index
        """
        # Update topic index
        topic = knowledge.topic
        if topic not in self.topic_index:
            self.topic_index[topic] = set()
        self.topic_index[topic].add(knowledge.knowledge_id)

        # Update type index
        knowledge_type = knowledge.knowledge_type
        if knowledge_type not in self.type_index:
            self.type_index[knowledge_type] = set()
        self.type_index[knowledge_type].add(knowledge.knowledge_id)

        # Update source index
        if knowledge.source_id:
            source_id = knowledge.source_id
            if source_id not in self.source_index:
                self.source_index[source_id] = set()
            self.source_index[source_id].add(knowledge.knowledge_id)

        # Update tag index
        for tag in knowledge.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(knowledge.knowledge_id)

        # Update status index
        status = knowledge.status
        if status not in self.status_index:
            self.status_index[status] = set()
        self.status_index[status].add(knowledge.knowledge_id)

    def _remove_from_indexes(self, knowledge: KnowledgeItem) -> None:
        """
        Remove a knowledge item from indexes.

        Args:
            knowledge: Knowledge item to remove
        """
        # Remove from topic index
        topic = knowledge.topic
        if topic in self.topic_index:
            self.topic_index[topic].discard(knowledge.knowledge_id)
            if not self.topic_index[topic]:
                del self.topic_index[topic]

        # Remove from type index
        knowledge_type = knowledge.knowledge_type
        if knowledge_type in self.type_index:
            self.type_index[knowledge_type].discard(knowledge.knowledge_id)
            if not self.type_index[knowledge_type]:
                del self.type_index[knowledge_type]

        # Remove from source index
        if knowledge.source_id:
            source_id = knowledge.source_id
            if source_id in self.source_index:
                self.source_index[source_id].discard(knowledge.knowledge_id)
                if not self.source_index[source_id]:
                    del self.source_index[source_id]

        # Remove from tag index
        for tag in knowledge.tags:
            if tag in self.tag_index:
                self.tag_index[tag].discard(knowledge.knowledge_id)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]

        # Remove from status index
        status = knowledge.status
        if status in self.status_index:
            self.status_index[status].discard(knowledge.knowledge_id)
            if not self.status_index[status]:
                del self.status_index[status]

    async def _notify_subscribers(self, knowledge: KnowledgeItem) -> None:
        """
        Notify subscribers about a knowledge item.

        Args:
            knowledge: Knowledge item to notify about
        """
        # Notify subscribers
        for subscription_id, (filter, handler) in self.subscriptions.items():
            # Check if the knowledge item matches the filter
            if filter is None or filter.matches(knowledge):
                try:
                    # Call the handler
                    await handler(knowledge)
                except Exception as e:
                    self.logger.warning(
                        f"Error in subscription handler {subscription_id}: {str(e)}"
                    )

    async def _subscribe_to_events(self) -> None:
        """
        Subscribe to knowledge-related events.
        """
        # Subscribe to knowledge query events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"knowledge_query"}),
            handler=self._handle_knowledge_query,
        )
        self.event_subscription_ids.append(subscription_id)

        # Subscribe to knowledge publish events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"knowledge_publish"}),
            handler=self._handle_knowledge_publish,
        )
        self.event_subscription_ids.append(subscription_id)

        # Subscribe to knowledge update events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"knowledge_update"}),
            handler=self._handle_knowledge_update,
        )
        self.event_subscription_ids.append(subscription_id)

        # Subscribe to knowledge delete events
        subscription_id = await self.subscriber.subscribe(
            filter=EventNameFilter(event_names={"knowledge_delete"}),
            handler=self._handle_knowledge_delete,
        )
        self.event_subscription_ids.append(subscription_id)

    async def _handle_knowledge_query(self, event: Event) -> None:
        """
        Handle a knowledge query event.

        Args:
            event: Knowledge query event
        """
        try:
            # Extract query information
            query = event.data.get("query")
            query_type = event.data.get("query_type")
            limit = event.data.get("limit", 10)
            correlation_id = event.correlation_id

            if not query or not query_type:
                self.logger.warning("Received knowledge query event with missing data")
                return

            # Process the query
            results = []
            if query_type == "text":
                # Text search
                search_results = await self.search_knowledge(query, limit)
                results = [result.knowledge.to_dict() for result in search_results]
            elif query_type == "topic":
                # Topic search
                topic_results = await self.get_knowledge_by_topic(query)
                results = [item.to_dict() for item in topic_results[:limit]]
            elif query_type == "tag":
                # Tag search
                tag_results = await self.get_knowledge_by_tag(query)
                results = [item.to_dict() for item in tag_results[:limit]]
            elif query_type == "id":
                # ID lookup
                item = await self.get_knowledge(query)
                if item:
                    results = [item.to_dict()]
            else:
                self.logger.warning(f"Unknown query type: {query_type}")
                return

            # Publish response
            await self.publisher.publish_notification(
                notification_name="knowledge_query_response",
                data={
                    "query": query,
                    "query_type": query_type,
                    "results": results,
                    "result_count": len(results),
                },
                correlation_id=correlation_id,
            )
        except Exception as e:
            self.logger.error(
                f"Error handling knowledge query event: {str(e)}", exc_info=True
            )

    async def _handle_knowledge_publish(self, event: Event) -> None:
        """
        Handle a knowledge publish event.

        Args:
            event: Knowledge publish event
        """
        try:
            # Extract knowledge information
            knowledge_type_str = event.data.get("knowledge_type")
            topic = event.data.get("topic")
            content = event.data.get("content")
            metadata = event.data.get("metadata")
            source_id = event.data.get("source_id")
            access_control = event.data.get("access_control")
            tags = event.data.get("tags")
            correlation_id = event.correlation_id

            if not knowledge_type_str or not topic or content is None:
                self.logger.warning(
                    "Received knowledge publish event with missing data"
                )
                return

            # Convert knowledge type string to enum
            try:
                knowledge_type = KnowledgeType[knowledge_type_str]
            except (KeyError, ValueError):
                self.logger.warning(f"Invalid knowledge type: {knowledge_type_str}")
                return

            # Convert tags to set if provided
            if tags and isinstance(tags, list):
                tags = set(tags)

            # Publish the knowledge item
            try:
                knowledge_id = await self.publish_knowledge(
                    knowledge_type=knowledge_type,
                    topic=topic,
                    content=content,
                    metadata=metadata,
                    source_id=source_id,
                    access_control=access_control,
                    tags=tags,
                )

                # Publish response
                await self.publisher.publish_notification(
                    notification_name="knowledge_publish_response",
                    data={"knowledge_id": knowledge_id, "success": True},
                    correlation_id=correlation_id,
                )
            except PublishError as e:
                # Publish error response
                await self.publisher.publish_notification(
                    notification_name="knowledge_publish_response",
                    data={"success": False, "error": str(e)},
                    correlation_id=correlation_id,
                )
        except Exception as e:
            self.logger.error(
                f"Error handling knowledge publish event: {str(e)}", exc_info=True
            )

    async def _handle_knowledge_update(self, event: Event) -> None:
        """
        Handle a knowledge update event.

        Args:
            event: Knowledge update event
        """
        try:
            # Extract knowledge information
            knowledge_id = event.data.get("knowledge_id")
            content = event.data.get("content")
            metadata = event.data.get("metadata")
            status_str = event.data.get("status")
            tags = event.data.get("tags")
            correlation_id = event.correlation_id

            if not knowledge_id:
                self.logger.warning(
                    "Received knowledge update event with missing knowledge_id"
                )
                return

            # Convert status string to enum if provided
            status = None
            if status_str:
                try:
                    status = KnowledgeStatus[status_str]
                except (KeyError, ValueError):
                    self.logger.warning(f"Invalid knowledge status: {status_str}")
                    return

            # Convert tags to set if provided
            if tags and isinstance(tags, list):
                tags = set(tags)

            # Update the knowledge item
            try:
                updated_id = await self.update_knowledge_by_id(
                    knowledge_id=knowledge_id,
                    content=content,
                    metadata=metadata,
                    status=status,
                    tags=tags,
                )

                # Publish response
                await self.publisher.publish_notification(
                    notification_name="knowledge_update_response",
                    data={
                        "knowledge_id": knowledge_id,
                        "updated_id": updated_id,
                        "success": True,
                    },
                    correlation_id=correlation_id,
                )
            except PublishError as e:
                # Publish error response
                await self.publisher.publish_notification(
                    notification_name="knowledge_update_response",
                    data={
                        "knowledge_id": knowledge_id,
                        "success": False,
                        "error": str(e),
                    },
                    correlation_id=correlation_id,
                )
        except Exception as e:
            self.logger.error(
                f"Error handling knowledge update event: {str(e)}", exc_info=True
            )

    async def _handle_knowledge_delete(self, event: Event) -> None:
        """
        Handle a knowledge delete event.

        Args:
            event: Knowledge delete event
        """
        try:
            # Extract knowledge information
            knowledge_id = event.data.get("knowledge_id")
            correlation_id = event.correlation_id

            if not knowledge_id:
                self.logger.warning(
                    "Received knowledge delete event with missing knowledge_id"
                )
                return

            # Delete the knowledge item
            try:
                deleted = await self.delete_knowledge_by_id(knowledge_id)

                # Publish response
                await self.publisher.publish_notification(
                    notification_name="knowledge_delete_response",
                    data={"knowledge_id": knowledge_id, "success": deleted},
                    correlation_id=correlation_id,
                )
            except PublishError as e:
                # Publish error response
                await self.publisher.publish_notification(
                    notification_name="knowledge_delete_response",
                    data={
                        "knowledge_id": knowledge_id,
                        "success": False,
                        "error": str(e),
                    },
                    correlation_id=correlation_id,
                )
        except Exception as e:
            self.logger.error(
                f"Error handling knowledge delete event: {str(e)}", exc_info=True
            )

    async def _publish_knowledge_added_event(self, knowledge: KnowledgeItem) -> None:
        """
        Publish a knowledge added event.

        Args:
            knowledge: The added knowledge item
        """
        await self.publisher.publish_notification(
            notification_name="knowledge_added",
            data={
                "knowledge_id": knowledge.knowledge_id,
                "knowledge_type": knowledge.knowledge_type.name,
                "topic": knowledge.topic,
                "source_id": knowledge.source_id,
                "created_at": knowledge.created_at.isoformat(),
            },
        )

    async def _publish_knowledge_updated_event(self, knowledge: KnowledgeItem) -> None:
        """
        Publish a knowledge updated event.

        Args:
            knowledge: The updated knowledge item
        """
        await self.publisher.publish_notification(
            notification_name="knowledge_updated",
            data={
                "knowledge_id": knowledge.knowledge_id,
                "previous_version_id": knowledge.previous_version_id,
                "knowledge_type": knowledge.knowledge_type.name,
                "topic": knowledge.topic,
                "source_id": knowledge.source_id,
                "updated_at": knowledge.updated_at.isoformat(),
                "version": knowledge.version,
            },
        )

    async def _publish_knowledge_deleted_event(self, knowledge: KnowledgeItem) -> None:
        """
        Publish a knowledge deleted event.

        Args:
            knowledge: The deleted knowledge item
        """
        await self.publisher.publish_notification(
            notification_name="knowledge_deleted",
            data={
                "knowledge_id": knowledge.knowledge_id,
                "knowledge_type": knowledge.knowledge_type.name,
                "topic": knowledge.topic,
                "source_id": knowledge.source_id,
            },
        )

    async def get_all_knowledge(self) -> List[KnowledgeItem]:
        """
        Get all knowledge items in the repository.

        Returns:
            List of all knowledge items

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Try to get from cache first
            cached_items = await self.cache.get_all()
            if cached_items and len(cached_items) == len(self.knowledge_items):
                return cached_items

            # Get all knowledge items
            items = list(self.knowledge_items.values())

            # Add to cache
            for item in items:
                await self.cache.add(item)

            return items
        except Exception as e:
            error_msg = f"Failed to get all knowledge items: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    async def get_knowledge_updates(
        self, since_timestamp: datetime
    ) -> List[KnowledgeItem]:
        """
        Get knowledge items updated since a timestamp.

        Args:
            since_timestamp: Timestamp to get updates since

        Returns:
            List of knowledge items updated since the timestamp

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Get all knowledge items
            items = list(self.knowledge_items.values())

            # Filter by update timestamp
            updated_items = [
                item for item in items if item.updated_at > since_timestamp
            ]

            # Add to cache
            for item in updated_items:
                await self.cache.add(item)

            return updated_items
        except Exception as e:
            error_msg = (
                f"Failed to get knowledge updates since {since_timestamp}: {str(e)}"
            )
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)

    async def get_critical_updates(
        self, since_timestamp: datetime, priority_threshold: float = 0.5
    ) -> List[KnowledgeItem]:
        """
        Get critical knowledge updates since a timestamp.

        This method is optimized for mobile devices with limited bandwidth.
        It returns only high-priority knowledge updates.

        Args:
            since_timestamp: Timestamp to get updates since
            priority_threshold: Priority threshold (0.0 to 1.0)

        Returns:
            List of critical knowledge items updated since the timestamp

        Raises:
            KnowledgeError: If the knowledge items cannot be retrieved
        """
        try:
            # Get all knowledge items updated since the timestamp
            updated_items = await self.get_knowledge_updates(since_timestamp)

            # Filter by priority
            critical_items = []
            for item in updated_items:
                # Calculate priority based on metadata, type, and status
                priority = 0.0

                # Knowledge type priority
                if item.knowledge_type == KnowledgeType.RULE:
                    priority += 0.3  # Rules are important
                elif item.knowledge_type == KnowledgeType.PROCEDURE:
                    priority += 0.2  # Procedures are somewhat important

                # Status priority
                if item.status == KnowledgeStatus.ACTIVE:
                    priority += 0.2  # Active items are important
                elif item.status == KnowledgeStatus.DEPRECATED:
                    priority += 0.1  # Deprecated items are somewhat important

                # Metadata priority
                if item.metadata:
                    # Check for priority in metadata
                    if "priority" in item.metadata:
                        try:
                            metadata_priority = float(item.metadata["priority"])
                            priority += metadata_priority
                        except (ValueError, TypeError):
                            pass

                    # Check for critical flag in metadata
                    if "critical" in item.metadata and item.metadata["critical"]:
                        priority += 0.3

                # Normalize priority to 0.0-1.0 range
                priority = min(1.0, priority)

                # Add to critical items if priority is above threshold
                if priority >= priority_threshold:
                    critical_items.append(item)
                    # Add to cache
                    await self.cache.add(item)

            return critical_items
        except Exception as e:
            error_msg = f"Failed to get critical knowledge updates since {since_timestamp}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise KnowledgeError(error_msg, cause=e)
