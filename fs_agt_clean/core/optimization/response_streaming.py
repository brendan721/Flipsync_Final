#!/usr/bin/env python3
"""
Response Streaming Optimization for FlipSync Phase 4 Advanced Optimization
==========================================================================

This module provides optimized response delivery mechanisms to achieve
improved efficiency and cost reduction through streaming optimization,
bandwidth optimization, and response compression.

Features:
- Optimized response delivery with streaming efficiency improvements
- Bandwidth optimization and response compression
- Adaptive streaming based on content type and size
- Integration with existing optimization systems
- Real-time streaming performance monitoring
"""

import asyncio
import gzip
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator, Union
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class StreamingStrategy(Enum):
    """Response streaming strategies."""

    IMMEDIATE = "immediate"
    CHUNKED = "chunked"
    COMPRESSED = "compressed"
    ADAPTIVE = "adaptive"
    OPTIMIZED = "optimized"


class CompressionType(Enum):
    """Response compression types."""

    NONE = "none"
    GZIP = "gzip"
    DEFLATE = "deflate"
    ADAPTIVE = "adaptive"


class ResponseType(Enum):
    """Response content types."""

    TEXT = "text"
    JSON = "json"
    BINARY = "binary"
    STREAM = "stream"


@dataclass
class StreamingConfig:
    """Configuration for response streaming."""

    strategy: StreamingStrategy
    compression: CompressionType
    chunk_size: int
    buffer_size: int
    compression_threshold: int
    adaptive_enabled: bool


@dataclass
class StreamingMetrics:
    """Metrics for streaming performance."""

    total_responses: int
    total_bytes_sent: int
    total_bytes_saved: int
    average_compression_ratio: float
    average_streaming_time: float
    bandwidth_savings: float
    streaming_efficiency: float


@dataclass
class ResponseStreamResult:
    """Result of response streaming operation."""

    response_id: str
    original_size: int
    compressed_size: int
    compression_ratio: float
    streaming_time: float
    strategy_used: StreamingStrategy
    compression_used: CompressionType
    bandwidth_saved: int
    cost_reduction: float


class ResponseStreamingSystem:
    """
    Response streaming optimization system for FlipSync advanced optimization.

    Provides optimized response delivery mechanisms to improve efficiency
    and reduce costs through intelligent streaming, compression, and
    bandwidth optimization.
    """

    def __init__(self):
        """Initialize response streaming system."""

        # Default streaming configuration
        self.default_config = StreamingConfig(
            strategy=StreamingStrategy.ADAPTIVE,
            compression=CompressionType.ADAPTIVE,
            chunk_size=8192,  # 8KB chunks
            buffer_size=65536,  # 64KB buffer
            compression_threshold=1024,  # Compress responses > 1KB
            adaptive_enabled=True,
        )

        # Performance tracking
        self.streaming_history: List[ResponseStreamResult] = []
        self.performance_cache: Dict[str, List[ResponseStreamResult]] = {}

        # Metrics
        self.metrics = StreamingMetrics(
            total_responses=0,
            total_bytes_sent=0,
            total_bytes_saved=0,
            average_compression_ratio=0.0,
            average_streaming_time=0.0,
            bandwidth_savings=0.0,
            streaming_efficiency=0.0,
        )

        # Configuration
        self.baseline_bandwidth_cost = 0.0001  # Cost per KB
        self.compression_cpu_cost = 0.00001  # CPU cost for compression

        logger.info(
            "ResponseStreamingSystem initialized with adaptive streaming optimization"
        )

    async def stream_response(
        self,
        response_data: Union[str, bytes, Dict[str, Any]],
        response_type: ResponseType,
        client_context: Dict[str, Any],
        config: Optional[StreamingConfig] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream response with optimization.

        Yields:
            Optimized response chunks
        """

        start_time = time.time()
        response_id = f"stream_{int(time.time() * 1000)}"

        # Use provided config or default
        streaming_config = config or self.default_config

        # Prepare response data
        prepared_data = await self._prepare_response_data(response_data, response_type)
        original_size = len(prepared_data)

        # Determine optimal streaming strategy
        optimal_strategy = await self._determine_streaming_strategy(
            prepared_data, response_type, client_context, streaming_config
        )

        # Apply compression if beneficial
        compressed_data, compression_used = await self._apply_compression(
            prepared_data, optimal_strategy, streaming_config
        )

        compressed_size = len(compressed_data)
        compression_ratio = (
            compressed_size / original_size if original_size > 0 else 1.0
        )

        # Stream the response
        async for chunk in self._stream_data(
            compressed_data, optimal_strategy, streaming_config
        ):
            yield chunk

        # Calculate performance metrics
        streaming_time = time.time() - start_time
        bandwidth_saved = original_size - compressed_size
        cost_reduction = (bandwidth_saved * self.baseline_bandwidth_cost) - (
            self.compression_cpu_cost if compression_used != CompressionType.NONE else 0
        )

        # Create result record
        result = ResponseStreamResult(
            response_id=response_id,
            original_size=original_size,
            compressed_size=compressed_size,
            compression_ratio=compression_ratio,
            streaming_time=streaming_time,
            strategy_used=optimal_strategy,
            compression_used=compression_used,
            bandwidth_saved=bandwidth_saved,
            cost_reduction=cost_reduction,
        )

        # Track performance
        await self._track_streaming_performance(result, response_type)

    async def optimize_streaming_config(
        self, response_type: ResponseType, client_context: Dict[str, Any]
    ) -> StreamingConfig:
        """
        Optimize streaming configuration based on context and performance history.

        Returns:
            Optimized streaming configuration
        """

        # Analyze historical performance for this response type
        performance_analysis = await self._analyze_streaming_performance(response_type)

        # Determine optimal strategy based on analysis
        optimal_strategy = await self._determine_optimal_strategy(
            performance_analysis, client_context
        )

        # Determine optimal compression
        optimal_compression = await self._determine_optimal_compression(
            performance_analysis, client_context
        )

        # Calculate optimal chunk size
        optimal_chunk_size = await self._calculate_optimal_chunk_size(
            performance_analysis, client_context
        )

        return StreamingConfig(
            strategy=optimal_strategy,
            compression=optimal_compression,
            chunk_size=optimal_chunk_size,
            buffer_size=max(
                optimal_chunk_size * 8, 32768
            ),  # 8x chunk size or 32KB minimum
            compression_threshold=1024,  # Keep standard threshold
            adaptive_enabled=True,
        )

    async def get_streaming_metrics(self) -> StreamingMetrics:
        """Get response streaming performance metrics."""
        return self.metrics

    async def _prepare_response_data(
        self,
        response_data: Union[str, bytes, Dict[str, Any]],
        response_type: ResponseType,
    ) -> bytes:
        """Prepare response data for streaming."""

        if isinstance(response_data, bytes):
            return response_data
        elif isinstance(response_data, str):
            return response_data.encode("utf-8")
        elif isinstance(response_data, dict):
            return json.dumps(response_data, separators=(",", ":")).encode("utf-8")
        else:
            return str(response_data).encode("utf-8")

    async def _determine_streaming_strategy(
        self,
        data: bytes,
        response_type: ResponseType,
        client_context: Dict[str, Any],
        config: StreamingConfig,
    ) -> StreamingStrategy:
        """Determine optimal streaming strategy."""

        if not config.adaptive_enabled:
            return config.strategy

        data_size = len(data)

        # Small responses - immediate streaming
        if data_size < 1024:  # < 1KB
            return StreamingStrategy.IMMEDIATE

        # Large responses - chunked streaming
        elif data_size > 100000:  # > 100KB
            return StreamingStrategy.CHUNKED

        # Medium responses - check client capabilities
        client_bandwidth = client_context.get("bandwidth", "unknown")
        client_type = client_context.get("client_type", "web")

        if client_bandwidth == "low" or client_type == "mobile":
            return StreamingStrategy.COMPRESSED

        # Default to optimized streaming
        return StreamingStrategy.OPTIMIZED

    async def _apply_compression(
        self, data: bytes, strategy: StreamingStrategy, config: StreamingConfig
    ) -> tuple[bytes, CompressionType]:
        """Apply compression to response data."""

        # Skip compression for small data
        if len(data) < config.compression_threshold:
            return data, CompressionType.NONE

        # Skip compression for immediate streaming
        if strategy == StreamingStrategy.IMMEDIATE:
            return data, CompressionType.NONE

        # Determine compression type
        compression_type = config.compression
        if compression_type == CompressionType.ADAPTIVE:
            # Choose best compression based on data characteristics
            compression_type = await self._choose_adaptive_compression(data)

        # Apply compression
        if compression_type == CompressionType.GZIP:
            compressed_data = gzip.compress(
                data, compresslevel=6
            )  # Balanced compression
            return compressed_data, CompressionType.GZIP
        elif compression_type == CompressionType.DEFLATE:
            # Simulate deflate compression (using gzip for simplicity)
            compressed_data = gzip.compress(data, compresslevel=4)  # Faster compression
            return compressed_data, CompressionType.DEFLATE

        return data, CompressionType.NONE

    async def _choose_adaptive_compression(self, data: bytes) -> CompressionType:
        """Choose optimal compression type based on data characteristics."""

        # Analyze data compressibility
        sample_size = min(1024, len(data))
        sample_data = data[:sample_size]

        # Test compression ratio with small sample
        try:
            gzip_compressed = gzip.compress(sample_data, compresslevel=1)
            compression_ratio = len(gzip_compressed) / len(sample_data)

            # If data compresses well, use gzip
            if compression_ratio < 0.8:
                return CompressionType.GZIP
            # If data doesn't compress well, skip compression
            elif compression_ratio > 0.95:
                return CompressionType.NONE
            # Medium compression - use deflate
            else:
                return CompressionType.DEFLATE
        except Exception:
            return CompressionType.NONE

    async def _stream_data(
        self, data: bytes, strategy: StreamingStrategy, config: StreamingConfig
    ) -> AsyncGenerator[bytes, None]:
        """Stream data using specified strategy."""

        if strategy == StreamingStrategy.IMMEDIATE:
            # Send all data at once
            yield data

        elif strategy == StreamingStrategy.CHUNKED:
            # Send data in chunks
            chunk_size = config.chunk_size
            for i in range(0, len(data), chunk_size):
                chunk = data[i : i + chunk_size]
                yield chunk
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.001)

        elif strategy == StreamingStrategy.OPTIMIZED:
            # Adaptive chunk size based on data size
            data_size = len(data)
            if data_size < 10000:  # < 10KB
                chunk_size = 2048  # 2KB chunks
            elif data_size < 100000:  # < 100KB
                chunk_size = 8192  # 8KB chunks
            else:
                chunk_size = 16384  # 16KB chunks

            for i in range(0, len(data), chunk_size):
                chunk = data[i : i + chunk_size]
                yield chunk
                await asyncio.sleep(0.0005)  # Smaller delay for optimized streaming

        else:
            # Default chunked streaming
            chunk_size = config.chunk_size
            for i in range(0, len(data), chunk_size):
                chunk = data[i : i + chunk_size]
                yield chunk
                await asyncio.sleep(0.001)

    async def _track_streaming_performance(
        self, result: ResponseStreamResult, response_type: ResponseType
    ):
        """Track streaming performance metrics."""

        # Add to history
        self.streaming_history.append(result)

        # Add to performance cache by response type
        type_key = response_type.value
        if type_key not in self.performance_cache:
            self.performance_cache[type_key] = []
        self.performance_cache[type_key].append(result)

        # Update metrics
        self.metrics.total_responses += 1
        self.metrics.total_bytes_sent += result.compressed_size
        self.metrics.total_bytes_saved += result.bandwidth_saved

        # Update averages
        total_compression_ratio = (
            self.metrics.average_compression_ratio * (self.metrics.total_responses - 1)
            + result.compression_ratio
        ) / self.metrics.total_responses
        self.metrics.average_compression_ratio = total_compression_ratio

        total_streaming_time = (
            self.metrics.average_streaming_time * (self.metrics.total_responses - 1)
            + result.streaming_time
        ) / self.metrics.total_responses
        self.metrics.average_streaming_time = total_streaming_time

        # Calculate bandwidth savings percentage
        if self.metrics.total_bytes_sent > 0:
            original_total = (
                self.metrics.total_bytes_sent + self.metrics.total_bytes_saved
            )
            self.metrics.bandwidth_savings = (
                self.metrics.total_bytes_saved / original_total
            )

        # Calculate streaming efficiency
        if result.streaming_time > 0:
            efficiency = (
                result.compressed_size / result.streaming_time
            )  # bytes per second
            self.metrics.streaming_efficiency = (
                self.metrics.streaming_efficiency * (self.metrics.total_responses - 1)
                + efficiency
            ) / self.metrics.total_responses

    async def _analyze_streaming_performance(
        self, response_type: ResponseType
    ) -> Dict[str, Any]:
        """Analyze streaming performance for response type."""

        type_key = response_type.value
        if type_key not in self.performance_cache:
            return {"no_data": True}

        performance_data = self.performance_cache[type_key]
        recent_data = performance_data[-50:]  # Last 50 responses

        if not recent_data:
            return {"no_data": True}

        # Calculate performance statistics
        avg_compression_ratio = statistics.mean(
            [r.compression_ratio for r in recent_data]
        )
        avg_streaming_time = statistics.mean([r.streaming_time for r in recent_data])
        avg_bandwidth_saved = statistics.mean([r.bandwidth_saved for r in recent_data])
        avg_cost_reduction = statistics.mean([r.cost_reduction for r in recent_data])

        # Analyze strategy effectiveness
        strategy_performance = {}
        for strategy in StreamingStrategy:
            strategy_data = [r for r in recent_data if r.strategy_used == strategy]
            if strategy_data:
                strategy_performance[strategy.value] = {
                    "count": len(strategy_data),
                    "avg_compression": statistics.mean(
                        [r.compression_ratio for r in strategy_data]
                    ),
                    "avg_time": statistics.mean(
                        [r.streaming_time for r in strategy_data]
                    ),
                    "avg_savings": statistics.mean(
                        [r.bandwidth_saved for r in strategy_data]
                    ),
                }

        return {
            "response_type": response_type.value,
            "total_responses": len(recent_data),
            "avg_compression_ratio": avg_compression_ratio,
            "avg_streaming_time": avg_streaming_time,
            "avg_bandwidth_saved": avg_bandwidth_saved,
            "avg_cost_reduction": avg_cost_reduction,
            "strategy_performance": strategy_performance,
        }

    async def _determine_optimal_strategy(
        self, performance_analysis: Dict[str, Any], client_context: Dict[str, Any]
    ) -> StreamingStrategy:
        """Determine optimal streaming strategy based on analysis."""

        if performance_analysis.get("no_data"):
            return StreamingStrategy.ADAPTIVE

        strategy_performance = performance_analysis.get("strategy_performance", {})

        # Find strategy with best cost reduction
        best_strategy = StreamingStrategy.ADAPTIVE
        best_savings = 0

        for strategy_name, perf_data in strategy_performance.items():
            if perf_data["avg_savings"] > best_savings:
                best_savings = perf_data["avg_savings"]
                best_strategy = StreamingStrategy(strategy_name)

        return best_strategy

    async def _determine_optimal_compression(
        self, performance_analysis: Dict[str, Any], client_context: Dict[str, Any]
    ) -> CompressionType:
        """Determine optimal compression type based on analysis."""

        # Consider client capabilities
        client_cpu = client_context.get("cpu_capability", "medium")
        client_bandwidth = client_context.get("bandwidth", "medium")

        # Low CPU - avoid compression
        if client_cpu == "low":
            return CompressionType.NONE

        # Low bandwidth - prioritize compression
        if client_bandwidth == "low":
            return CompressionType.GZIP

        # Default to adaptive
        return CompressionType.ADAPTIVE

    async def _calculate_optimal_chunk_size(
        self, performance_analysis: Dict[str, Any], client_context: Dict[str, Any]
    ) -> int:
        """Calculate optimal chunk size based on analysis and context."""

        # Base chunk size
        base_chunk_size = 8192  # 8KB

        # Adjust based on client bandwidth
        client_bandwidth = client_context.get("bandwidth", "medium")
        if client_bandwidth == "low":
            return 4096  # 4KB for low bandwidth
        elif client_bandwidth == "high":
            return 16384  # 16KB for high bandwidth

        # Adjust based on historical performance
        if not performance_analysis.get("no_data"):
            avg_streaming_time = performance_analysis.get("avg_streaming_time", 0)
            if avg_streaming_time > 1.0:  # Slow streaming
                return 4096  # Smaller chunks
            elif avg_streaming_time < 0.1:  # Fast streaming
                return 16384  # Larger chunks

        return base_chunk_size


# Global response streaming system instance
_response_streaming_instance = None


def get_response_streaming_system() -> ResponseStreamingSystem:
    """Get global response streaming system instance."""
    global _response_streaming_instance
    if _response_streaming_instance is None:
        _response_streaming_instance = ResponseStreamingSystem()
    return _response_streaming_instance
