"""
Production Shared Product Data Cache for FlipSync Phase 1.5
==========================================================

Production-ready implementation with PostgreSQL + Redis backend for persistent
caching and high-performance lookups in the FlipSync production environment.

Features:
- PostgreSQL backend for persistent storage (174.138.77.110:5432)
- Redis layer for high-performance lookups (174.138.77.110:6379)
- Database schema integration with existing FlipSync models
- Production error handling and fallback mechanisms
- Autonomous architecture compliance (zero LLM dependencies)
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from uuid import uuid4

# Database imports
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

# FlipSync imports
from fs_agt_clean.core.db.optimized_database import OptimizedDatabase
from fs_agt_clean.core.redis.redis_manager import RedisManager, RedisConfig
from fs_agt_clean.core.optimization.shared_product_cache import (
    ProductIdentifier,
    ProductIdentifierType,
    ComprehensiveProductData,
    CachePerformanceMetrics,
)

logger = logging.getLogger(__name__)

# Database models
Base = declarative_base()


class CachedProductData(Base):
    """Database model for cached product data."""

    __tablename__ = "cached_product_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(String(255), unique=True, index=True, nullable=False)
    cache_key = Column(String(500), unique=True, index=True, nullable=False)

    # Product identifiers (JSON)
    identifiers = Column(JSON, nullable=False)

    # Agent-specific data (JSON)
    market_data = Column(JSON, nullable=False)
    pricing_data = Column(JSON, nullable=False)
    competitive_analysis = Column(JSON, nullable=False)
    content_data = Column(JSON, nullable=False)
    category_data = Column(JSON, nullable=False)
    seo_data = Column(JSON, nullable=False)
    decision_data = Column(JSON, nullable=False)
    confidence_metrics = Column(JSON, nullable=False)
    strategic_data = Column(JSON, nullable=False)
    logistics_data = Column(JSON, nullable=False)
    shipping_data = Column(JSON, nullable=False)
    dimensions_data = Column(JSON, nullable=False)

    # Metadata
    data_sources = Column(JSON, nullable=False)
    quality_score = Column(Float, default=0.0)
    cache_hits = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)


class CachePerformanceLog(Base):
    """Database model for cache performance metrics."""

    __tablename__ = "cache_performance_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Performance metrics
    total_requests = Column(Integer, default=0)
    cache_hits = Column(Integer, default=0)
    cache_misses = Column(Integer, default=0)
    api_calls_saved = Column(Integer, default=0)
    average_lookup_time_ms = Column(Float, default=0.0)
    cache_size_mb = Column(Float, default=0.0)
    hit_rate = Column(Float, default=0.0)
    api_call_reduction_rate = Column(Float, default=0.0)

    # Timestamp
    recorded_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)


class BatchOperationResult(Base):
    """Database model for batch operation results."""

    __tablename__ = "batch_operation_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    batch_id = Column(String(255), index=True, nullable=False)
    operation_type = Column(String(100), nullable=False)

    # Batch metrics
    total_requests = Column(Integer, default=0)
    successful_requests = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    total_processing_time_ms = Column(Float, default=0.0)
    api_calls_saved = Column(Integer, default=0)

    # Results data
    responses = Column(JSON, nullable=False)

    # Timestamp
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)


class ProductionSharedProductCache:
    """
    Production-ready shared product cache with PostgreSQL + Redis backend.

    Provides persistent storage via PostgreSQL and high-performance lookups
    via Redis while maintaining the same interface as the prototype cache.
    """

    def __init__(
        self,
        database: Optional[OptimizedDatabase] = None,
        redis_manager: Optional[RedisManager] = None,
        default_ttl_seconds: int = 3600,
        high_confidence_ttl_seconds: int = 86400,
        redis_ttl_seconds: int = 1800,
    ):
        """Initialize production shared product cache."""

        self.database = database
        self.redis_manager = redis_manager
        self.default_ttl = default_ttl_seconds
        self.high_confidence_ttl = high_confidence_ttl_seconds
        self.redis_ttl = redis_ttl_seconds

        # Performance metrics
        self.metrics = CachePerformanceMetrics()

        # Initialization state
        self._initialized = False

        logger.info("ProductionSharedProductCache initialized")

    async def initialize(self) -> bool:
        """Initialize database and Redis connections."""
        if self._initialized:
            return True

        try:
            # Initialize database if not provided
            if self.database is None:
                self.database = OptimizedDatabase()
                await self.database.initialize()

            # Initialize Redis if not provided
            if self.redis_manager is None:
                redis_config = RedisConfig(
                    host="127.0.0.1",
                    port=6379,
                    db=0,
                    password=None,
                )
                self.redis_manager = await RedisManager.create(redis_config)

            # Create database tables
            await self._create_tables()

            self._initialized = True
            logger.info("Production cache initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize production cache: {e}")
            return False

    async def _create_tables(self):
        """Create database tables if they don't exist."""
        try:
            async with self.database.get_session() as session:
                # Import create_all for table creation
                from sqlalchemy import MetaData

                # Create tables
                async with self.database._engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)

                logger.info("Database tables created/verified")

        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def generate_cache_key(self, identifiers: List[ProductIdentifier]) -> str:
        """Generate intelligent cache key from product identifiers."""
        try:
            # Sort identifiers by confidence (highest first)
            sorted_identifiers = sorted(
                identifiers, key=lambda x: x.confidence, reverse=True
            )

            # Use highest confidence identifier as primary key
            if sorted_identifiers:
                primary_identifier = sorted_identifiers[0]

                # Generate key based on identifier type
                if primary_identifier.identifier_type == ProductIdentifierType.UPC:
                    primary_key = f"upc_{primary_identifier.value.replace('-', '').replace(' ', '')}"
                elif primary_identifier.identifier_type == ProductIdentifierType.EAN:
                    primary_key = f"ean_{primary_identifier.value.replace('-', '').replace(' ', '')}"
                elif primary_identifier.identifier_type == ProductIdentifierType.ASIN:
                    primary_key = f"asin_{primary_identifier.value.upper()}"
                elif (
                    primary_identifier.identifier_type
                    == ProductIdentifierType.EBAY_ITEM_ID
                ):
                    primary_key = f"ebay_{primary_identifier.value}"
                else:
                    # For title/category keywords, create hash
                    import hashlib

                    value_hash = hashlib.md5(
                        primary_identifier.value.lower().encode()
                    ).hexdigest()[:12]
                    primary_key = (
                        f"{primary_identifier.identifier_type.value}_{value_hash}"
                    )

                # Add secondary identifiers for uniqueness
                secondary_keys = []
                for identifier in sorted_identifiers[1:3]:  # Max 2 secondary keys
                    secondary_key = (
                        f"{identifier.identifier_type.value}_{identifier.value}"[:8]
                    )
                    secondary_keys.append(secondary_key)

                # Combine keys
                if secondary_keys:
                    cache_key = f"{primary_key}:{':'.join(secondary_keys)}"
                else:
                    cache_key = primary_key

                logger.debug(f"Generated cache key: {cache_key}")
                return cache_key

            # Fallback to timestamp-based key
            fallback_key = f"product_{int(time.time() * 1000)}"
            logger.warning(
                f"No identifiers provided, using fallback key: {fallback_key}"
            )
            return fallback_key

        except Exception as e:
            logger.error(f"Cache key generation failed: {e}")
            return f"error_{uuid4().hex[:8]}"

    async def get_product_data(
        self, identifiers: List[ProductIdentifier], agent_type: str = "unknown"
    ) -> Optional[ComprehensiveProductData]:
        """
        Get comprehensive product data from cache (Redis first, then PostgreSQL).

        Args:
            identifiers: Product identifiers for cache lookup
            agent_type: Type of agent requesting data (for metrics)

        Returns:
            Comprehensive product data if cached, None otherwise
        """
        start_time = time.perf_counter()
        self.metrics.total_requests += 1

        try:
            # Generate cache key
            cache_key = self.generate_cache_key(identifiers)

            # Try Redis first (fastest)
            redis_data = await self._get_from_redis(cache_key)
            if redis_data:
                lookup_time = (time.perf_counter() - start_time) * 1000
                self._update_lookup_metrics(lookup_time)
                self.metrics.cache_hits += 1

                logger.debug(
                    f"Redis HIT for {agent_type}: {cache_key} "
                    f"(lookup: {lookup_time:.1f}ms)"
                )

                return redis_data

            # Try PostgreSQL (persistent storage)
            db_data = await self._get_from_database(cache_key)
            if db_data:
                # Store in Redis for future fast access
                await self._store_in_redis(cache_key, db_data)

                lookup_time = (time.perf_counter() - start_time) * 1000
                self._update_lookup_metrics(lookup_time)
                self.metrics.cache_hits += 1

                logger.debug(
                    f"Database HIT for {agent_type}: {cache_key} "
                    f"(lookup: {lookup_time:.1f}ms)"
                )

                return db_data

            # Cache miss
            self.metrics.cache_misses += 1
            lookup_time = (time.perf_counter() - start_time) * 1000
            self._update_lookup_metrics(lookup_time)

            logger.debug(
                f"Cache MISS for {agent_type}: {cache_key} "
                f"(lookup: {lookup_time:.1f}ms)"
            )

            return None

        except Exception as e:
            logger.error(f"Cache lookup failed: {e}")
            self.metrics.cache_misses += 1
            return None

    async def store_product_data(
        self,
        identifiers: List[ProductIdentifier],
        product_data: ComprehensiveProductData,
        ttl_override: Optional[int] = None,
    ) -> bool:
        """
        Store comprehensive product data in cache (both Redis and PostgreSQL).

        Args:
            identifiers: Product identifiers for cache key generation
            product_data: Comprehensive product data to cache
            ttl_override: Override default TTL

        Returns:
            True if stored successfully, False otherwise
        """
        try:
            # Generate cache key
            cache_key = self.generate_cache_key(identifiers)

            # Determine TTL based on data quality
            if ttl_override:
                ttl = ttl_override
            elif product_data.quality_score > 0.8:
                ttl = self.high_confidence_ttl
            else:
                ttl = self.default_ttl

            # Store in PostgreSQL (persistent)
            db_success = await self._store_in_database(cache_key, product_data, ttl)

            # Store in Redis (fast access)
            redis_success = await self._store_in_redis(cache_key, product_data)

            if db_success:
                # Update metrics
                self.metrics.api_calls_saved += len(product_data.data_sources)

                logger.debug(
                    f"Cached product data: {cache_key} "
                    f"(ttl: {ttl}s, quality: {product_data.quality_score:.2f}, "
                    f"db: {db_success}, redis: {redis_success})"
                )

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to store product data: {e}")
            return False

    async def _get_from_redis(
        self, cache_key: str
    ) -> Optional[ComprehensiveProductData]:
        """Get product data from Redis cache."""
        try:
            if not self.redis_manager or not self.redis_manager._client:
                return None

            # Get data from Redis
            redis_data = await self.redis_manager._client.get(
                f"product_cache:{cache_key}"
            )
            if not redis_data:
                return None

            # Deserialize data
            data_dict = json.loads(redis_data)

            # Convert back to ComprehensiveProductData
            return self._dict_to_comprehensive_data(data_dict)

        except Exception as e:
            logger.warning(f"Redis lookup failed for {cache_key}: {e}")
            return None

    async def _store_in_redis(
        self, cache_key: str, product_data: ComprehensiveProductData
    ) -> bool:
        """Store product data in Redis cache."""
        try:
            if not self.redis_manager or not self.redis_manager._client:
                return False

            # Serialize data
            data_dict = self._comprehensive_data_to_dict(product_data)
            redis_data = json.dumps(data_dict, default=str)

            # Store in Redis with TTL
            await self.redis_manager._client.setex(
                f"product_cache:{cache_key}", self.redis_ttl, redis_data
            )

            return True

        except Exception as e:
            logger.warning(f"Redis storage failed for {cache_key}: {e}")
            return False

    async def _get_from_database(
        self, cache_key: str
    ) -> Optional[ComprehensiveProductData]:
        """Get product data from PostgreSQL database."""
        try:
            async with self.database.get_session() as session:
                from sqlalchemy import select

                # Query for cached data
                stmt = select(CachedProductData).where(
                    CachedProductData.cache_key == cache_key
                )
                result = await session.execute(stmt)
                cached_row = result.scalar_one_or_none()

                if not cached_row:
                    return None

                # Check expiration
                if cached_row.expires_at and datetime.now() > cached_row.expires_at:
                    # Expired, remove from database
                    await session.delete(cached_row)
                    await session.commit()
                    return None

                # Update cache hits
                cached_row.cache_hits += 1
                await session.commit()

                # Convert to ComprehensiveProductData
                return ComprehensiveProductData(
                    product_id=cached_row.product_id,
                    identifiers=[
                        ProductIdentifier(**id_data)
                        for id_data in cached_row.identifiers
                    ],
                    market_data=cached_row.market_data,
                    pricing_data=cached_row.pricing_data,
                    competitive_analysis=cached_row.competitive_analysis,
                    content_data=cached_row.content_data,
                    category_data=cached_row.category_data,
                    seo_data=cached_row.seo_data,
                    decision_data=cached_row.decision_data,
                    confidence_metrics=cached_row.confidence_metrics,
                    strategic_data=cached_row.strategic_data,
                    logistics_data=cached_row.logistics_data,
                    shipping_data=cached_row.shipping_data,
                    dimensions_data=cached_row.dimensions_data,
                    created_at=cached_row.created_at,
                    updated_at=cached_row.updated_at,
                    cache_hits=cached_row.cache_hits,
                    data_sources=cached_row.data_sources,
                    quality_score=cached_row.quality_score,
                )

        except Exception as e:
            logger.error(f"Database lookup failed for {cache_key}: {e}")
            return None

    async def _store_in_database(
        self, cache_key: str, product_data: ComprehensiveProductData, ttl: int
    ) -> bool:
        """Store product data in PostgreSQL database."""
        try:
            async with self.database.get_session() as session:
                from sqlalchemy import select

                # Check if already exists
                stmt = select(CachedProductData).where(
                    CachedProductData.cache_key == cache_key
                )
                result = await session.execute(stmt)
                existing_row = result.scalar_one_or_none()

                # Calculate expiration
                expires_at = datetime.now() + timedelta(seconds=ttl)

                if existing_row:
                    # Update existing row
                    existing_row.market_data = product_data.market_data
                    existing_row.pricing_data = product_data.pricing_data
                    existing_row.competitive_analysis = (
                        product_data.competitive_analysis
                    )
                    existing_row.content_data = product_data.content_data
                    existing_row.category_data = product_data.category_data
                    existing_row.seo_data = product_data.seo_data
                    existing_row.decision_data = product_data.decision_data
                    existing_row.confidence_metrics = product_data.confidence_metrics
                    existing_row.strategic_data = product_data.strategic_data
                    existing_row.logistics_data = product_data.logistics_data
                    existing_row.shipping_data = product_data.shipping_data
                    existing_row.dimensions_data = product_data.dimensions_data
                    existing_row.data_sources = product_data.data_sources
                    existing_row.quality_score = product_data.quality_score
                    existing_row.expires_at = expires_at
                    existing_row.updated_at = datetime.now()
                else:
                    # Create new row
                    new_row = CachedProductData(
                        product_id=product_data.product_id,
                        cache_key=cache_key,
                        identifiers=[
                            asdict(id_obj) for id_obj in product_data.identifiers
                        ],
                        market_data=product_data.market_data,
                        pricing_data=product_data.pricing_data,
                        competitive_analysis=product_data.competitive_analysis,
                        content_data=product_data.content_data,
                        category_data=product_data.category_data,
                        seo_data=product_data.seo_data,
                        decision_data=product_data.decision_data,
                        confidence_metrics=product_data.confidence_metrics,
                        strategic_data=product_data.strategic_data,
                        logistics_data=product_data.logistics_data,
                        shipping_data=product_data.shipping_data,
                        dimensions_data=product_data.dimensions_data,
                        data_sources=product_data.data_sources,
                        quality_score=product_data.quality_score,
                        expires_at=expires_at,
                    )
                    session.add(new_row)

                await session.commit()
                return True

        except Exception as e:
            logger.error(f"Database storage failed for {cache_key}: {e}")
            return False

    def _comprehensive_data_to_dict(
        self, data: ComprehensiveProductData
    ) -> Dict[str, Any]:
        """Convert ComprehensiveProductData to dictionary for serialization."""
        return {
            "product_id": data.product_id,
            "identifiers": [asdict(id_obj) for id_obj in data.identifiers],
            "market_data": data.market_data,
            "pricing_data": data.pricing_data,
            "competitive_analysis": data.competitive_analysis,
            "content_data": data.content_data,
            "category_data": data.category_data,
            "seo_data": data.seo_data,
            "decision_data": data.decision_data,
            "confidence_metrics": data.confidence_metrics,
            "strategic_data": data.strategic_data,
            "logistics_data": data.logistics_data,
            "shipping_data": data.shipping_data,
            "dimensions_data": data.dimensions_data,
            "created_at": data.created_at.isoformat() if data.created_at else None,
            "updated_at": data.updated_at.isoformat() if data.updated_at else None,
            "cache_hits": data.cache_hits,
            "data_sources": data.data_sources,
            "quality_score": data.quality_score,
        }

    def _dict_to_comprehensive_data(
        self, data_dict: Dict[str, Any]
    ) -> ComprehensiveProductData:
        """Convert dictionary to ComprehensiveProductData."""
        return ComprehensiveProductData(
            product_id=data_dict["product_id"],
            identifiers=[
                ProductIdentifier(**id_data) for id_data in data_dict["identifiers"]
            ],
            market_data=data_dict["market_data"],
            pricing_data=data_dict["pricing_data"],
            competitive_analysis=data_dict["competitive_analysis"],
            content_data=data_dict["content_data"],
            category_data=data_dict["category_data"],
            seo_data=data_dict["seo_data"],
            decision_data=data_dict["decision_data"],
            confidence_metrics=data_dict["confidence_metrics"],
            strategic_data=data_dict["strategic_data"],
            logistics_data=data_dict["logistics_data"],
            shipping_data=data_dict["shipping_data"],
            dimensions_data=data_dict["dimensions_data"],
            created_at=(
                datetime.fromisoformat(data_dict["created_at"])
                if data_dict.get("created_at")
                else datetime.now()
            ),
            updated_at=(
                datetime.fromisoformat(data_dict["updated_at"])
                if data_dict.get("updated_at")
                else datetime.now()
            ),
            cache_hits=data_dict.get("cache_hits", 0),
            data_sources=data_dict["data_sources"],
            quality_score=data_dict["quality_score"],
        )

    def _update_lookup_metrics(self, lookup_time_ms: float) -> None:
        """Update lookup time metrics."""
        self.metrics.total_lookup_time_ms += lookup_time_ms
        self.metrics.average_lookup_time_ms = (
            self.metrics.total_lookup_time_ms / self.metrics.total_requests
        )

    async def log_performance_metrics(self) -> bool:
        """Log current performance metrics to database."""
        try:
            async with self.database.get_session() as session:
                # Update calculated metrics
                if self.metrics.total_requests > 0:
                    self.metrics.hit_rate = (
                        self.metrics.cache_hits / self.metrics.total_requests
                    )

                if self.metrics.cache_hits > 0:
                    self.metrics.api_call_reduction_rate = (
                        self.metrics.api_calls_saved
                        / (self.metrics.api_calls_saved + self.metrics.cache_misses)
                    )

                # Create performance log entry
                log_entry = CachePerformanceLog(
                    total_requests=self.metrics.total_requests,
                    cache_hits=self.metrics.cache_hits,
                    cache_misses=self.metrics.cache_misses,
                    api_calls_saved=self.metrics.api_calls_saved,
                    average_lookup_time_ms=self.metrics.average_lookup_time_ms,
                    cache_size_mb=self.metrics.cache_size_mb,
                    hit_rate=self.metrics.hit_rate,
                    api_call_reduction_rate=self.metrics.api_call_reduction_rate,
                )

                session.add(log_entry)
                await session.commit()

                return True

        except Exception as e:
            logger.error(f"Failed to log performance metrics: {e}")
            return False

    async def get_performance_metrics(self) -> CachePerformanceMetrics:
        """Get current cache performance metrics."""
        # Update calculated metrics
        if self.metrics.total_requests > 0:
            self.metrics.hit_rate = (
                self.metrics.cache_hits / self.metrics.total_requests
            )

        if self.metrics.cache_hits > 0:
            self.metrics.api_call_reduction_rate = self.metrics.api_calls_saved / (
                self.metrics.api_calls_saved + self.metrics.cache_misses
            )

        # Estimate cache size (rough calculation)
        self.metrics.cache_size_mb = self.metrics.cache_hits * 0.05  # Rough estimate

        return self.metrics

    async def clear_expired_entries(self) -> int:
        """Clear expired cache entries from database and return count cleared."""
        try:
            async with self.database.get_session() as session:
                from sqlalchemy import delete

                # Delete expired entries
                stmt = delete(CachedProductData).where(
                    CachedProductData.expires_at < datetime.now()
                )
                result = await session.execute(stmt)
                cleared_count = result.rowcount

                await session.commit()

                if cleared_count > 0:
                    logger.info(f"Cleared {cleared_count} expired cache entries")

                return cleared_count

        except Exception as e:
            logger.error(f"Failed to clear expired entries: {e}")
            return 0


# Global production cache instance
_production_cache_instance: Optional[ProductionSharedProductCache] = None


async def get_production_shared_cache() -> ProductionSharedProductCache:
    """Get global production shared cache instance."""
    global _production_cache_instance
    if _production_cache_instance is None:
        _production_cache_instance = ProductionSharedProductCache()
        await _production_cache_instance.initialize()
    return _production_cache_instance


# Export main components
__all__ = [
    "ProductionSharedProductCache",
    "CachedProductData",
    "CachePerformanceLog",
    "BatchOperationResult",
    "get_production_shared_cache",
]
