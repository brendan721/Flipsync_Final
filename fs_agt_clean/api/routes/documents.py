"""Document API routes for FlipSync.

This module provides API endpoints for document management, including:
- Creating documents
- Retrieving documents
- Searching documents
- Batch document processing
- Updating documents
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from fs_agt_clean.core.models.document import Document, SearchQuery
from fs_agt_clean.services.qdrant.simple_service import SimpleQdrantService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


class BatchDocuments(BaseModel):
    """Batch of documents for processing."""

    documents: List[Dict[str, Any]]


@router.post("/", status_code=201)
async def create_document(
    request: Request, document: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Create a new document.

    Args:
        request: The request object
        document: Document data including title, content, and optional metadata

    Returns:
        Document creation status and ID

    Raises:
        HTTPException: If document creation fails
    """
    # Validate required fields
    if "title" not in document:
        raise HTTPException(status_code=400, detail="Title is required")
    if "content" not in document:
        raise HTTPException(status_code=400, detail="Content is required")
    if "vector" in document and len(document["vector"]) != 1536:
        raise HTTPException(status_code=400, detail="Invalid vector dimension")

    try:
        # Create Document instance
        doc = Document(
            id=document.get("id", str(uuid.uuid4())),
            content=document["content"],
            metadata=document.get("metadata", {"title": document["title"]}),
            embedding=document.get("vector"),
        )

        # Get SimpleQdrantService from app state
        qdrant_service = request.app.state.qdrant_service
        if not qdrant_service:
            logger.error("SimpleQdrantService not available")
            raise HTTPException(status_code=500, detail="Document service unavailable")

        # Store document
        success = await qdrant_service.store_document(doc)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to store document")

        return {"status": "success", "id": doc.id}
    except Exception as e:
        logger.error(f"Error creating document: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Document creation failed: {str(e)}"
        )


@router.get("/{doc_id}")
async def get_document(request: Request, doc_id: str) -> Dict[str, Any]:
    """Get a document by ID.

    Args:
        request: The request object
        doc_id: Document ID

    Returns:
        Document data

    Raises:
        HTTPException: If document not found or retrieval fails
    """
    try:
        # Get SimpleQdrantService from app state
        qdrant_service = request.app.state.qdrant_service
        if not qdrant_service:
            logger.error("SimpleQdrantService not available")
            raise HTTPException(status_code=500, detail="Document service unavailable")

        # Get document
        doc = await qdrant_service.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Document retrieval failed: {str(e)}"
        )


@router.post("/search")
async def search_documents(
    request: Request, query: Dict[str, str]
) -> Dict[str, List[Dict[str, Any]]]:
    """Search documents by text.

    Args:
        request: The request object
        query: Search query with "query" field

    Returns:
        Search results

    Raises:
        HTTPException: If search fails
    """
    try:
        # Validate query
        if "query" not in query:
            raise HTTPException(status_code=400, detail="Query is required")

        # Get SimpleQdrantService from app state
        qdrant_service = request.app.state.qdrant_service
        if not qdrant_service:
            logger.error("SimpleQdrantService not available")
            raise HTTPException(status_code=500, detail="Document service unavailable")

        # Search documents
        results = await qdrant_service.search_documents(query["query"])
        return {"results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document search failed: {str(e)}")


@router.post("/batch", status_code=201)
async def batch_create_documents(
    request: Request, batch: BatchDocuments
) -> Dict[str, Any]:
    """Create multiple documents in batch.

    Args:
        request: The request object
        batch: Batch of documents

    Returns:
        Batch creation status and document IDs

    Raises:
        HTTPException: If batch creation fails
    """
    try:
        # Get SimpleQdrantService from app state
        qdrant_service = request.app.state.qdrant_service
        if not qdrant_service:
            logger.error("SimpleQdrantService not available")
            raise HTTPException(status_code=500, detail="Document service unavailable")

        # Convert each document to Document instance
        docs = []
        for doc_data in batch.documents:
            # Validate required fields
            if "title" not in doc_data:
                raise HTTPException(
                    status_code=400, detail="Title is required for all documents"
                )
            if "content" not in doc_data:
                raise HTTPException(
                    status_code=400, detail="Content is required for all documents"
                )

            doc = Document(
                id=doc_data.get("id", str(uuid.uuid4())),
                content=doc_data.get("content", ""),
                metadata=doc_data.get("metadata", {"title": doc_data.get("title", "")}),
                embedding=doc_data.get("vector"),
            )
            docs.append(doc)

        # Store documents
        ids = []
        for doc in docs:
            success = await qdrant_service.store_document(doc)
            if success:
                ids.append(doc.id)

        return {"status": "created", "ids": ids}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating batch documents: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Batch document creation failed: {str(e)}"
        )


@router.put("/{doc_id}")
async def update_document(
    request: Request, doc_id: str, document: Dict[str, Any] = Body(...)
) -> Dict[str, Any]:
    """Update a document.

    Args:
        request: The request object
        doc_id: Document ID
        document: Updated document data

    Returns:
        Update status

    Raises:
        HTTPException: If update fails
    """
    try:
        # Get SimpleQdrantService from app state
        qdrant_service = request.app.state.qdrant_service
        if not qdrant_service:
            logger.error("SimpleQdrantService not available")
            raise HTTPException(status_code=500, detail="Document service unavailable")

        # Create Document instance with updated data
        # Add title to metadata if provided
        metadata = document.get("metadata", {})
        if "title" in document:
            metadata["title"] = document["title"]

        doc = Document(
            id=doc_id,
            content=document.get("content", ""),
            metadata=metadata,
            embedding=document.get("vector"),
        )

        # Update document
        success = await qdrant_service.store_document(doc)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update document")

        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Document update failed: {str(e)}")
