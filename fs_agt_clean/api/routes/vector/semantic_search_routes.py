"""
Semantic Search API Routes for FlipSync.

This module provides API endpoints for vector-based semantic search,
product recommendations, and similarity analysis.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.core.config.vector_config import vector_db_manager
from fs_agt_clean.database.models.unified_user import UnifiedUser
from fs_agt_clean.database.repositories.vector_repository import (
    vector_embedding_repository,
)
from fs_agt_clean.services.vector.embedding_service import embedding_service

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/vector", tags=["semantic-search"])


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of results")
    score_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional search filters"
    )


class ProductEmbeddingRequest(BaseModel):
    """Request model for product embedding."""

    product_name: str = Field(..., description="Product name")
    description: str = Field(default="", description="Product description")
    category: str = Field(..., description="Product category")
    condition: str = Field(default="used", description="Product condition")
    brand: Optional[str] = Field(default=None, description="Product brand")
    features: Optional[List[str]] = Field(default=None, description="Product features")
    price: Optional[float] = Field(default=None, description="Product price")
    marketplace: str = Field(default="ebay", description="Target marketplace")


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""

    query: str
    results: List[Dict[str, Any]]
    total_results: int
    search_time_ms: float
    score_threshold: float


class ProductEmbeddingResponse(BaseModel):
    """Response model for product embedding."""

    product_id: str
    embedding_id: str
    success: bool
    message: str
    vector_dimension: int


class SimilarProductsResponse(BaseModel):
    """Response model for similar products."""

    product_id: str
    similar_products: List[Dict[str, Any]]
    total_found: int
    search_time_ms: float


@router.post("/search", response_model=SemanticSearchResponse)
async def semantic_search(
    request: SemanticSearchRequest,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Perform semantic search for products.

    This endpoint:
    - Generates embeddings for the search query
    - Searches for semantically similar products
    - Returns ranked results with similarity scores
    - Supports filtering and result limiting
    """
    try:
        start_time = datetime.now()

        logger.info(f"Semantic search for user {current_user.id}: {request.query}")

        # Perform semantic search
        results = await embedding_service.search_similar_products(
            query_text=request.query,
            limit=request.limit,
            score_threshold=request.score_threshold,
            filters=request.filters,
        )

        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000

        return SemanticSearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=round(search_time, 2),
            score_threshold=request.score_threshold,
        )

    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Semantic search failed: {str(e)}",
        )


@router.post("/embed/product", response_model=ProductEmbeddingResponse)
async def embed_product(
    request: ProductEmbeddingRequest,
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Generate and store embedding for a product.

    This endpoint:
    - Creates vector embedding for product data
    - Stores embedding in vector database
    - Returns embedding metadata and success status
    - Enables future semantic search and recommendations
    """
    try:
        logger.info(
            f"Embedding product for user {current_user.id}: {request.product_name}"
        )

        # Generate unique product ID
        import uuid

        product_id = str(uuid.uuid4())

        # Prepare product data
        product_data = {
            "name": request.product_name,
            "description": request.description,
            "category": request.category,
            "condition": request.condition,
            "brand": request.brand,
            "features": request.features or [],
            "price": request.price,
            "marketplace": request.marketplace,
        }

        # Generate and store embedding
        success = await embedding_service.embed_product(
            product_id=product_id,
            product_data=product_data,
            user_id=str(current_user.id),
        )

        if success:
            # Get embedding stats for response
            stats = await embedding_service.get_embedding_stats()
            vector_dimension = 384  # Default local embedding dimension

            return ProductEmbeddingResponse(
                product_id=product_id,
                embedding_id=f"emb_{product_id}",
                success=True,
                message="Product embedding created successfully",
                vector_dimension=vector_dimension,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product embedding",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error embedding product: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Product embedding failed: {str(e)}",
        )


@router.get("/similar/{product_id}", response_model=SimilarProductsResponse)
async def get_similar_products(
    product_id: str,
    limit: int = Query(
        default=10, ge=1, le=50, description="Maximum number of results"
    ),
    score_threshold: float = Query(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    ),
    current_user: UnifiedUser = Depends(AuthService.get_current_user),
):
    """
    Get products similar to a specific product.

    This endpoint:
    - Retrieves the embedding for the specified product
    - Searches for similar products in the vector database
    - Returns ranked similar products with scores
    - Supports result limiting and score thresholds
    """
    try:
        start_time = datetime.now()

        logger.info(
            f"Finding similar products for user {current_user.id}: {product_id}"
        )

        # Get product embedding
        embeddings = await vector_embedding_repository.get_embeddings_by_entity(
            entity_id=product_id, entity_type="product"
        )

        if not embeddings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product embedding not found: {product_id}",
            )

        # Use the first embedding for similarity search
        product_embedding = embeddings[0]

        # Search for similar embeddings
        similar_embeddings = (
            await vector_embedding_repository.search_similar_embeddings(
                query_vector=product_embedding.vector,
                entity_type="product",
                limit=limit + 1,  # +1 to exclude the original product
                score_threshold=score_threshold,
            )
        )

        # Format results (exclude the original product)
        similar_products = []
        for embedding, score in similar_embeddings:
            if embedding.entity_id != product_id:  # Exclude original product
                similar_products.append(
                    {
                        "product_id": embedding.entity_id,
                        "similarity_score": score,
                        "metadata": embedding.metadata,
                        "created_at": (
                            embedding.created_at.isoformat()
                            if embedding.created_at
                            else None
                        ),
                    }
                )

        # Limit results
        similar_products = similar_products[:limit]

        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000

        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=similar_products,
            total_found=len(similar_products),
            search_time_ms=round(search_time, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similar products search failed: {str(e)}",
        )


@router.get("/stats")
async def get_vector_stats(current_user: UnifiedUser = Depends(AuthService.get_current_user)):
    """
    Get vector database statistics and health information.

    This endpoint returns:
    - Vector database connection status
    - Collection statistics and health
    - Embedding service metrics
    - Performance information
    """
    try:
        # Get embedding service stats
        embedding_stats = await embedding_service.get_embedding_stats()

        # Get vector database health
        vector_health = await vector_db_manager.health_check()

        # Get collection stats
        collection_stats = await vector_embedding_repository.get_collection_stats()

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "embedding_service": embedding_stats,
                "vector_database": vector_health,
                "collections": collection_stats,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving vector stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve vector statistics: {str(e)}",
        )


@router.delete("/embedding/{embedding_id}")
async def delete_embedding(
    embedding_id: str, current_user: UnifiedUser = Depends(AuthService.get_current_user)
):
    """
    Delete a vector embedding.

    This endpoint:
    - Removes the specified embedding from the vector database
    - Returns success status
    - Requires proper authentication
    """
    try:
        logger.info(f"Deleting embedding for user {current_user.id}: {embedding_id}")

        # Delete embedding
        success = await vector_embedding_repository.delete_embedding(embedding_id)

        if success:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "success": True,
                    "message": f"Embedding deleted successfully: {embedding_id}",
                    "deleted_at": datetime.now(timezone.utc).isoformat(),
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Embedding not found or could not be deleted: {embedding_id}",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting embedding: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete embedding: {str(e)}",
        )


@router.post("/health")
async def vector_health_check():
    """
    Perform health check on vector database and services.

    This endpoint:
    - Tests vector database connectivity
    - Validates collection health
    - Returns comprehensive health status
    - Available without authentication for monitoring
    """
    try:
        # Perform health checks
        vector_health = await vector_db_manager.health_check()
        embedding_stats = await embedding_service.get_embedding_stats()

        # Determine overall health
        overall_health = "healthy"
        if not vector_health.get("connected", False):
            overall_health = "degraded"

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": overall_health,
                "vector_database": vector_health,
                "embedding_service": embedding_stats,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
