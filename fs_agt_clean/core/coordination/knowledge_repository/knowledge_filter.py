"""
Knowledge filter classes for filtering knowledge items.
"""

import abc
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from fs_agt_clean.core.coordination.knowledge_repository.knowledge_item import (
    KnowledgeItem,
    KnowledgeStatus,
    KnowledgeType,
)


class KnowledgeFilter(abc.ABC):
    """
    Base class for knowledge filters.
    """

    @abc.abstractmethod
    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches the filter, False otherwise
        """
        pass


class TopicFilter(KnowledgeFilter):
    """
    Filter knowledge items by topic.
    """

    def __init__(
        self, topics: Optional[Set[str]] = None, patterns: Optional[Set[str]] = None
    ):
        """
        Initialize the topic filter.

        Args:
            topics: Set of topics to match (exact match)
            patterns: Set of topic patterns to match (regex match)
        """
        self.topics = topics or set()
        self.patterns = patterns or set()
        self.compiled_patterns = [re.compile(pattern) for pattern in self.patterns]

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches the filter, False otherwise
        """
        # Check for exact topic match
        if knowledge.topic in self.topics:
            return True

        # Check for pattern match
        for pattern in self.compiled_patterns:
            if pattern.match(knowledge.topic):
                return True

        return False


class TypeFilter(KnowledgeFilter):
    """
    Filter knowledge items by type.
    """

    def __init__(self, types: Set[KnowledgeType]):
        """
        Initialize the type filter.

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
            True if the knowledge item matches the filter, False otherwise
        """
        return knowledge.knowledge_type in self.types


class StatusFilter(KnowledgeFilter):
    """
    Filter knowledge items by status.
    """

    def __init__(self, statuses: Set[KnowledgeStatus]):
        """
        Initialize the status filter.

        Args:
            statuses: Set of knowledge statuses to match
        """
        self.statuses = statuses

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches the filter, False otherwise
        """
        return knowledge.status in self.statuses


class TagFilter(KnowledgeFilter):
    """
    Filter knowledge items by tag.
    """

    def __init__(self, tags: Set[str], match_all: bool = False):
        """
        Initialize the tag filter.

        Args:
            tags: Set of tags to match
            match_all: If True, all tags must match; if False, any tag must match
        """
        self.tags = tags
        self.match_all = match_all

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches the filter, False otherwise
        """
        if not knowledge.tags:
            return False

        if self.match_all:
            # All tags must match
            return all(tag in knowledge.tags for tag in self.tags)
        else:
            # Any tag must match
            return any(tag in knowledge.tags for tag in self.tags)


class SourceFilter(KnowledgeFilter):
    """
    Filter knowledge items by source.
    """

    def __init__(self, sources: Set[str]):
        """
        Initialize the source filter.

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
            True if the knowledge item matches the filter, False otherwise
        """
        return knowledge.source_id in self.sources


class CompositeFilter(KnowledgeFilter):
    """
    Base class for composite filters.
    """

    def __init__(self, filters: List[KnowledgeFilter]):
        """
        Initialize the composite filter.

        Args:
            filters: List of filters to combine
        """
        self.filters = filters


class AndFilter(CompositeFilter):
    """
    Filter that matches if all child filters match.
    """

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches all child filters, False otherwise
        """
        return all(filter.matches(knowledge) for filter in self.filters)


class OrFilter(CompositeFilter):
    """
    Filter that matches if any child filter matches.
    """

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item matches any child filter, False otherwise
        """
        return any(filter.matches(knowledge) for filter in self.filters)


class NotFilter(KnowledgeFilter):
    """
    Filter that matches if the child filter does not match.
    """

    def __init__(self, filter: KnowledgeFilter):
        """
        Initialize the NOT filter.

        Args:
            filter: Filter to negate
        """
        self.filter = filter

    def matches(self, knowledge: KnowledgeItem) -> bool:
        """
        Check if a knowledge item matches the filter.

        Args:
            knowledge: Knowledge item to check

        Returns:
            True if the knowledge item does not match the child filter, False otherwise
        """
        return not self.filter.matches(knowledge)
