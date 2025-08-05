"""Vector store package initialization."""

from .client import QdrantClient as VectorStoreClient
from .models import ProductMetadata, SearchQuery, SearchResult
from .store import VectorStore

# Aliases for backward compatibility with expected import names
VectorStoreDocument = ProductMetadata
VectorStoreQuery = SearchQuery
VectorStoreResult = SearchResult

__all__ = [
    "VectorStoreClient",
    "VectorStore",
    "SearchResult",
    "SearchQuery",
    "ProductMetadata",
    "VectorStoreDocument",
    "VectorStoreQuery",
    "VectorStoreResult",
]
