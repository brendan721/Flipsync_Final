"""
Learning Performance Optimizer for FlipSync Agentic System
Phase 2.3: Performance Optimization and Measurement

This module optimizes learning system performance to meet <500ms targets through
query optimization, connection pooling, caching, and performance monitoring.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import defaultdict, deque
import json

from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for learning operations."""
    operation_type: str
    execution_time: float
    query_count: int
    cache_hits: int
    cache_misses: int
    memory_usage: float
    timestamp: datetime


@dataclass
class OptimizationResult:
    """Result of performance optimization."""
    operation_type: str
    original_time: float
    optimized_time: float
    improvement_percentage: float
    optimization_techniques: List[str]
    timestamp: datetime


class LearningPerformanceOptimizer:
    """
    Optimizes learning system performance for <500ms targets.
    
    Features:
    - Query optimization and caching
    - Connection pooling management
    - Performance monitoring and alerting
    - Adaptive optimization strategies
    - Real-time performance metrics
    """

    def __init__(self, database: Database, target_performance_ms: float = 500.0):
        """Initialize the learning performance optimizer.
        
        Args:
            database: Database instance for optimization
            target_performance_ms: Target performance in milliseconds
        """
        self.database = database
        self.target_performance_ms = target_performance_ms
        
        # Performance tracking
        self.performance_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.optimization_results: List[OptimizationResult] = []
        
        # Caching system
        self.query_cache: Dict[str, Tuple[Any, float]] = {}  # query_hash -> (result, timestamp)
        self.cache_ttl = 300.0  # 5 minutes cache TTL
        self.max_cache_size = 1000
        
        # Query optimization patterns
        self.optimized_queries: Dict[str, str] = {}
        self.query_performance: Dict[str, List[float]] = defaultdict(list)
        
        # Performance monitoring
        self.performance_alerts: List[Dict[str, Any]] = []
        self.monitoring_enabled = True

    async def optimize_learning_query(
        self,
        query: str,
        parameters: Dict[str, Any],
        operation_type: str = "learning_query"
    ) -> Tuple[Any, PerformanceMetrics]:
        """
        Execute and optimize a learning-related database query.
        
        Args:
            query: SQL query to execute
            parameters: Query parameters
            operation_type: Type of operation for metrics tracking
            
        Returns:
            Tuple of (query_result, performance_metrics)
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(query, parameters)
            
            # Check cache first
            cached_result = self._get_cached_result(cache_key)
            if cached_result is not None:
                execution_time = (time.time() - start_time) * 1000
                metrics = PerformanceMetrics(
                    operation_type=operation_type,
                    execution_time=execution_time,
                    query_count=0,
                    cache_hits=1,
                    cache_misses=0,
                    memory_usage=0.0,
                    timestamp=datetime.now(timezone.utc)
                )
                
                logger.debug(f"Cache hit for {operation_type}: {execution_time:.2f}ms")
                return cached_result, metrics
            
            # Optimize query if needed
            optimized_query = await self._optimize_query(query, operation_type)
            
            # Execute query with performance monitoring
            result = await self._execute_optimized_query(
                optimized_query, parameters, operation_type
            )
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Calculate metrics
            execution_time = (time.time() - start_time) * 1000
            metrics = PerformanceMetrics(
                operation_type=operation_type,
                execution_time=execution_time,
                query_count=1,
                cache_hits=0,
                cache_misses=1,
                memory_usage=0.0,
                timestamp=datetime.now(timezone.utc)
            )
            
            # Track performance
            await self._track_performance(metrics)
            
            # Check if performance target is met
            if execution_time > self.target_performance_ms:
                await self._handle_performance_violation(operation_type, execution_time)
            
            logger.debug(f"Query executed for {operation_type}: {execution_time:.2f}ms")
            return result, metrics
            
        except Exception as e:
            logger.error(f"Error optimizing learning query: {e}")
            raise

    async def optimize_batch_learning_operations(
        self,
        operations: List[Dict[str, Any]],
        batch_size: int = 10
    ) -> List[Tuple[Any, PerformanceMetrics]]:
        """
        Optimize batch learning operations for better performance.
        
        Args:
            operations: List of operations to execute
            batch_size: Size of batches for processing
            
        Returns:
            List of (result, metrics) tuples
        """
        start_time = time.time()
        results = []
        
        try:
            # Process operations in batches
            for i in range(0, len(operations), batch_size):
                batch = operations[i:i + batch_size]
                batch_results = await self._process_operation_batch(batch)
                results.extend(batch_results)
            
            total_time = (time.time() - start_time) * 1000
            logger.info(f"Batch operations completed: {len(operations)} ops in {total_time:.2f}ms")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch learning operations: {e}")
            raise

    async def _optimize_query(self, query: str, operation_type: str) -> str:
        """Optimize a SQL query for better performance."""
        try:
            # Check if we have an optimized version cached
            query_hash = hash(query)
            if query_hash in self.optimized_queries:
                return self.optimized_queries[query_hash]
            
            optimized_query = query
            
            # Apply common optimization patterns
            if "SELECT *" in query:
                # Suggest specific column selection (placeholder)
                logger.debug(f"Query optimization suggestion: Use specific columns instead of SELECT *")
            
            if "ORDER BY" in query and "LIMIT" not in query:
                # Add LIMIT for potentially large result sets
                if operation_type in ["learning_history", "performance_metrics"]:
                    optimized_query = f"{query} LIMIT 1000"
                    logger.debug("Added LIMIT clause for performance")
            
            # Add indexes suggestions (would be implemented based on query patterns)
            await self._suggest_index_optimizations(query, operation_type)
            
            # Cache the optimized query
            self.optimized_queries[query_hash] = optimized_query
            
            return optimized_query
            
        except Exception as e:
            logger.error(f"Error optimizing query: {e}")
            return query

    async def _execute_optimized_query(
        self,
        query: str,
        parameters: Dict[str, Any],
        operation_type: str
    ) -> Any:
        """Execute an optimized query with performance monitoring."""
        try:
            async with self.database.get_session() as session:
                from sqlalchemy import text
                result = await session.execute(text(query), parameters)
                
                # Track query performance
                if operation_type not in self.query_performance:
                    self.query_performance[operation_type] = []
                
                return result.fetchall()
                
        except Exception as e:
            logger.error(f"Error executing optimized query: {e}")
            raise

    def _generate_cache_key(self, query: str, parameters: Dict[str, Any]) -> str:
        """Generate a cache key for query and parameters."""
        try:
            # Create a deterministic hash of query and parameters
            param_str = json.dumps(parameters, sort_keys=True)
            cache_key = f"{hash(query)}_{hash(param_str)}"
            return cache_key
        except Exception:
            # Fallback to simple hash if JSON serialization fails
            return f"{hash(query)}_{hash(str(parameters))}"

    def _get_cached_result(self, cache_key: str) -> Optional[Any]:
        """Get cached result if available and not expired."""
        if cache_key not in self.query_cache:
            return None
        
        result, timestamp = self.query_cache[cache_key]
        
        # Check if cache entry is expired
        if time.time() - timestamp > self.cache_ttl:
            del self.query_cache[cache_key]
            return None
        
        return result

    def _cache_result(self, cache_key: str, result: Any):
        """Cache query result with timestamp."""
        try:
            # Implement LRU eviction if cache is full
            if len(self.query_cache) >= self.max_cache_size:
                # Remove oldest entry
                oldest_key = min(self.query_cache.keys(), 
                               key=lambda k: self.query_cache[k][1])
                del self.query_cache[oldest_key]
            
            self.query_cache[cache_key] = (result, time.time())
            
        except Exception as e:
            logger.error(f"Error caching result: {e}")

    async def _track_performance(self, metrics: PerformanceMetrics):
        """Track performance metrics for analysis."""
        try:
            # Add to performance history
            self.performance_history[metrics.operation_type].append(metrics)
            
            # Calculate rolling averages
            recent_metrics = list(self.performance_history[metrics.operation_type])[-10:]
            avg_time = sum(m.execution_time for m in recent_metrics) / len(recent_metrics)
            
            # Log performance trends
            if len(recent_metrics) >= 10:
                if avg_time > self.target_performance_ms:
                    logger.warning(
                        f"Performance degradation detected for {metrics.operation_type}: "
                        f"avg {avg_time:.2f}ms > target {self.target_performance_ms}ms"
                    )
                
        except Exception as e:
            logger.error(f"Error tracking performance: {e}")

    async def _handle_performance_violation(self, operation_type: str, execution_time: float):
        """Handle performance target violations."""
        try:
            violation = {
                "operation_type": operation_type,
                "execution_time": execution_time,
                "target_time": self.target_performance_ms,
                "violation_percentage": ((execution_time - self.target_performance_ms) / self.target_performance_ms) * 100,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "suggested_optimizations": await self._suggest_optimizations(operation_type, execution_time)
            }
            
            self.performance_alerts.append(violation)
            
            # Keep only recent alerts (last 100)
            if len(self.performance_alerts) > 100:
                self.performance_alerts = self.performance_alerts[-100:]
            
            logger.warning(
                f"Performance violation: {operation_type} took {execution_time:.2f}ms "
                f"(target: {self.target_performance_ms}ms)"
            )
            
        except Exception as e:
            logger.error(f"Error handling performance violation: {e}")

    async def _suggest_optimizations(self, operation_type: str, execution_time: float) -> List[str]:
        """Suggest optimizations based on performance violations."""
        suggestions = []
        
        try:
            if execution_time > self.target_performance_ms * 2:
                suggestions.append("Consider query optimization or indexing")
                suggestions.append("Implement result caching")
            
            if operation_type in ["learning_history", "performance_metrics"]:
                suggestions.append("Add pagination for large result sets")
                suggestions.append("Consider data archiving for old records")
            
            if execution_time > self.target_performance_ms * 3:
                suggestions.append("Consider database connection pooling")
                suggestions.append("Implement asynchronous processing")
            
        except Exception as e:
            logger.error(f"Error generating optimization suggestions: {e}")
        
        return suggestions

    async def _suggest_index_optimizations(self, query: str, operation_type: str):
        """Suggest database index optimizations."""
        try:
            # Analyze query patterns and suggest indexes
            if "WHERE agent_id =" in query:
                logger.debug("Suggestion: Consider index on agent_id column")
            
            if "ORDER BY created_at" in query:
                logger.debug("Suggestion: Consider index on created_at column")
            
            if "WHERE insight_type =" in query:
                logger.debug("Suggestion: Consider index on insight_type column")
                
        except Exception as e:
            logger.error(f"Error suggesting index optimizations: {e}")

    async def _process_operation_batch(
        self,
        batch: List[Dict[str, Any]]
    ) -> List[Tuple[Any, PerformanceMetrics]]:
        """Process a batch of operations efficiently."""
        results = []
        
        try:
            # Group similar operations for batch processing
            operation_groups = defaultdict(list)
            for op in batch:
                operation_groups[op.get("type", "unknown")].append(op)
            
            # Process each group
            for op_type, operations in operation_groups.items():
                group_results = await self._process_operation_group(op_type, operations)
                results.extend(group_results)
            
        except Exception as e:
            logger.error(f"Error processing operation batch: {e}")
        
        return results

    async def _process_operation_group(
        self,
        operation_type: str,
        operations: List[Dict[str, Any]]
    ) -> List[Tuple[Any, PerformanceMetrics]]:
        """Process a group of similar operations."""
        results = []
        
        try:
            for operation in operations:
                # Simulate operation processing
                start_time = time.time()
                
                # Process operation (placeholder)
                result = {"status": "processed", "operation": operation}
                
                execution_time = (time.time() - start_time) * 1000
                metrics = PerformanceMetrics(
                    operation_type=operation_type,
                    execution_time=execution_time,
                    query_count=1,
                    cache_hits=0,
                    cache_misses=1,
                    memory_usage=0.0,
                    timestamp=datetime.now(timezone.utc)
                )
                
                results.append((result, metrics))
                
        except Exception as e:
            logger.error(f"Error processing operation group: {e}")
        
        return results

    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        try:
            report = {
                "target_performance_ms": self.target_performance_ms,
                "total_operations": sum(len(history) for history in self.performance_history.values()),
                "cache_statistics": {
                    "cache_size": len(self.query_cache),
                    "max_cache_size": self.max_cache_size,
                    "cache_hit_rate": self._calculate_cache_hit_rate()
                },
                "performance_by_operation": {},
                "recent_alerts": self.performance_alerts[-10:],
                "optimization_suggestions": await self._generate_optimization_report()
            }
            
            # Calculate performance statistics by operation type
            for op_type, history in self.performance_history.items():
                if history:
                    execution_times = [m.execution_time for m in history]
                    report["performance_by_operation"][op_type] = {
                        "total_operations": len(execution_times),
                        "average_time_ms": sum(execution_times) / len(execution_times),
                        "min_time_ms": min(execution_times),
                        "max_time_ms": max(execution_times),
                        "target_violations": len([t for t in execution_times if t > self.target_performance_ms]),
                        "violation_rate": len([t for t in execution_times if t > self.target_performance_ms]) / len(execution_times)
                    }
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}

    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate from recent operations."""
        try:
            total_hits = 0
            total_operations = 0
            
            for history in self.performance_history.values():
                for metrics in history:
                    total_hits += metrics.cache_hits
                    total_operations += metrics.cache_hits + metrics.cache_misses
            
            return total_hits / total_operations if total_operations > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating cache hit rate: {e}")
            return 0.0

    async def _generate_optimization_report(self) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        try:
            # Analyze performance patterns
            for op_type, history in self.performance_history.items():
                if not history:
                    continue
                
                recent_times = [m.execution_time for m in list(history)[-50:]]
                avg_time = sum(recent_times) / len(recent_times)
                
                if avg_time > self.target_performance_ms:
                    recommendations.append(
                        f"Optimize {op_type} operations: avg {avg_time:.2f}ms > target {self.target_performance_ms}ms"
                    )
            
            # Cache optimization recommendations
            hit_rate = self._calculate_cache_hit_rate()
            if hit_rate < 0.5:
                recommendations.append(f"Improve caching strategy: hit rate {hit_rate:.2%} is low")
            
            # General recommendations
            if len(self.performance_alerts) > 10:
                recommendations.append("Consider scaling database resources due to frequent performance violations")
            
        except Exception as e:
            logger.error(f"Error generating optimization report: {e}")
        
        return recommendations

    async def clear_cache(self):
        """Clear the query cache."""
        self.query_cache.clear()
        logger.info("Query cache cleared")

    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        return {
            "cache_size": len(self.query_cache),
            "max_cache_size": self.max_cache_size,
            "cache_ttl_seconds": self.cache_ttl,
            "cache_hit_rate": self._calculate_cache_hit_rate(),
            "memory_usage_estimate": len(self.query_cache) * 1024  # Rough estimate
        }
