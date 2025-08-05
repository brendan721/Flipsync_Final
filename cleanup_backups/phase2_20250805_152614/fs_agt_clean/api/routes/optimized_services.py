#!/usr/bin/env python3
"""
Optimized Services API Routes

This module provides API endpoints for testing and using the optimized services:
- OptimizedApiClient with circuit breaker
- OptimizedEbayService with official SDKs
- Performance metrics and health checks
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from fs_agt_clean.core.api.optimized_service_integration import (
    get_optimized_service_manager,
)
from fs_agt_clean.api.dependencies.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["optimized-services"])


@router.get("/health")
async def optimized_services_health():
    """
    Get health status of optimized services.

    Returns:
        Health status and metrics
    """
    try:
        service_manager = await get_optimized_service_manager()
        health_status = await service_manager.health_check()

        return {
            "status": "success",
            "data": health_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Optimized services health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/metrics")
async def optimized_services_metrics():
    """
    Get performance metrics for optimized services.

    Returns:
        Performance metrics including success rates and cache hits
    """
    try:
        service_manager = await get_optimized_service_manager()
        metrics = service_manager.get_metrics()

        return {
            "status": "success",
            "data": {
                "metrics": metrics,
                "description": {
                    "total_requests": "Total API requests processed",
                    "successful_requests": "Successfully completed requests",
                    "failed_requests": "Failed requests",
                    "success_rate": "Success rate percentage",
                    "cache_hits": "Requests served from cache",
                    "cache_hit_rate": "Cache hit rate percentage",
                    "circuit_breaker_trips": "Circuit breaker activations",
                },
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get optimized services metrics: {e}")
        raise HTTPException(
            status_code=500, detail=f"Metrics retrieval failed: {str(e)}"
        )


@router.post("/metrics/reset")
async def reset_optimized_services_metrics(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Reset performance metrics for optimized services.

    Requires authentication.
    """
    try:
        service_manager = await get_optimized_service_manager()
        service_manager.reset_metrics()

        return {
            "status": "success",
            "message": "Optimized services metrics reset successfully",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to reset optimized services metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics reset failed: {str(e)}")


@router.get("/ebay/categories/test")
async def test_optimized_ebay_categories():
    """
    Test optimized eBay categories endpoint.

    This endpoint tests the optimized API client with circuit breaker.
    """
    try:
        service_manager = await get_optimized_service_manager()

        # Test with dummy auth headers (for testing circuit breaker)
        dummy_headers = {"Authorization": "Bearer test"}

        # This will test the circuit breaker pattern
        categories = await service_manager.get_ebay_categories(dummy_headers)

        return {
            "status": "success",
            "data": {
                "categories_count": len(categories),
                "sample_categories": categories[:5] if categories else [],
                "source": "optimized_api_client",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Optimized eBay categories test failed: {e}")
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}",
            "note": "This is expected if eBay credentials are not configured",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


@router.get("/ebay/category/{category_id}/specifics")
async def test_optimized_category_specifics(category_id: str):
    """
    Test optimized category specifics with hybrid fallback.

    Args:
        category_id: eBay category ID to test

    Returns:
        Category specifics from optimized service
    """
    try:
        service_manager = await get_optimized_service_manager()

        # Test hybrid fallback strategy (local taxonomy -> eBay API -> defaults)
        specifics = await service_manager.get_category_specifics(category_id)

        return {
            "status": "success",
            "data": {
                "category_id": category_id,
                "specifics": specifics,
                "source": specifics.get("source", "unknown"),
                "lookup_time_ms": specifics.get("lookup_time_ms", 0),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Optimized category specifics test failed for {category_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Category specifics test failed: {str(e)}"
        )


@router.get("/comparison/legacy-vs-optimized")
async def compare_legacy_vs_optimized():
    """
    Compare legacy vs optimized service performance.

    Returns:
        Comparison of features and performance metrics
    """
    try:
        service_manager = await get_optimized_service_manager()
        metrics = service_manager.get_metrics()

        comparison = {
            "legacy_services": {
                "features": [
                    "Basic HTTP requests",
                    "Simple error handling",
                    "No connection pooling",
                    "No circuit breaker",
                    "Mixed HTTP/HTTPS URLs",
                    "No local caching",
                ],
                "performance": "Variable, no metrics",
                "fault_tolerance": "Limited",
            },
            "optimized_services": {
                "features": [
                    "Circuit breaker pattern",
                    "Connection pooling (100 concurrent)",
                    "Batch processing",
                    "Enhanced error handling",
                    "Consistent HTTPS URLs",
                    "Local taxonomy caching",
                    "Official eBay SDKs",
                    "Performance monitoring",
                ],
                "performance": {
                    "success_rate": f"{metrics.get('success_rate', 0):.1f}%",
                    "cache_hit_rate": f"{metrics.get('cache_hit_rate', 0):.1f}%",
                    "total_requests": metrics.get("total_requests", 0),
                },
                "fault_tolerance": "Circuit breaker + retry logic",
            },
            "improvements": [
                "Eliminated mixed content issues",
                "Added fault tolerance with circuit breaker",
                "Improved performance with connection pooling",
                "Enhanced caching with local taxonomy",
                "Better error handling and monitoring",
                "Consistent HTTPS URL management",
            ],
        }

        return {
            "status": "success",
            "data": comparison,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to generate comparison: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
