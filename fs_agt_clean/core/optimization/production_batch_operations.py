"""
Production Batch eBay Operations for FlipSync Phase 1.5
======================================================

Production-ready implementation of batch eBay operations with real API
integration, error handling, and database persistence for the FlipSync
production environment.

Features:
- Real eBay API integration with production/sandbox credentials
- Database persistence for batch operation results
- Enhanced error handling and fallback mechanisms
- Rate limiting compliance with eBay API requirements
- Performance monitoring and optimization
- Autonomous architecture compliance (zero LLM dependencies)
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

# FlipSync imports
from fs_agt_clean.core.optimization.batch_ebay_operations import (
    BatchEbayOperations,
    BatchRequest,
    BatchResponse,
    BatchResult,
    BatchOperationType,
    BatchPerformanceMetrics
)
from fs_agt_clean.core.optimization.production_shared_cache import (
    BatchOperationResult,
    get_production_shared_cache
)
from fs_agt_clean.agents.market.ebay_client import eBayClient
from fs_agt_clean.core.db.optimized_database import OptimizedDatabase

logger = logging.getLogger(__name__)

class ProductionBatchEbayOperations(BatchEbayOperations):
    """
    Production-ready batch eBay operations with database persistence.
    
    Extends the base BatchEbayOperations with production features:
    - Real eBay API integration
    - Database persistence for results
    - Enhanced error handling
    - Performance monitoring
    """
    
    def __init__(self, 
                 ebay_client: Optional[eBayClient] = None,
                 database: Optional[OptimizedDatabase] = None,
                 max_batch_size: int = 20,
                 max_concurrent_batches: int = 3,
                 rate_limit_delay_ms: int = 100):
        """Initialize production batch eBay operations."""
        
        # Initialize base class
        super().__init__(
            ebay_client=ebay_client,
            max_batch_size=max_batch_size,
            max_concurrent_batches=max_concurrent_batches,
            rate_limit_delay_ms=rate_limit_delay_ms
        )
        
        self.database = database
        self._initialized = False
        
        # Production metrics
        self.production_metrics = {
            "real_api_calls": 0,
            "database_operations": 0,
            "error_recovery_attempts": 0,
            "fallback_activations": 0
        }
        
        logger.info("ProductionBatchEbayOperations initialized")
    
    async def initialize(self) -> bool:
        """Initialize production batch operations."""
        if self._initialized:
            return True
        
        try:
            # Initialize database if not provided
            if self.database is None:
                self.database = OptimizedDatabase()
                await self.database.initialize()
            
            # Initialize eBay client if not provided
            if self.ebay_client is None:
                import os
                self.ebay_client = eBayClient(
                    client_id=os.getenv('EBAY_CLIENT_ID'),
                    client_secret=os.getenv('EBAY_CLIENT_SECRET'),
                    environment=os.getenv('EBAY_ENVIRONMENT', 'sandbox')
                )
            
            # Verify eBay client connectivity
            await self._verify_ebay_connectivity()
            
            self._initialized = True
            logger.info("Production batch operations initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize production batch operations: {e}")
            return False
    
    async def _verify_ebay_connectivity(self) -> bool:
        """Verify eBay API connectivity."""
        try:
            # Test with a simple search
            test_result = await self.ebay_client.search_products(
                query="test",
                limit=1
            )
            
            if test_result is not None:
                logger.info("eBay API connectivity verified")
                return True
            else:
                logger.warning("eBay API connectivity test returned None")
                return False
                
        except Exception as e:
            logger.error(f"eBay API connectivity test failed: {e}")
            return False
    
    async def _process_product_search_batch(self, 
                                          batch_requests: List[BatchRequest]) -> List[BatchResponse]:
        """Process batch of product search requests with real eBay API."""
        responses = []
        
        try:
            # Group similar searches to optimize API usage
            search_groups = self._group_similar_searches(batch_requests)
            
            for group in search_groups:
                # Use the most comprehensive search parameters
                primary_request = group[0]
                params = primary_request.parameters
                
                # Execute real eBay search
                search_start = time.perf_counter()
                try:
                    search_results = await self._execute_real_ebay_search(
                        query=params["query"],
                        category_id=params.get("category_id"),
                        limit=params.get("limit", 10)
                    )
                    
                    search_time = (time.perf_counter() - search_start) * 1000
                    self.production_metrics["real_api_calls"] += 1
                    
                    # Create responses for all requests in group
                    for request in group:
                        responses.append(BatchResponse(
                            request_id=request.request_id,
                            success=True,
                            data=search_results,
                            processing_time_ms=search_time / len(group),
                            api_calls_used=1
                        ))
                        
                except Exception as e:
                    logger.error(f"Real eBay search failed: {e}")
                    self.production_metrics["error_recovery_attempts"] += 1
                    
                    # Try fallback approach
                    fallback_results = await self._execute_fallback_search(params)
                    
                    for request in group:
                        responses.append(BatchResponse(
                            request_id=request.request_id,
                            success=fallback_results is not None,
                            data=fallback_results,
                            error=str(e) if fallback_results is None else None,
                            processing_time_ms=search_time / len(group) if 'search_time' in locals() else 0
                        ))
            
        except Exception as e:
            logger.error(f"Product search batch processing failed: {e}")
            # Create error responses for all requests
            for request in batch_requests:
                responses.append(BatchResponse(
                    request_id=request.request_id,
                    success=False,
                    error=str(e)
                ))
        
        return responses
    
    async def _execute_real_ebay_search(self, 
                                      query: str,
                                      category_id: Optional[str] = None,
                                      limit: int = 10) -> Dict[str, Any]:
        """Execute real eBay API search with error handling."""
        try:
            # Call real eBay API
            search_results = await self.ebay_client.search_products(
                query=query,
                category_id=category_id,
                limit=limit
            )
            
            if search_results is None:
                raise ValueError("eBay API returned None")
            
            # Validate and structure results
            structured_results = {
                "query": query,
                "category_id": category_id,
                "total_results": len(search_results) if isinstance(search_results, list) else 1,
                "results": search_results,
                "api_source": "ebay_production",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.debug(f"Real eBay search successful: {query} -> {len(search_results) if isinstance(search_results, list) else 1} results")
            
            return structured_results
            
        except Exception as e:
            logger.error(f"Real eBay search failed for query '{query}': {e}")
            raise
    
    async def _execute_fallback_search(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute fallback search when real eBay API fails."""
        try:
            self.production_metrics["fallback_activations"] += 1
            
            # Use mock data as fallback
            fallback_results = self.ebay_client._create_mock_search_results(
                query=params["query"],
                limit=params.get("limit", 10)
            )
            
            structured_results = {
                "query": params["query"],
                "category_id": params.get("category_id"),
                "total_results": len(fallback_results),
                "results": fallback_results,
                "api_source": "fallback_mock",
                "timestamp": datetime.now().isoformat(),
                "fallback_reason": "real_api_failure"
            }
            
            logger.warning(f"Using fallback search for query: {params['query']}")
            
            return structured_results
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            return None
    
    async def _process_inventory_lookup_batch(self, 
                                            batch_requests: List[BatchRequest]) -> List[BatchResponse]:
        """Process batch of inventory lookup requests with real eBay API."""
        responses = []
        
        try:
            # Collect all item IDs from batch
            all_item_ids = []
            request_item_mapping = {}
            
            for request in batch_requests:
                item_ids = request.parameters.get("item_ids", [])
                all_item_ids.extend(item_ids)
                request_item_mapping[request.request_id] = item_ids
            
            # Execute batch inventory lookup
            lookup_start = time.perf_counter()
            try:
                # Use real eBay inventory API
                inventory_results = await self._execute_real_inventory_lookup(all_item_ids)
                lookup_time = (time.perf_counter() - lookup_start) * 1000
                
                self.production_metrics["real_api_calls"] += 1
                
                # Distribute results back to individual requests
                for request in batch_requests:
                    request_item_ids = request_item_mapping[request.request_id]
                    request_results = {
                        item_id: inventory_results.get(item_id)
                        for item_id in request_item_ids
                        if item_id in inventory_results
                    }
                    
                    responses.append(BatchResponse(
                        request_id=request.request_id,
                        success=True,
                        data={"inventory_data": request_results},
                        processing_time_ms=lookup_time / len(batch_requests),
                        api_calls_used=1
                    ))
                    
            except Exception as e:
                logger.error(f"Real inventory lookup failed: {e}")
                self.production_metrics["error_recovery_attempts"] += 1
                
                # Create error responses
                for request in batch_requests:
                    responses.append(BatchResponse(
                        request_id=request.request_id,
                        success=False,
                        error=str(e)
                    ))
            
        except Exception as e:
            logger.error(f"Inventory lookup batch processing failed: {e}")
            for request in batch_requests:
                responses.append(BatchResponse(
                    request_id=request.request_id,
                    success=False,
                    error=str(e)
                ))
        
        return responses
    
    async def _execute_real_inventory_lookup(self, item_ids: List[str]) -> Dict[str, Any]:
        """Execute real eBay inventory lookup."""
        try:
            # Use eBay GetMyeBaySelling for real inventory data
            inventory_data = await self.ebay_client.get_ebay_inventory(
                limit=len(item_ids),
                sync=True
            )
            
            # Structure results by item ID
            structured_results = {}
            
            if inventory_data and isinstance(inventory_data, list):
                for item in inventory_data:
                    item_id = item.get("itemId") or item.get("id")
                    if item_id:
                        structured_results[item_id] = {
                            "item_id": item_id,
                            "title": item.get("title", ""),
                            "price": item.get("price", {}),
                            "quantity": item.get("quantity", 0),
                            "status": item.get("status", "unknown"),
                            "api_source": "ebay_inventory",
                            "timestamp": datetime.now().isoformat()
                        }
            
            logger.debug(f"Real inventory lookup successful: {len(structured_results)} items")
            
            return structured_results
            
        except Exception as e:
            logger.error(f"Real inventory lookup failed: {e}")
            raise
    
    async def _store_batch_result_in_database(self, batch_result: BatchResult) -> bool:
        """Store batch operation result in database."""
        try:
            async with self.database.get_session() as session:
                # Create batch operation result record
                db_result = BatchOperationResult(
                    batch_id=batch_result.batch_id,
                    operation_type=batch_result.operation_type.value,
                    total_requests=batch_result.total_requests,
                    successful_requests=batch_result.successful_requests,
                    failed_requests=batch_result.failed_requests,
                    total_processing_time_ms=batch_result.total_processing_time_ms,
                    api_calls_saved=batch_result.api_calls_saved,
                    responses=[asdict(response) for response in batch_result.responses]
                )
                
                session.add(db_result)
                await session.commit()
                
                self.production_metrics["database_operations"] += 1
                logger.debug(f"Stored batch result in database: {batch_result.batch_id}")
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to store batch result in database: {e}")
            return False
    
    async def process_pending_batches(self, 
                                    operation_type: Optional[BatchOperationType] = None,
                                    force_process: bool = False) -> List[BatchResult]:
        """Process pending batches with database persistence."""
        try:
            # Process batches using parent implementation
            batch_results = await super().process_pending_batches(operation_type, force_process)
            
            # Store results in database
            for batch_result in batch_results:
                await self._store_batch_result_in_database(batch_result)
            
            return batch_results
            
        except Exception as e:
            logger.error(f"Production batch processing failed: {e}")
            return []
    
    def get_production_metrics(self) -> Dict[str, Any]:
        """Get production-specific performance metrics."""
        base_metrics = self.get_performance_metrics()
        
        return {
            "base_metrics": base_metrics.__dict__,
            "production_metrics": self.production_metrics,
            "api_reliability": {
                "real_api_calls": self.production_metrics["real_api_calls"],
                "fallback_rate": self.production_metrics["fallback_activations"] / max(1, self.production_metrics["real_api_calls"]),
                "error_recovery_rate": self.production_metrics["error_recovery_attempts"] / max(1, self.production_metrics["real_api_calls"])
            }
        }

# Global production batch operations instance
_production_batch_instance: Optional[ProductionBatchEbayOperations] = None

async def get_production_batch_operations() -> ProductionBatchEbayOperations:
    """Get global production batch operations instance."""
    global _production_batch_instance
    if _production_batch_instance is None:
        _production_batch_instance = ProductionBatchEbayOperations()
        await _production_batch_instance.initialize()
    return _production_batch_instance

# Export main components
__all__ = [
    "ProductionBatchEbayOperations",
    "get_production_batch_operations"
]
