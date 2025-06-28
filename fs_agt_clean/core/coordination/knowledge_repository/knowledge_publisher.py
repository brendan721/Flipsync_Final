"""
Knowledge publisher for the knowledge repository.

This module provides interfaces and implementations for publishing knowledge
to the knowledge repository, including validation and notification.
"""

import abc
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.event_system import (
    Event,
    EventPriority,
    EventType,
    create_publisher,
)
from fs_agt_clean.core.coordination.knowledge_repository.embedding_provider import (
    EmbeddingError,
    EmbeddingProvider,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_repository import (
    KnowledgeError,
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeType,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_validator import (
    KnowledgeValidator,
    ValidationError,
)
from fs_agt_clean.core.monitoring import get_logger


class PublishError(Exception):
    """Base exception for knowledge publisher errors."""

    def __init__(
        self,
        message: str,
        knowledge_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        """
        Initialize a publish error.

        Args:
            message: Error message
            knowledge_id: ID of the knowledge item related to the error
            cause: Original exception that caused this error
        """
        self.message = message
        self.knowledge_id = knowledge_id
        self.cause = cause

        # Create a detailed error message
        detailed_message = message
        if knowledge_id:
            detailed_message += f" (knowledge_id: {knowledge_id})"
        if cause:
            detailed_message += f" - caused by: {str(cause)}"

        super().__init__(detailed_message)


class KnowledgePublisher(abc.ABC):
    """
    Interface for knowledge publishers.

    Knowledge publishers publish knowledge to the knowledge repository,
    including validation and notification.
    """

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    async def update_knowledge(
        self,
        knowledge_id: str,
        content: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: Optional[KnowledgeStatus] = None,
        tags: Optional[Set[str]] = None,
    ) -> str:
        """
        Update a knowledge item in the repository.

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
        pass

    @abc.abstractmethod
    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """
        Delete a knowledge item from the repository.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            True if the knowledge item was deleted

        Raises:
            PublishError: If the knowledge item cannot be deleted
        """
        pass

    @abc.abstractmethod
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
        pass
