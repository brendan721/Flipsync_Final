"""
Search services module.

This module provides comprehensive search functionality including
basic search, advanced search, analytics, and search service management.
"""

from fs_agt_clean.services.search.service import SearchResult, SearchService

# Import analytics if available
try:
    from fs_agt_clean.services.search.analytics import SearchAnalytics
except ImportError:
    SearchAnalytics = None

# Import advanced search with fallback
try:
    from fs_agt_clean.services.search.advanced_search import (
        AdvancedSearchEngine as AdvancedSearchService,
    )
except ImportError:
    # Create a simple fallback class
    class AdvancedSearchService:
        def __init__(self, *args, **kwargs):
            pass

        async def search(self, *args, **kwargs):
            return []


# Import models if available
try:
    from fs_agt_clean.services.search.models import SearchFilter, SearchQuery
except ImportError:
    # Create simple fallback classes
    class SearchQuery:
        def __init__(self, query: str):
            self.query = query

    class SearchFilter:
        def __init__(self, **kwargs):
            self.filters = kwargs


__all__ = [
    "SearchService",
    "SearchResult",
    "AdvancedSearchService",
    "SearchAnalytics",
    "SearchQuery",
    "SearchFilter",
]
