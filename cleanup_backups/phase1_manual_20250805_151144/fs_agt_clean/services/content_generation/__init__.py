"""
Content generation and optimization services.

This module provides comprehensive content generation capabilities including:
- Dynamic content generation with market trend integration
- Keyword optimization and SEO
- Price optimization strategies
- Storytelling and narrative enhancement
- Async listing generation and processing
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Import main components
try:
    from .content_generator import ContentGenerator, ContentTemplate, ListingContent
except ImportError:
    ContentGenerator = None
    ContentTemplate = None
    ListingContent = None

try:
    from .keyword_optimizer import KeywordOptimizer
except ImportError:
    KeywordOptimizer = None

try:
    from .price_optimizer import PriceOptimizer
except ImportError:
    PriceOptimizer = None

try:
    from .storytelling_engine import StorytellingEngine
except ImportError:
    StorytellingEngine = None

try:
    from .listing_generation_agent import ListingGenerationUnifiedAgent
except ImportError:
    ListingGenerationUnifiedAgent = None

try:
    from .listing_generator import ListingGenerator
except ImportError:
    ListingGenerator = None

try:
    from .async_listing_generator import ListingGenerator as AsyncListingGenerator
except ImportError:
    AsyncListingGenerator = None

try:
    from .content_optimizer import ContentOptimizer
except ImportError:
    ContentOptimizer = None

try:
    from .models import ListingContent as BaseListingContent
    from .models import ListingMetrics
except ImportError:
    BaseListingContent = None
    ListingMetrics = None

try:
    from .generation_models import (
        ContentMetrics,
        ItemSpecific,
        KeywordMetrics,
    )
    from .generation_models import ListingContent as GenerationListingContent
    from .generation_models import (
        OptimizationResult,
    )
except ImportError:
    GenerationListingContent = None
    OptimizationResult = None
    ContentMetrics = None
    ItemSpecific = None
    KeywordMetrics = None


class ContentGenerationService:
    """Main service for content generation and optimization."""

    def __init__(self, market_analyzer=None, vector_store=None):
        """Initialize the content generation service."""
        self.market_analyzer = market_analyzer
        self.vector_store = vector_store

        # Initialize components
        self.content_generator = (
            ContentGenerator(market_analyzer=market_analyzer, vector_store=vector_store)
            if ContentGenerator and market_analyzer and vector_store
            else None
        )

        self.keyword_optimizer = KeywordOptimizer() if KeywordOptimizer else None
        self.price_optimizer = PriceOptimizer() if PriceOptimizer else None
        self.storytelling_engine = StorytellingEngine() if StorytellingEngine else None
        self.content_optimizer = ContentOptimizer() if ContentOptimizer else None

    async def generate_optimized_content(
        self,
        product_data: Dict,
        market_trends: Optional[List] = None,
        competitors: Optional[List] = None,
        category_id: Optional[str] = None,
    ):
        """Generate fully optimized listing content."""
        try:
            if not self.content_generator:
                raise ValueError("Content generator not properly initialized")

            # Generate base content
            content = self.content_generator.generate_listing(
                product_data=product_data,
                market_trends=market_trends or [],
                competitors=competitors or [],
                category_id=category_id or "",
            )

            return content

        except Exception as e:
            logger.error("Failed to generate optimized content: %s", str(e))
            raise


__all__ = [
    "ContentGenerationService",
    "ContentGenerator",
    "KeywordOptimizer",
    "PriceOptimizer",
    "StorytellingEngine",
    "ListingGenerationUnifiedAgent",
    "ListingGenerator",
    "AsyncListingGenerator",
    "ContentOptimizer",
    "ContentTemplate",
    "ListingContent",
    "BaseListingContent",
    "GenerationListingContent",
    "ListingMetrics",
    "OptimizationResult",
    "ContentMetrics",
    "ItemSpecific",
    "KeywordMetrics",
]
