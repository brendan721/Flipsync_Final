"""
Knowledge cache for the knowledge repository.

This module provides interfaces and implementations for caching knowledge
items, enabling efficient access and offline operation.
"""

import abc
import asyncio
import time
from collections import OrderedDict
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.knowledge_repository.knowledge_repository import (
    KnowledgeError,
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeType,
)
from fs_agt_clean.core.monitoring import get_logger


class CacheStrategy(Enum):
    """Cache replacement strategies."""

    LRU = auto()  # Least Recently Used
    LFU = auto()  # Least Frequently Used
    FIFO = auto()  # First In, First Out
    PRIORITY = auto()  # Priority-based


class KnowledgeCache(abc.ABC):
    """
    Interface for knowledge caches.

    Knowledge caches store knowledge items locally for efficient access
    and offline operation.
    """

    @abc.abstractmethod
    async def add(self, knowledge: KnowledgeItem) -> None:
        """
        Add a knowledge item to the cache.

        Args:
            knowledge: Knowledge item to add
        """
        pass

    @abc.abstractmethod
    async def get(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """
        Get a knowledge item from the cache.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            The knowledge item, or None if not in the cache
        """
        pass

    @abc.abstractmethod
    async def remove(self, knowledge_id: str) -> bool:
        """
        Remove a knowledge item from the cache.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            True if the knowledge item was removed
        """
        pass

    @abc.abstractmethod
    async def clear(self) -> None:
        """
        Clear all knowledge items from the cache.
        """
        pass

    @abc.abstractmethod
    async def get_by_topic(self, topic: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by topic from the cache.

        Args:
            topic: Topic to search for

        Returns:
            List of knowledge items with the specified topic
        """
        pass

    @abc.abstractmethod
    async def get_by_type(self, knowledge_type: KnowledgeType) -> List[KnowledgeItem]:
        """
        Get knowledge items by type from the cache.

        Args:
            knowledge_type: Type to search for

        Returns:
            List of knowledge items with the specified type
        """
        pass

    @abc.abstractmethod
    async def get_by_tag(self, tag: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by tag from the cache.

        Args:
            tag: Tag to search for

        Returns:
            List of knowledge items with the specified tag
        """
        pass

    @abc.abstractmethod
    async def get_by_status(self, status: KnowledgeStatus) -> List[KnowledgeItem]:
        """
        Get knowledge items by status from the cache.

        Args:
            status: Status to search for

        Returns:
            List of knowledge items with the specified status
        """
        pass

    @abc.abstractmethod
    async def get_all(self) -> List[KnowledgeItem]:
        """
        Get all knowledge items from the cache.

        Returns:
            List of all knowledge items in the cache
        """
        pass

    @abc.abstractmethod
    async def get_size(self) -> int:
        """
        Get the number of knowledge items in the cache.

        Returns:
            Number of knowledge items
        """
        pass

    @abc.abstractmethod
    async def get_max_size(self) -> int:
        """
        Get the maximum size of the cache.

        Returns:
            Maximum number of knowledge items
        """
        pass

    @abc.abstractmethod
    async def set_max_size(self, max_size: int) -> None:
        """
        Set the maximum size of the cache.

        Args:
            max_size: Maximum number of knowledge items
        """
        pass

    @abc.abstractmethod
    async def get_strategy(self) -> CacheStrategy:
        """
        Get the cache replacement strategy.

        Returns:
            Cache replacement strategy
        """
        pass

    @abc.abstractmethod
    async def set_strategy(self, strategy: CacheStrategy) -> None:
        """
        Set the cache replacement strategy.

        Args:
            strategy: Cache replacement strategy
        """
        pass


class LRUCache(KnowledgeCache):
    """
    Least Recently Used (LRU) knowledge cache.

    This implementation uses an OrderedDict to maintain the LRU order.
    """

    def __init__(self, cache_id: str, max_size: int = 1000):
        """
        Initialize an LRU cache.

        Args:
            cache_id: Unique identifier for this cache
            max_size: Maximum number of knowledge items
        """
        self.cache_id = cache_id
        self.logger = get_logger(f"knowledge_cache.{cache_id}")
        self.max_size = max_size
        self.strategy = CacheStrategy.LRU

        # Initialize cache
        self.cache: OrderedDict[str, KnowledgeItem] = OrderedDict()

        # Initialize indexes
        self.topic_index: Dict[str, Set[str]] = {}
        self.type_index: Dict[KnowledgeType, Set[str]] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        self.status_index: Dict[KnowledgeStatus, Set[str]] = {}

    async def add(self, knowledge: KnowledgeItem) -> None:
        """
        Add a knowledge item to the cache.

        Args:
            knowledge: Knowledge item to add
        """
        knowledge_id = knowledge.knowledge_id

        # If the item is already in the cache, remove it first
        if knowledge_id in self.cache:
            await self.remove(knowledge_id)

        # If the cache is full, remove the least recently used item
        if len(self.cache) >= self.max_size:
            # Get the oldest item (first item in the OrderedDict)
            oldest_id, _ = next(iter(self.cache.items()))
            await self.remove(oldest_id)

        # Add the item to the cache
        self.cache[knowledge_id] = knowledge

        # Update indexes
        topic = knowledge.topic
        if topic not in self.topic_index:
            self.topic_index[topic] = set()
        self.topic_index[topic].add(knowledge_id)

        knowledge_type = knowledge.knowledge_type
        if knowledge_type not in self.type_index:
            self.type_index[knowledge_type] = set()
        self.type_index[knowledge_type].add(knowledge_id)

        for tag in knowledge.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(knowledge_id)

        status = knowledge.status
        if status not in self.status_index:
            self.status_index[status] = set()
        self.status_index[status].add(knowledge_id)

        self.logger.debug(f"Added knowledge item to cache: {knowledge_id}")

    async def get(self, knowledge_id: str) -> Optional[KnowledgeItem]:
        """
        Get a knowledge item from the cache.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            The knowledge item, or None if not in the cache
        """
        # Get the item from the cache
        knowledge = self.cache.get(knowledge_id)

        # If the item exists, move it to the end (most recently used)
        if knowledge:
            self.cache.move_to_end(knowledge_id)

        return knowledge

    async def remove(self, knowledge_id: str) -> bool:
        """
        Remove a knowledge item from the cache.

        Args:
            knowledge_id: ID of the knowledge item

        Returns:
            True if the knowledge item was removed
        """
        # Check if the item is in the cache
        if knowledge_id not in self.cache:
            return False

        # Get the item before removing it
        knowledge = self.cache[knowledge_id]

        # Remove the item from the cache
        del self.cache[knowledge_id]

        # Remove from indexes
        topic = knowledge.topic
        if topic in self.topic_index:
            self.topic_index[topic].discard(knowledge_id)
            if not self.topic_index[topic]:
                del self.topic_index[topic]

        knowledge_type = knowledge.knowledge_type
        if knowledge_type in self.type_index:
            self.type_index[knowledge_type].discard(knowledge_id)
            if not self.type_index[knowledge_type]:
                del self.type_index[knowledge_type]

        for tag in knowledge.tags:
            if tag in self.tag_index:
                self.tag_index[tag].discard(knowledge_id)
                if not self.tag_index[tag]:
                    del self.tag_index[tag]

        status = knowledge.status
        if status in self.status_index:
            self.status_index[status].discard(knowledge_id)
            if not self.status_index[status]:
                del self.status_index[status]

        self.logger.debug(f"Removed knowledge item from cache: {knowledge_id}")
        return True

    async def clear(self) -> None:
        """
        Clear all knowledge items from the cache.
        """
        self.cache.clear()
        self.topic_index.clear()
        self.type_index.clear()
        self.tag_index.clear()
        self.status_index.clear()
        self.logger.debug("Cleared knowledge cache")

    async def get_by_topic(self, topic: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by topic from the cache.

        Args:
            topic: Topic to search for

        Returns:
            List of knowledge items with the specified topic
        """
        # Get the IDs of items with the specified topic
        knowledge_ids = self.topic_index.get(topic, set())

        # Get the items and update their LRU order
        items = []
        for knowledge_id in knowledge_ids:
            knowledge = await self.get(knowledge_id)
            if knowledge:
                items.append(knowledge)

        return items

    async def get_by_type(self, knowledge_type: KnowledgeType) -> List[KnowledgeItem]:
        """
        Get knowledge items by type from the cache.

        Args:
            knowledge_type: Type to search for

        Returns:
            List of knowledge items with the specified type
        """
        # Get the IDs of items with the specified type
        knowledge_ids = self.type_index.get(knowledge_type, set())

        # Get the items and update their LRU order
        items = []
        for knowledge_id in knowledge_ids:
            knowledge = await self.get(knowledge_id)
            if knowledge:
                items.append(knowledge)

        return items

    async def get_by_tag(self, tag: str) -> List[KnowledgeItem]:
        """
        Get knowledge items by tag from the cache.

        Args:
            tag: Tag to search for

        Returns:
            List of knowledge items with the specified tag
        """
        # Get the IDs of items with the specified tag
        knowledge_ids = self.tag_index.get(tag, set())

        # Get the items and update their LRU order
        items = []
        for knowledge_id in knowledge_ids:
            knowledge = await self.get(knowledge_id)
            if knowledge:
                items.append(knowledge)

        return items

    async def get_by_status(self, status: KnowledgeStatus) -> List[KnowledgeItem]:
        """
        Get knowledge items by status from the cache.

        Args:
            status: Status to search for

        Returns:
            List of knowledge items with the specified status
        """
        # Get the IDs of items with the specified status
        knowledge_ids = self.status_index.get(status, set())

        # Get the items and update their LRU order
        items = []
        for knowledge_id in knowledge_ids:
            knowledge = await self.get(knowledge_id)
            if knowledge:
                items.append(knowledge)

        return items

    async def get_all(self) -> List[KnowledgeItem]:
        """
        Get all knowledge items from the cache.

        Returns:
            List of all knowledge items in the cache
        """
        # Return a copy of all items
        return list(self.cache.values())

    async def get_size(self) -> int:
        """
        Get the number of knowledge items in the cache.

        Returns:
            Number of knowledge items
        """
        return len(self.cache)

    async def get_max_size(self) -> int:
        """
        Get the maximum size of the cache.

        Returns:
            Maximum number of knowledge items
        """
        return self.max_size

    async def set_max_size(self, max_size: int) -> None:
        """
        Set the maximum size of the cache.

        Args:
            max_size: Maximum number of knowledge items
        """
        # Ensure max_size is positive
        if max_size <= 0:
            raise ValueError("Maximum size must be positive")

        # Set the new maximum size
        self.max_size = max_size

        # If the cache is now too large, remove the least recently used items
        while len(self.cache) > self.max_size:
            oldest_id, _ = next(iter(self.cache.items()))
            await self.remove(oldest_id)

    async def get_strategy(self) -> CacheStrategy:
        """
        Get the cache replacement strategy.

        Returns:
            Cache replacement strategy
        """
        return self.strategy

    async def set_strategy(self, strategy: CacheStrategy) -> None:
        """
        Set the cache replacement strategy.

        Args:
            strategy: Cache replacement strategy
        """
        # This implementation only supports LRU
        if strategy != CacheStrategy.LRU:
            raise ValueError(f"Unsupported cache strategy: {strategy}")

        self.strategy = strategy
