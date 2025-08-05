#!/usr/bin/env python3
"""
Optimized eBay Service using official eBay SDKs and OAuth client.

This service replaces the custom ProductionEbayService with official eBay SDKs:
- eBay Python SDK (ebaysdk) for API calls
- eBay OAuth Python Client for authentication
- Local taxonomy data for performance optimization
"""

import asyncio
import logging
import os
import time
from typing import Any, Dict, Optional, List
import yaml

# Local taxonomy service
from .local_taxonomy_service import get_local_taxonomy_service

# TSV-enhanced taxonomy service
from .tsv_enhanced_taxonomy_service import get_tsv_enhanced_taxonomy_service

# Standard library imports for simplified implementation
import requests
import json

# Optimized API client
from optimized_api_client import get_ebay_api_client

logger = logging.getLogger(__name__)


class OptimizedEbayService:
    """Optimized eBay service using official SDKs and local taxonomy data."""

    def __init__(self, environment: str = "sandbox"):
        """Initialize the optimized eBay service.

        Args:
            environment: eBay environment ("sandbox" or "production")
        """
        self.environment = environment
        self.config_file = "ebay-config.yaml"

        # Performance tracking
        self.performance_metrics = {
            "api_calls": 0,
            "cache_hits": 0,
            "local_taxonomy_hits": 0,
            "total_requests": 0,
            "avg_response_time": 0.0,
        }

        # Initialize components
        self._load_configuration()
        self._initialize_oauth()
        self._initialize_trading_api()
        self._initialize_local_taxonomy()
        self._initialize_api_client()

        logger.info(f"Initialized OptimizedEbayService for {environment} environment")

    def _load_configuration(self):
        """Load eBay configuration from YAML file."""
        try:
            with open(self.config_file, "r") as f:
                self.config = yaml.safe_load(f)
            logger.info("eBay configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load eBay configuration: {e}")
            raise

    def _initialize_oauth(self):
        """Initialize eBay OAuth client."""
        try:
            # Initialize simple OAuth client
            self.oauth_client = get_oauth_client(self.config_file, self.environment)

            # Test token retrieval
            self.app_token = self.oauth_client.get_application_token()
            logger.info("eBay OAuth client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OAuth client: {e}")
            # Fallback to None - will be handled in API calls
            self.oauth_client = None
            self.app_token = None

    def _initialize_trading_api(self):
        """Initialize eBay Trading API connection."""
        try:
            # Determine domain based on environment
            domain = (
                f'api.{"sandbox." if self.environment == "sandbox" else ""}ebay.com'
            )

            # Initialize Trading API with config file
            self.trading_api = Trading(
                domain=domain, config_file=self.config_file, https=True
            )
            logger.info("eBay Trading API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Trading API: {e}")
            self.trading_api = None

    def _initialize_local_taxonomy(self):
        """Initialize local taxonomy data for fast lookups."""
        try:
            # Use TSV-enhanced taxonomy service for better performance
            self.local_taxonomy = get_tsv_enhanced_taxonomy_service()
            logger.info("TSV-enhanced taxonomy service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TSV taxonomy service: {e}")
            # Fallback to original CSV service
            try:
                self.local_taxonomy = get_local_taxonomy_service()
                logger.info("Fallback to CSV taxonomy service successful")
            except Exception as e2:
                logger.error(f"Failed to initialize any taxonomy service: {e2}")
                self.local_taxonomy = None

    def _initialize_api_client(self):
        """Initialize optimized API client."""
        try:
            # Note: API client will be initialized async when needed
            self.api_client = None
            logger.info("API client initialization deferred to async context")
        except Exception as e:
            logger.error(f"Failed to initialize API client: {e}")
            self.api_client = None

    async def get_category_item_specifics(self, category_id: str) -> Dict[str, Any]:
        """Get category-specific item specifics with hybrid fallback strategy.

        Strategy:
        1. Try local taxonomy data (instant)
        2. Fallback to eBay SDK API call (optimized)
        3. Final fallback to generated defaults

        Args:
            category_id: eBay category ID

        Returns:
            Dictionary containing category aspects and item specifics
        """
        start_time = time.perf_counter()
        self.performance_metrics["total_requests"] += 1

        try:
            # Step 1: Try local taxonomy data (Week 2 implementation)
            if self.local_taxonomy:
                local_data = await self._get_from_local_taxonomy(category_id)
                if local_data:
                    self.performance_metrics["local_taxonomy_hits"] += 1
                    self._update_performance_metrics(start_time)
                    return local_data

            # Step 2: Fallback to eBay SDK API call
            api_data = await self._get_from_ebay_api(category_id)
            if api_data:
                self.performance_metrics["api_calls"] += 1
                self._update_performance_metrics(start_time)
                return api_data

            # Step 3: Final fallback to generated defaults
            default_data = self._generate_default_aspects(category_id)
            self._update_performance_metrics(start_time)
            return default_data

        except Exception as e:
            logger.error(f"Error getting category specifics for {category_id}: {e}")
            # Return minimal default data
            self._update_performance_metrics(start_time)
            return self._generate_minimal_defaults(category_id)

    async def _get_from_local_taxonomy(
        self, category_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get category data from local taxonomy."""
        if not self.local_taxonomy:
            return None

        try:
            # Check if the taxonomy service has async methods
            if hasattr(self.local_taxonomy, "get_category_info"):
                if asyncio.iscoroutinefunction(self.local_taxonomy.get_category_info):
                    # TSV-enhanced service (async)
                    category_info = await self.local_taxonomy.get_category_info(
                        category_id
                    )
                else:
                    # Original CSV service (sync)
                    category_info = self.local_taxonomy.get_category_info(category_id)

                if category_info and self.local_taxonomy.is_data_fresh(category_info):
                    return category_info
            return None
        except Exception as e:
            logger.error(f"Error getting local taxonomy data for {category_id}: {e}")
            return None

    async def _get_from_ebay_api(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Get category specifics from eBay API using official SDK."""
        if not self.trading_api:
            logger.warning("Trading API not initialized")
            return None

        try:
            # Use eBay SDK to get category specifics
            response = self.trading_api.execute(
                "GetCategorySpecifics",
                {"CategoryID": category_id, "DetailLevel": "ReturnAll"},
            )

            # Process the response
            if response.reply.Ack in ["Success", "Warning"]:
                return self._process_api_response(response, category_id)
            else:
                logger.warning(
                    f"eBay API returned error for category {category_id}: {response.reply.Errors}"
                )
                return None

        except EbayConnectionError as e:
            logger.error(f"eBay API connection error for category {category_id}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error calling eBay API for category {category_id}: {e}"
            )
            return None

    def _process_api_response(self, response, category_id: str) -> Dict[str, Any]:
        """Process eBay API response into standardized format."""
        try:
            # Extract category specifics from response
            specifics = {}

            if (
                hasattr(response.reply, "CategorySpecifics")
                and response.reply.CategorySpecifics
            ):
                for specific in response.reply.CategorySpecifics:
                    if hasattr(specific, "NameRecommendation"):
                        for name_rec in specific.NameRecommendation:
                            name = name_rec.Name
                            specifics[name] = {
                                "required": getattr(name_rec, "Required", False),
                                "values": [],
                            }

                            # Extract recommended values
                            if hasattr(name_rec, "ValueRecommendation"):
                                for value_rec in name_rec.ValueRecommendation:
                                    specifics[name]["values"].append(value_rec.Value)

            return {
                "category_id": category_id,
                "specifics": specifics,
                "source": "ebay_api",
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.error(
                f"Error processing API response for category {category_id}: {e}"
            )
            return self._generate_default_aspects(category_id)

    def _generate_default_aspects(self, category_id: str) -> Dict[str, Any]:
        """Generate default item specifics based on category ID."""
        # Common aspects that apply to most categories
        default_aspects = {
            "Brand": {"required": True, "values": []},
            "Condition": {"required": True, "values": ["New", "Used", "Refurbished"]},
            "Color": {"required": False, "values": []},
            "Material": {"required": False, "values": []},
            "Size": {"required": False, "values": []},
        }

        # Category-specific enhancements (basic logic)
        if category_id == "9355":  # Cell Phones & Smartphones
            default_aspects.update(
                {
                    "Model": {"required": True, "values": []},
                    "Storage Capacity": {
                        "required": False,
                        "values": ["64GB", "128GB", "256GB", "512GB", "1TB"],
                    },
                    "Network": {
                        "required": False,
                        "values": ["Unlocked", "Verizon", "AT&T", "T-Mobile"],
                    },
                    "Operating System": {
                        "required": False,
                        "values": ["iOS", "Android"],
                    },
                }
            )

        return {
            "category_id": category_id,
            "specifics": default_aspects,
            "source": "generated_defaults",
            "timestamp": time.time(),
        }

    def _generate_minimal_defaults(self, category_id: str) -> Dict[str, Any]:
        """Generate minimal default data for error cases."""
        return {
            "category_id": category_id,
            "specifics": {
                "Brand": {"required": True, "values": []},
                "Condition": {"required": True, "values": ["New", "Used"]},
            },
            "source": "minimal_defaults",
            "timestamp": time.time(),
        }

    def _update_performance_metrics(self, start_time: float):
        """Update performance metrics."""
        response_time = time.perf_counter() - start_time

        # Update average response time
        total = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["avg_response_time"]
        self.performance_metrics["avg_response_time"] = (
            current_avg * (total - 1) + response_time
        ) / total

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        total_requests = self.performance_metrics["total_requests"]
        if total_requests == 0:
            return self.performance_metrics

        # Calculate percentages
        api_dependency = (self.performance_metrics["api_calls"] / total_requests) * 100
        local_hit_rate = (
            self.performance_metrics["local_taxonomy_hits"] / total_requests
        ) * 100

        return {
            **self.performance_metrics,
            "api_dependency_percentage": api_dependency,
            "local_taxonomy_hit_rate": local_hit_rate,
            "avg_response_time_ms": self.performance_metrics["avg_response_time"]
            * 1000,
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components."""
        health = {
            "oauth_client": self.app_token is not None,
            "trading_api": self.trading_api is not None,
            "local_taxonomy": self.local_taxonomy is not None,
            "config_loaded": hasattr(self, "config"),
            "environment": self.environment,
        }

        # Test API connectivity
        try:
            if self.trading_api:
                # Simple API test
                response = self.trading_api.execute("GeteBayOfficialTime")
                health["api_connectivity"] = response.reply.Ack == "Success"
            else:
                health["api_connectivity"] = False
        except Exception as e:
            health["api_connectivity"] = False
            health["api_error"] = str(e)

        return health


# Compatibility wrapper for existing code
class ProductionEbayService(OptimizedEbayService):
    """Compatibility wrapper to maintain existing interface."""

    def __init__(self, environment: str = "sandbox"):
        super().__init__(environment)
        logger.info(
            "Using OptimizedEbayService via ProductionEbayService compatibility wrapper"
        )
