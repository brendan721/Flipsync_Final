"""Simple QdrantService for document storage and retrieval.

This module provides a simplified service for storing, retrieving, and searching documents
using an in-memory dictionary as the backend.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.models.document import Document

logger = logging.getLogger(__name__)


class SimpleQdrantService:
    """Simple service for document operations using an in-memory dictionary."""

    def __init__(self):
        """Initialize the SimpleQdrantService."""
        self.documents = {}
        logger.info("Initialized SimpleQdrantService with in-memory storage")

    async def init_schema(self) -> None:
        """Initialize the schema (no-op for in-memory implementation)."""
        logger.info("SimpleQdrantService schema initialized")

    async def store_document(self, document: Document) -> bool:
        """Store a document in the in-memory dictionary.

        Args:
            document: The document to store

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure document has an ID
            if not document.id:
                document.id = str(uuid.uuid4())

            # Create document data
            doc_data = {
                "id": document.id,
                "content": document.content,
                "metadata": document.metadata or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            # Add title to metadata if available
            if hasattr(document, "title") and document.title:
                doc_data["title"] = document.title
                if not doc_data["metadata"]:
                    doc_data["metadata"] = {}
                doc_data["metadata"]["title"] = document.title

            # Store document
            self.documents[document.id] = doc_data

            logger.info(f"Stored document with ID: {document.id}")
            return True
        except Exception as e:
            logger.error(f"Error storing document: {str(e)}")
            return False

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a document by ID.

        Args:
            doc_id: The document ID

        Returns:
            Document data or None if not found
        """
        try:
            # Get document from dictionary
            doc = self.documents.get(doc_id)
            if not doc:
                logger.warning(f"Document not found: {doc_id}")
                return None

            return doc
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return None

    async def search_documents(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search documents by text query.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            List of matching documents
        """
        try:
            # Simple search implementation - just check if query is in content
            results = []
            for doc_id, doc in self.documents.items():
                if query.lower() in doc.get("content", "").lower():
                    # Add document to results with a mock score
                    doc_copy = doc.copy()
                    doc_copy["score"] = 0.9  # Mock score
                    results.append(doc_copy)

                    # Stop if we've reached the limit
                    if len(results) >= limit:
                        break

            return results
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID.

        Args:
            doc_id: The document ID

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete document from dictionary
            if doc_id in self.documents:
                del self.documents[doc_id]
                logger.info(f"Deleted document with ID: {doc_id}")
                return True
            else:
                logger.warning(f"Document not found for deletion: {doc_id}")
                return False
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
