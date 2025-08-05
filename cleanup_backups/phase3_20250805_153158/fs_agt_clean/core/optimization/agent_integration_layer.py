"""
Agent Integration Layer for FlipSync Phase 1.5
==============================================

Production integration layer that connects the 4 autonomous agents
(MarketAgent, ContentAgent, ExecutiveAgent, LogisticsAgent) with the
optimized shared cache and batch operations systems.

Features:
- Seamless integration with existing agent architectures
- Automatic cache lookup and storage for product data
- Batch operation coordination across agents
- Performance monitoring and optimization
- Autonomous architecture compliance (zero LLM dependencies)
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# FlipSync imports
from fs_agt_clean.core.optimization.production_shared_cache import (
    get_production_shared_cache,
    ProductionSharedProductCache
)
from fs_agt_clean.core.optimization.batch_ebay_operations import (
    BatchEbayOperations,
    BatchOperationType
)
from fs_agt_clean.core.data.standardized_product_data import (
    StandardizedProductData,
    MarketAgentData,
    ContentAgentData,
    ExecutiveAgentData,
    LogisticsAgentData,
    ProductIdentifier,
    ProductIdentifierType
)
from fs_agt_clean.agents.market.ebay_client import eBayClient

logger = logging.getLogger(__name__)

class AgentCacheIntegration:
    """
    Integration layer for connecting agents with the production shared cache.
    
    Provides optimized data access patterns for all 4 autonomous agents
    while maintaining their existing interfaces and decision-making autonomy.
    """
    
    def __init__(self):
        """Initialize agent cache integration."""
        self.cache: Optional[ProductionSharedProductCache] = None
        self.batch_operations: Optional[BatchEbayOperations] = None
        self.ebay_client: Optional[eBayClient] = None
        self._initialized = False
        
        # Performance tracking
        self.integration_metrics = {
            "cache_hits": 0,
            "cache_misses": 0,
            "batch_operations": 0,
            "agent_requests": 0,
            "optimization_savings_ms": 0.0
        }
        
        logger.info("AgentCacheIntegration initialized")
    
    async def initialize(self) -> bool:
        """Initialize cache and batch operations."""
        if self._initialized:
            return True
        
        try:
            # Initialize production cache
            self.cache = await get_production_shared_cache()
            
            # Initialize eBay client
            import os
            self.ebay_client = eBayClient(
                client_id=os.getenv('EBAY_CLIENT_ID'),
                client_secret=os.getenv('EBAY_CLIENT_SECRET'),
                environment=os.getenv('EBAY_ENVIRONMENT', 'sandbox')
            )
            
            # Initialize batch operations
            self.batch_operations = BatchEbayOperations(
                ebay_client=self.ebay_client,
                max_batch_size=20,
                max_concurrent_batches=3
            )
            
            self._initialized = True
            logger.info("Agent cache integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent cache integration: {e}")
            return False
    
    async def get_market_data_optimized(self, 
                                      product_identifiers: List[ProductIdentifier],
                                      agent_id: str = "market_agent") -> Optional[MarketAgentData]:
        """
        Get optimized market data for MarketAgent.
        
        Args:
            product_identifiers: Product identifiers for cache lookup
            agent_id: Agent identifier for metrics
            
        Returns:
            MarketAgentData if available, None otherwise
        """
        start_time = time.perf_counter()
        self.integration_metrics["agent_requests"] += 1
        
        try:
            # Try cache first
            cached_data = await self.cache.get_product_data(
                product_identifiers, agent_type=agent_id
            )
            
            if cached_data and cached_data.market_data:
                # Extract market-specific data
                market_data = self._extract_market_data_from_cache(cached_data)
                
                lookup_time = (time.perf_counter() - start_time) * 1000
                self.integration_metrics["cache_hits"] += 1
                self.integration_metrics["optimization_savings_ms"] += lookup_time
                
                logger.debug(f"Market data cache HIT for {agent_id}: {lookup_time:.1f}ms")
                return market_data
            
            # Cache miss - need to fetch data
            self.integration_metrics["cache_misses"] += 1
            logger.debug(f"Market data cache MISS for {agent_id}")
            return None
            
        except Exception as e:
            logger.error(f"Market data optimization failed: {e}")
            return None
    
    async def get_content_data_optimized(self, 
                                       product_identifiers: List[ProductIdentifier],
                                       agent_id: str = "content_agent") -> Optional[ContentAgentData]:
        """
        Get optimized content data for ContentAgent.
        
        Args:
            product_identifiers: Product identifiers for cache lookup
            agent_id: Agent identifier for metrics
            
        Returns:
            ContentAgentData if available, None otherwise
        """
        start_time = time.perf_counter()
        self.integration_metrics["agent_requests"] += 1
        
        try:
            # Try cache first
            cached_data = await self.cache.get_product_data(
                product_identifiers, agent_type=agent_id
            )
            
            if cached_data and cached_data.content_data:
                # Extract content-specific data
                content_data = self._extract_content_data_from_cache(cached_data)
                
                lookup_time = (time.perf_counter() - start_time) * 1000
                self.integration_metrics["cache_hits"] += 1
                self.integration_metrics["optimization_savings_ms"] += lookup_time
                
                logger.debug(f"Content data cache HIT for {agent_id}: {lookup_time:.1f}ms")
                return content_data
            
            # Cache miss
            self.integration_metrics["cache_misses"] += 1
            logger.debug(f"Content data cache MISS for {agent_id}")
            return None
            
        except Exception as e:
            logger.error(f"Content data optimization failed: {e}")
            return None
    
    async def get_executive_data_optimized(self, 
                                         product_identifiers: List[ProductIdentifier],
                                         agent_id: str = "executive_agent") -> Optional[ExecutiveAgentData]:
        """
        Get optimized executive data for ExecutiveAgent.
        
        Args:
            product_identifiers: Product identifiers for cache lookup
            agent_id: Agent identifier for metrics
            
        Returns:
            ExecutiveAgentData if available, None otherwise
        """
        start_time = time.perf_counter()
        self.integration_metrics["agent_requests"] += 1
        
        try:
            # Try cache first
            cached_data = await self.cache.get_product_data(
                product_identifiers, agent_type=agent_id
            )
            
            if cached_data and cached_data.decision_data:
                # Extract executive-specific data
                executive_data = self._extract_executive_data_from_cache(cached_data)
                
                lookup_time = (time.perf_counter() - start_time) * 1000
                self.integration_metrics["cache_hits"] += 1
                self.integration_metrics["optimization_savings_ms"] += lookup_time
                
                logger.debug(f"Executive data cache HIT for {agent_id}: {lookup_time:.1f}ms")
                return executive_data
            
            # Cache miss
            self.integration_metrics["cache_misses"] += 1
            logger.debug(f"Executive data cache MISS for {agent_id}")
            return None
            
        except Exception as e:
            logger.error(f"Executive data optimization failed: {e}")
            return None
    
    async def get_logistics_data_optimized(self, 
                                         product_identifiers: List[ProductIdentifier],
                                         agent_id: str = "logistics_agent") -> Optional[LogisticsAgentData]:
        """
        Get optimized logistics data for LogisticsAgent.
        
        Args:
            product_identifiers: Product identifiers for cache lookup
            agent_id: Agent identifier for metrics
            
        Returns:
            LogisticsAgentData if available, None otherwise
        """
        start_time = time.perf_counter()
        self.integration_metrics["agent_requests"] += 1
        
        try:
            # Try cache first
            cached_data = await self.cache.get_product_data(
                product_identifiers, agent_type=agent_id
            )
            
            if cached_data and cached_data.logistics_data:
                # Extract logistics-specific data
                logistics_data = self._extract_logistics_data_from_cache(cached_data)
                
                lookup_time = (time.perf_counter() - start_time) * 1000
                self.integration_metrics["cache_hits"] += 1
                self.integration_metrics["optimization_savings_ms"] += lookup_time
                
                logger.debug(f"Logistics data cache HIT for {agent_id}: {lookup_time:.1f}ms")
                return logistics_data
            
            # Cache miss
            self.integration_metrics["cache_misses"] += 1
            logger.debug(f"Logistics data cache MISS for {agent_id}")
            return None
            
        except Exception as e:
            logger.error(f"Logistics data optimization failed: {e}")
            return None
    
    async def store_standardized_data(self, 
                                    standardized_data: StandardizedProductData) -> bool:
        """
        Store standardized product data in the shared cache.
        
        Args:
            standardized_data: Standardized product data to cache
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Convert to comprehensive product data
            comprehensive_data = standardized_data.to_comprehensive_product_data()
            
            # Store in cache
            success = await self.cache.store_product_data(
                standardized_data.identifiers,
                comprehensive_data
            )
            
            if success:
                logger.debug(f"Stored standardized data for product: {standardized_data.product_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to store standardized data: {e}")
            return False
    
    async def batch_market_analysis(self, 
                                  product_queries: List[str],
                                  agent_id: str = "market_agent") -> List[str]:
        """
        Submit batch market analysis requests.
        
        Args:
            product_queries: List of product search queries
            agent_id: Agent identifier for metrics
            
        Returns:
            List of request IDs for tracking
        """
        try:
            request_ids = []
            
            for query in product_queries:
                request_id = await self.batch_operations.add_product_search_request(
                    search_query=query,
                    category_id="58058",  # Electronics default
                    limit=10,
                    priority=1
                )
                request_ids.append(request_id)
            
            self.integration_metrics["batch_operations"] += 1
            logger.debug(f"Submitted {len(product_queries)} batch market analysis requests")
            
            return request_ids
            
        except Exception as e:
            logger.error(f"Batch market analysis failed: {e}")
            return []
    
    async def process_pending_batches(self) -> Dict[str, Any]:
        """Process all pending batch operations."""
        try:
            batch_results = await self.batch_operations.process_pending_batches(
                force_process=True
            )
            
            # Extract performance metrics
            performance_metrics = self.batch_operations.get_performance_metrics()
            
            return {
                "batch_results": batch_results,
                "performance_metrics": performance_metrics.__dict__,
                "batches_processed": len(batch_results)
            }
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return {"error": str(e)}
    
    def _extract_market_data_from_cache(self, cached_data) -> MarketAgentData:
        """Extract MarketAgentData from cached comprehensive data."""
        try:
            from fs_agt_clean.core.data.standardized_product_data import ProductCategory
            
            market_data_dict = cached_data.market_data
            
            # Reconstruct MarketAgentData
            return MarketAgentData(
                product_identifiers=cached_data.identifiers,
                search_keywords=market_data_dict.get("search_keywords", []),
                category=ProductCategory(market_data_dict.get("category", "general")),
                estimated_price_range=tuple(market_data_dict.get("price_range", [10.0, 100.0])),
                competitive_keywords=market_data_dict.get("search_keywords", [])[:5],
                market_category_id=market_data_dict.get("ebay_category_id"),
                brand=market_data_dict.get("brand"),
                model=market_data_dict.get("model")
            )
            
        except Exception as e:
            logger.error(f"Failed to extract market data from cache: {e}")
            # Return minimal valid data
            from fs_agt_clean.core.data.standardized_product_data import ProductCategory
            return MarketAgentData(
                product_identifiers=cached_data.identifiers,
                search_keywords=["product"],
                category=ProductCategory.GENERAL,
                estimated_price_range=(10.0, 100.0),
                competitive_keywords=["product"]
            )
    
    def _extract_content_data_from_cache(self, cached_data) -> ContentAgentData:
        """Extract ContentAgentData from cached comprehensive data."""
        try:
            from fs_agt_clean.core.data.standardized_product_data import ProductCategory
            
            content_data_dict = cached_data.content_data
            
            # Reconstruct ContentAgentData
            return ContentAgentData(
                title_keywords=content_data_dict.get("title_keywords", []),
                description_text=content_data_dict.get("description_text", []),
                category=ProductCategory(content_data_dict.get("category", "general")),
                features=content_data_dict.get("features", []),
                specifications=content_data_dict.get("specifications", {}),
                seo_keywords=content_data_dict.get("seo_keywords", []),
                quality_indicators=content_data_dict.get("quality_indicators", []),
                brand=content_data_dict.get("brand"),
                model=content_data_dict.get("model")
            )
            
        except Exception as e:
            logger.error(f"Failed to extract content data from cache: {e}")
            # Return minimal valid data
            from fs_agt_clean.core.data.standardized_product_data import ProductCategory
            return ContentAgentData(
                title_keywords=["product"],
                description_text=["Quality product"],
                category=ProductCategory.GENERAL,
                features=[],
                specifications={},
                seo_keywords=["product"],
                quality_indicators=[]
            )
    
    def _extract_executive_data_from_cache(self, cached_data) -> ExecutiveAgentData:
        """Extract ExecutiveAgentData from cached comprehensive data."""
        try:
            from fs_agt_clean.core.data.standardized_product_data import ProductCategory
            
            decision_data_dict = cached_data.decision_data
            confidence_metrics = cached_data.confidence_metrics
            strategic_data_dict = cached_data.strategic_data
            
            # Reconstruct ExecutiveAgentData
            return ExecutiveAgentData(
                confidence_score=confidence_metrics.get("overall_quality", 0.5),
                quality_metrics=confidence_metrics,
                risk_factors=decision_data_dict.get("risk_factors", []),
                decision_factors=decision_data_dict.get("decision_context", {}),
                strategic_category=ProductCategory(strategic_data_dict.get("category", "general")),
                investment_indicators=strategic_data_dict.get("investment_indicators", {}),
                processing_metadata=decision_data_dict.get("processing_metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Failed to extract executive data from cache: {e}")
            # Return minimal valid data
            from fs_agt_clean.core.data.standardized_product_data import ProductCategory
            return ExecutiveAgentData(
                confidence_score=0.5,
                quality_metrics={},
                risk_factors=[],
                decision_factors={},
                strategic_category=ProductCategory.GENERAL,
                investment_indicators={},
                processing_metadata={}
            )
    
    def _extract_logistics_data_from_cache(self, cached_data) -> LogisticsAgentData:
        """Extract LogisticsAgentData from cached comprehensive data."""
        try:
            from fs_agt_clean.core.data.standardized_product_data import ProductDimensions
            
            logistics_data_dict = cached_data.logistics_data
            shipping_data_dict = cached_data.shipping_data
            dimensions_data_dict = cached_data.dimensions_data
            
            # Reconstruct dimensions
            dimensions = ProductDimensions(
                length=dimensions_data_dict.get("length", 8.0),
                width=dimensions_data_dict.get("width", 6.0),
                height=dimensions_data_dict.get("height", 4.0),
                weight=dimensions_data_dict.get("weight", 2.0)
            )
            
            # Reconstruct LogisticsAgentData
            return LogisticsAgentData(
                dimensions=dimensions,
                estimated_weight=shipping_data_dict.get("estimated_weight", 2.0),
                shipping_category=logistics_data_dict.get("shipping_category", "general"),
                handling_requirements=shipping_data_dict.get("handling_requirements", []),
                fragility_score=logistics_data_dict.get("fragility_score", 0.3),
                size_category=logistics_data_dict.get("size_category", "medium")
            )
            
        except Exception as e:
            logger.error(f"Failed to extract logistics data from cache: {e}")
            # Return minimal valid data
            from fs_agt_clean.core.data.standardized_product_data import ProductDimensions
            return LogisticsAgentData(
                dimensions=ProductDimensions(8.0, 6.0, 4.0, 2.0),
                estimated_weight=2.0,
                shipping_category="general",
                handling_requirements=[],
                fragility_score=0.3,
                size_category="medium"
            )
    
    def get_integration_metrics(self) -> Dict[str, Any]:
        """Get current integration performance metrics."""
        total_requests = self.integration_metrics["agent_requests"]
        cache_hits = self.integration_metrics["cache_hits"]
        
        hit_rate = cache_hits / total_requests if total_requests > 0 else 0.0
        avg_savings = self.integration_metrics["optimization_savings_ms"] / cache_hits if cache_hits > 0 else 0.0
        
        return {
            **self.integration_metrics,
            "hit_rate": hit_rate,
            "average_optimization_savings_ms": avg_savings
        }

# Global integration instance
_agent_integration_instance: Optional[AgentCacheIntegration] = None

async def get_agent_integration() -> AgentCacheIntegration:
    """Get global agent integration instance."""
    global _agent_integration_instance
    if _agent_integration_instance is None:
        _agent_integration_instance = AgentCacheIntegration()
        await _agent_integration_instance.initialize()
    return _agent_integration_instance

# Export main components
__all__ = [
    "AgentCacheIntegration",
    "get_agent_integration"
]
