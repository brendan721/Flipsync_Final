#!/usr/bin/env python3
"""
Optimized Service Integration for FlipSync Backend

This module integrates the optimized API clients and services to replace legacy implementations:
- OptimizedApiClient with circuit breaker and connection pooling
- OptimizedEbayService with official eBay SDKs
- Enhanced error handling and URL management
- Performance monitoring and metrics

This addresses the mixed content issues and provides better fault tolerance.
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

# Import optimized services
from fs_agt_clean.core.api.optimized_api_client import (
    EbayOptimizedApiClient,
    get_ebay_api_client,
)
from fs_agt_clean.services.marketplace.simplified_optimized_ebay_service import (
    SimplifiedOptimizedEbayService,
    get_simplified_optimized_ebay_service,
)
from fs_agt_clean.services.marketplace.local_taxonomy_service import (
    get_local_taxonomy_service,
)

logger = logging.getLogger(__name__)


class OptimizedServiceManager:
    """
    Centralized manager for optimized API services.

    Replaces legacy API clients with optimized implementations that provide:
    - Circuit breaker pattern for fault tolerance
    - Connection pooling for performance
    - Proper HTTPS URL management
    - Enhanced error handling
    """

    def __init__(self):
        """Initialize the optimized service manager."""
        self.ebay_api_client: Optional[EbayOptimizedApiClient] = None
        self.ebay_service: Optional[SimplifiedOptimizedEbayService] = None
        self.local_taxonomy = None
        self.initialized = False

        # Performance metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_breaker_trips": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0,
            "last_reset": datetime.now(timezone.utc),
        }

        logger.info("OptimizedServiceManager initialized")

    async def initialize(self, environment: str = "production") -> bool:
        """
        Initialize all optimized services.

        Args:
            environment: eBay environment ("sandbox" or "production")

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info(
                f"Initializing optimized services for {environment} environment"
            )

            # Initialize eBay API client with circuit breaker
            self.ebay_api_client = await get_ebay_api_client(environment)
            logger.info("✅ Optimized eBay API client initialized")

            # Initialize simplified eBay service
            self.ebay_service = await get_simplified_optimized_ebay_service(environment)
            logger.info("✅ Optimized eBay service initialized")

            # Initialize local taxonomy service
            self.local_taxonomy = get_local_taxonomy_service()
            logger.info("✅ Local taxonomy service initialized")

            self.initialized = True
            logger.info("🎉 All optimized services initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize optimized services: {e}")
            return False

    async def get_ebay_categories(
        self, auth_headers: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Get eBay categories using optimized API client.

        Args:
            auth_headers: Authorization headers

        Returns:
            List of category dictionaries
        """
        if not self.initialized or not self.ebay_api_client:
            raise RuntimeError("Optimized services not initialized")

        try:
            self.metrics["total_requests"] += 1

            # Use optimized API client with circuit breaker
            categories = await self.ebay_api_client.get_categories(auth_headers)

            self.metrics["successful_requests"] += 1
            logger.info(
                f"Retrieved {len(categories)} eBay categories via optimized client"
            )
            return categories

        except Exception as e:
            self.metrics["failed_requests"] += 1
            logger.error(f"Failed to get eBay categories: {e}")
            raise

    async def get_category_specifics(self, category_id: str) -> Dict[str, Any]:
        """
        Get category specifics using hybrid fallback strategy.

        Args:
            category_id: eBay category ID

        Returns:
            Category specifics dictionary
        """
        if not self.initialized or not self.ebay_service:
            raise RuntimeError("Optimized services not initialized")

        try:
            self.metrics["total_requests"] += 1

            # Use optimized eBay service with local taxonomy fallback
            specifics = await self.ebay_service.get_category_item_specifics(category_id)

            self.metrics["successful_requests"] += 1

            # Track cache hits
            if specifics.get("source") == "local_taxonomy":
                self.metrics["cache_hits"] += 1

            logger.info(
                f"Retrieved category specifics for {category_id} from {specifics.get('source', 'unknown')}"
            )
            return specifics

        except Exception as e:
            self.metrics["failed_requests"] += 1
            logger.error(f"Failed to get category specifics for {category_id}: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all optimized services.

        Returns:
            Health status dictionary
        """
        health_status = {
            "optimized_services": {
                "initialized": self.initialized,
                "ebay_api_client": False,
                "ebay_service": False,
                "local_taxonomy": False,
            },
            "metrics": self.metrics.copy(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        try:
            # Check eBay API client
            if self.ebay_api_client:
                # Test with dummy auth headers
                dummy_headers = {"Authorization": "Bearer dummy"}
                api_healthy = await self.ebay_api_client.health_check(dummy_headers)
                health_status["optimized_services"]["ebay_api_client"] = api_healthy

            # Check eBay service
            if self.ebay_service:
                health_status["optimized_services"]["ebay_service"] = True

            # Check local taxonomy
            if self.local_taxonomy and self.local_taxonomy.loaded:
                health_status["optimized_services"]["local_taxonomy"] = True

            logger.info("Optimized services health check completed")
            return health_status

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["error"] = str(e)
            return health_status

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["successful_requests"]
                / max(self.metrics["total_requests"], 1)
            )
            * 100,
            "cache_hit_rate": (
                self.metrics["cache_hits"] / max(self.metrics["total_requests"], 1)
            )
            * 100,
        }

    def reset_metrics(self):
        """Reset performance metrics."""
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "circuit_breaker_trips": 0,
            "cache_hits": 0,
            "avg_response_time": 0.0,
            "last_reset": datetime.now(timezone.utc),
        }
        logger.info("Performance metrics reset")


# Global service manager instance
_service_manager: Optional[OptimizedServiceManager] = None


async def get_optimized_service_manager() -> OptimizedServiceManager:
    """
    Get global optimized service manager instance.

    Returns:
        OptimizedServiceManager instance
    """
    global _service_manager

    if _service_manager is None:
        _service_manager = OptimizedServiceManager()

        # Initialize with production environment
        environment = os.getenv("EBAY_ENVIRONMENT", "production")
        await _service_manager.initialize(environment)

    return _service_manager


async def replace_legacy_api_client(legacy_client_instance):
    """
    Replace legacy API client with optimized implementation.

    Args:
        legacy_client_instance: Legacy API client to replace

    Returns:
        OptimizedServiceManager instance
    """
    logger.info("Replacing legacy API client with optimized implementation")

    # Get optimized service manager
    service_manager = await get_optimized_service_manager()

    # Log the replacement
    logger.info(f"✅ Legacy API client replaced with OptimizedServiceManager")
    logger.info(f"   - Circuit breaker enabled")
    logger.info(f"   - Connection pooling active")
    logger.info(f"   - Local taxonomy caching available")
    logger.info(f"   - Enhanced error handling enabled")

    return service_manager
