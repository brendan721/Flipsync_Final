"""
Knowledge subscriber for the knowledge repository.

This module provides interfaces and implementations for subscribing to knowledge
updates in the knowledge repository, including filtering and notification.
"""

import abc
import re
from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple, Union

from fs_agt_clean.core.coordination.event_system import (
    Event,
    EventPriority,
    EventType,
)
from fs_agt_clean.core.coordination.event_system import (
    SubscriptionFilter as EventSubscriptionFilter,
)
from fs_agt_clean.core.coordination.event_system import (
    create_subscriber,
)
from fs_agt_clean.core.coordination.knowledge_repository.knowledge_repository import (
    KnowledgeError,
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeType,
)
from fs_agt_clean.core.monitoring import get_logger

# Type for knowledge notification handlers
KnowledgeHandler = Callable[[KnowledgeItem], None]


class SubscriptionFilter(abc.ABC):
    """
    Interface for knowledge subscription filters.

    Subscription filters determine which knowledge items a subscriber
    receives notifications for.
    """

    @abc.abstractmethod
    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches the filter
        """
        pass


class TopicFilter(SubscriptionFilter):
    """
    Filter for knowledge topics.

    This filter matches knowledge items with specific topics.
    """

    def __init__(self, topics: Set[str]):
        """
        Initialize a topic filter.

        Args:
            topics: Set of topics to match
        """
        self.topics = topics

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item's topic is in the filter's topics
        """
        return knowledge.topic in self.topics


class SourceFilter(SubscriptionFilter):
    """
    Filter for knowledge sources.

    This filter matches knowledge items from specific sources.
    """

    def __init__(self, sources: Set[str]):
        """
        Initialize a source filter.

        Args:
            sources: Set of source IDs to match
        """
        self.sources = sources

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item's source is in the filter's sources
        """
        return knowledge.source_id in self.sources if knowledge.source_id else False


class TypeFilter(SubscriptionFilter):
    """
    Filter for knowledge types.

    This filter matches knowledge items with specific types.
    """

    def __init__(self, types: Set[KnowledgeType]):
        """
        Initialize a type filter.

        Args:
            types: Set of knowledge types to match
        """
        self.types = types

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item's type is in the filter's types
        """
        return knowledge.knowledge_type in self.types


class TagFilter(SubscriptionFilter):
    """
    Filter for knowledge tags.

    This filter matches knowledge items with specific tags.
    """

    def __init__(self, tags: Set[str], match_all: bool = False):
        """
        Initialize a tag filter.

        Args:
            tags: Set of tags to match
            match_all: If True, all tags must match; if False, any tag can match
        """
        self.tags = tags
        self.match_all = match_all

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item's tags match the filter's tags
        """
        if not knowledge.tags:
            return False

        if self.match_all:
            return self.tags.issubset(knowledge.tags)
        else:
            return bool(self.tags.intersection(knowledge.tags))


class TopicPatternFilter(SubscriptionFilter):
    """
    Filter for knowledge topics using regex patterns.

    This filter matches knowledge items with topics that match specific patterns.
    """

    def __init__(self, patterns: List[str]):
        """
        Initialize a topic pattern filter.

        Args:
            patterns: List of regex patterns to match
        """
        self.patterns = [re.compile(pattern) for pattern in patterns]

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item's topic matches any of the filter's patterns
        """
        return any(pattern.search(knowledge.topic) for pattern in self.patterns)


class CompositeFilter(SubscriptionFilter):
    """
    Composite filter combining multiple filters.

    This filter combines multiple filters using logical operations.
    """

    def __init__(self, filters: List[SubscriptionFilter], match_all: bool = True):
        """
        Initialize a composite filter.

        Args:
            filters: List of filters to combine
            match_all: If True, all filters must match; if False, any filter can match
        """
        self.filters = filters
        self.match_all = match_all

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches the composite filter
        """
        if not self.filters:
            return True

        if self.match_all:
            return all(f.matches(knowledge) for f in self.filters)
        else:
            return any(f.matches(knowledge) for f in self.filters)


class CustomFilter(SubscriptionFilter):
    """
    Custom filter using a callback function.

    This filter uses a custom callback function to determine matches.
    """

    def __init__(self, callback: Callable[[KnowledgeItem], bool]):
        """
        Initialize a custom filter.

        Args:
            callback: Function that takes a knowledge item and returns a boolean
        """
        self.callback = callback

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches the custom filter
        """
        return self.callback(knowledge)


class KnowledgeSubscriber(abc.ABC):
    """
    Interface for knowledge subscribers.

    Knowledge subscribers receive notifications about knowledge updates
    in the knowledge repository.
    """

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from knowledge updates.

        Args:
            subscription_id: ID of the subscription

        Returns:
            True if the subscription was removed
        """
        pass

    @abc.abstractmethod
    async def get_subscriptions(self) -> List[Dict[str, Any]]:
        """
        Get all subscriptions for this subscriber.

        Returns:
            List of subscription information
        """
        pass
