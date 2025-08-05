"""Document models for FlipSync."""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Document model for storing and retrieving documents."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique document identifier",
    )
    content: str = Field(..., description="Document content")
    title: Optional[str] = Field(None, description="Document title")
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Document metadata"
    )
    embedding: Optional[List[float]] = Field(
        None, description="Document embedding vector"
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp",
    )

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "title": self.title,
            "metadata": self.metadata or {},
            "embedding": self.embedding,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            title=data.get("title"),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class SearchQuery(BaseModel):
    """Search query model for document search."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results"
    )
    offset: int = Field(default=0, ge=0, description="Result offset for pagination")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional search filters"
    )
    include_embeddings: bool = Field(
        default=False, description="Whether to include embeddings in results"
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert search query to dictionary."""
        return {
            "query": self.query,
            "limit": self.limit,
            "offset": self.offset,
            "filters": self.filters,
            "include_embeddings": self.include_embeddings,
        }


class DocumentSearchResult(BaseModel):
    """Document search result model."""

    document: Document = Field(..., description="Found document")
    score: float = Field(..., description="Relevance score")
    highlights: Optional[List[str]] = Field(default=None, description="Text highlights")

    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "highlights": self.highlights or [],
        }


class DocumentBatch(BaseModel):
    """Batch of documents for bulk operations."""

    documents: List[Document] = Field(..., description="List of documents")

    def to_dict(self) -> Dict[str, Any]:
        """Convert document batch to dictionary."""
        return {"documents": [doc.to_dict() for doc in self.documents]}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocumentBatch":
        """Create document batch from dictionary."""
        documents = [
            Document.from_dict(doc_data) for doc_data in data.get("documents", [])
        ]
        return cls(documents=documents)


class DocumentStats(BaseModel):
    """Document collection statistics."""

    total_documents: int = Field(..., description="Total number of documents")
    total_size_bytes: int = Field(..., description="Total size in bytes")
    average_document_size: float = Field(..., description="Average document size")
    last_updated: datetime = Field(..., description="Last update timestamp")

    def to_dict(self) -> Dict[str, Any]:
        """Convert document stats to dictionary."""
        return {
            "total_documents": self.total_documents,
            "total_size_bytes": self.total_size_bytes,
            "average_document_size": self.average_document_size,
            "last_updated": self.last_updated.isoformat(),
        }
