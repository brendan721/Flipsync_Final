"""
Standardized Product Data Interfaces for FlipSync Phase 1 Optimization
=====================================================================

Unified data structures that eliminate multiple format conversions of vision
system results while serving all 4 autonomous agents' specific data needs.

Features:
- Single conversion from ImageAnalysisResult to standardized format
- Agent-specific data extraction methods for MarketAgent, ContentAgent, ExecutiveAgent, LogisticsAgent
- Backward compatibility with existing agent interfaces
- Zero LLM dependencies and autonomous architecture compliance
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple

# Import existing components
from fs_agt_clean.core.ai.scalable_vision_service import ImageAnalysisResult
from fs_agt_clean.core.optimization.shared_product_cache import (
    ProductIdentifier,
    ProductIdentifierType,
    ComprehensiveProductData,
)

logger = logging.getLogger(__name__)


class ProductCategory(Enum):
    """Standardized product categories."""

    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME_GARDEN = "home_garden"
    AUTOMOTIVE = "automotive"
    COLLECTIBLES = "collectibles"
    BOOKS = "books"
    TOYS = "toys"
    HEALTH_BEAUTY = "health_beauty"
    SPORTS = "sports"
    GENERAL = "general"


class ConfidenceLevel(Enum):
    """Confidence levels for data quality assessment."""

    HIGH = "high"  # >0.8
    MEDIUM = "medium"  # 0.5-0.8
    LOW = "low"  # <0.5


@dataclass
class ProductDimensions:
    """Standardized product dimensions for logistics."""

    length: float = 0.0
    width: float = 0.0
    height: float = 0.0
    weight: float = 0.0
    unit_length: str = "inches"
    unit_weight: str = "pounds"
    estimated: bool = True
    confidence: float = 0.5


@dataclass
class MarketAgentData:
    """Data structure optimized for MarketAgent consumption."""

    product_identifiers: List[ProductIdentifier]
    search_keywords: List[str]
    category: ProductCategory
    estimated_price_range: Tuple[float, float]
    competitive_keywords: List[str]
    market_category_id: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    condition: str = "new"

    def get_search_query(self) -> str:
        """Generate optimized search query for market analysis."""
        query_parts = []

        # Add brand and model if available
        if self.brand:
            query_parts.append(self.brand)
        if self.model:
            query_parts.append(self.model)

        # Add top keywords
        query_parts.extend(self.search_keywords[:3])

        return " ".join(query_parts).strip()

    def get_ebay_category_id(self) -> str:
        """Get eBay category ID for API calls."""
        category_mapping = {
            ProductCategory.ELECTRONICS: "58058",
            ProductCategory.CLOTHING: "11450",
            ProductCategory.HOME_GARDEN: "11700",
            ProductCategory.AUTOMOTIVE: "6000",
            ProductCategory.COLLECTIBLES: "1",
            ProductCategory.BOOKS: "267",
            ProductCategory.TOYS: "220",
            ProductCategory.HEALTH_BEAUTY: "26395",
            ProductCategory.SPORTS: "888",
            ProductCategory.GENERAL: "58058",
        }
        return category_mapping.get(self.category, "58058")


@dataclass
class ContentAgentData:
    """Data structure optimized for ContentAgent consumption."""

    title_keywords: List[str]
    description_text: List[str]
    category: ProductCategory
    features: List[str]
    specifications: Dict[str, str]
    seo_keywords: List[str]
    quality_indicators: List[str]
    brand: Optional[str] = None
    model: Optional[str] = None

    def get_title_template_data(self) -> Dict[str, Any]:
        """Get data for title template generation."""
        return {
            "brand": self.brand or "Quality",
            "model": self.model or "Product",
            "category": self.category.value.replace("_", " ").title(),
            "key_features": self.features[:2],
            "keywords": self.title_keywords[:3],
        }

    def get_description_template_data(self) -> Dict[str, Any]:
        """Get data for description template generation."""
        return {
            "features": self.features,
            "specifications": self.specifications,
            "description_text": self.description_text,
            "seo_keywords": self.seo_keywords,
            "quality_indicators": self.quality_indicators,
            "category": self.category.value,
        }


@dataclass
class ExecutiveAgentData:
    """Data structure optimized for ExecutiveAgent consumption."""

    confidence_score: float
    quality_metrics: Dict[str, float]
    risk_factors: List[str]
    decision_factors: Dict[str, Any]
    strategic_category: ProductCategory
    investment_indicators: Dict[str, float]
    processing_metadata: Dict[str, Any]

    def get_confidence_level(self) -> ConfidenceLevel:
        """Get confidence level classification."""
        if self.confidence_score > 0.8:
            return ConfidenceLevel.HIGH
        elif self.confidence_score > 0.5:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

    def get_decision_context(self) -> Dict[str, Any]:
        """Get context for strategic decision making."""
        return {
            "confidence_level": self.get_confidence_level().value,
            "quality_score": self.quality_metrics.get("overall_quality", 0.5),
            "risk_assessment": len(self.risk_factors),
            "category_strategy": self.strategic_category.value,
            "investment_score": self.investment_indicators.get("potential_roi", 0.5),
        }


@dataclass
class LogisticsAgentData:
    """Data structure optimized for LogisticsAgent consumption."""

    dimensions: ProductDimensions
    estimated_weight: float
    shipping_category: str
    handling_requirements: List[str]
    fragility_score: float
    size_category: str  # small, medium, large, oversized

    def get_shipping_profile(self) -> Dict[str, Any]:
        """Get shipping profile for rate calculation."""
        return {
            "length": self.dimensions.length,
            "width": self.dimensions.width,
            "height": self.dimensions.height,
            "weight": self.estimated_weight,
            "category": self.shipping_category,
            "fragile": self.fragility_score > 0.7,
            "special_handling": len(self.handling_requirements) > 0,
        }


@dataclass
class StandardizedProductData:
    """
    Unified product data format serving all 4 autonomous agents.

    Eliminates multiple format conversions by providing agent-specific
    data extraction methods from a single standardized structure.
    """

    # Core identification
    product_id: str
    identifiers: List[ProductIdentifier]

    # Agent-specific data
    market_data: MarketAgentData
    content_data: ContentAgentData
    executive_data: ExecutiveAgentData
    logistics_data: LogisticsAgentData

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    source_confidence: float = 0.5
    processing_method: str = "vision_analysis"
    data_completeness: float = 0.0

    @classmethod
    def from_vision_result(
        cls, vision_result: ImageAnalysisResult
    ) -> "StandardizedProductData":
        """
        Convert ImageAnalysisResult to StandardizedProductData.

        Args:
            vision_result: Enhanced vision system analysis result

        Returns:
            Standardized product data for all agents
        """
        try:
            # Generate unique product ID
            product_id = cls._generate_product_id(vision_result)

            # Extract identifiers
            identifiers = cls._extract_identifiers(vision_result)

            # Create agent-specific data structures
            market_data = cls._create_market_data(vision_result, identifiers)
            content_data = cls._create_content_data(vision_result)
            executive_data = cls._create_executive_data(vision_result)
            logistics_data = cls._create_logistics_data(vision_result)

            # Calculate data completeness
            completeness = cls._calculate_completeness(vision_result)

            return cls(
                product_id=product_id,
                identifiers=identifiers,
                market_data=market_data,
                content_data=content_data,
                executive_data=executive_data,
                logistics_data=logistics_data,
                source_confidence=vision_result.confidence,
                processing_method=vision_result.processing_method,
                data_completeness=completeness,
            )

        except Exception as e:
            logger.error(f"Failed to convert vision result to standardized data: {e}")
            # Return minimal valid structure
            return cls._create_fallback_data(vision_result)

    @staticmethod
    def _generate_product_id(vision_result: ImageAnalysisResult) -> str:
        """Generate unique product ID from vision result."""
        import hashlib

        # Use analysis content and timestamp for uniqueness
        content_hash = hashlib.md5(
            f"{vision_result.analysis}_{vision_result.confidence}".encode()
        ).hexdigest()[:12]

        timestamp = int(datetime.now().timestamp())
        return f"prod_{timestamp}_{content_hash}"

    @staticmethod
    def _extract_identifiers(
        vision_result: ImageAnalysisResult,
    ) -> List[ProductIdentifier]:
        """Extract product identifiers from vision result."""
        identifiers = []

        try:
            product_details = vision_result.product_details or {}

            # Extract barcode data
            barcode_data = product_details.get("barcode_data")
            if barcode_data and isinstance(barcode_data, dict):
                barcode_value = barcode_data.get("data", "")
                if barcode_value:
                    # Determine barcode type
                    if len(barcode_value) == 12:
                        identifier_type = ProductIdentifierType.UPC
                    elif len(barcode_value) == 13:
                        identifier_type = ProductIdentifierType.EAN
                    else:
                        identifier_type = ProductIdentifierType.UPC  # Default

                    identifiers.append(
                        ProductIdentifier(
                            identifier_type=identifier_type,
                            value=barcode_value,
                            confidence=0.9,
                            source="vision_barcode",
                        )
                    )

            # Extract text-based identifiers
            extracted_text = product_details.get("extracted_text", [])
            if extracted_text:
                # Look for ASIN patterns
                for text_item in extracted_text:
                    if isinstance(text_item, dict):
                        text = text_item.get("text", "")
                        # ASIN pattern: B followed by 9 alphanumeric characters
                        asin_match = re.search(r"B[A-Z0-9]{9}", text.upper())
                        if asin_match:
                            identifiers.append(
                                ProductIdentifier(
                                    identifier_type=ProductIdentifierType.ASIN,
                                    value=asin_match.group(),
                                    confidence=0.8,
                                    source="vision_ocr",
                                )
                            )

            # Extract title keywords
            analysis_text = vision_result.analysis.lower()
            keywords = []
            for word in analysis_text.split():
                if len(word) > 3 and word.isalpha():
                    keywords.append(word)

            if keywords:
                identifiers.append(
                    ProductIdentifier(
                        identifier_type=ProductIdentifierType.TITLE_KEYWORDS,
                        value=" ".join(keywords[:5]),
                        confidence=0.6,
                        source="vision_analysis",
                    )
                )

            # Extract category keywords
            category_predictions = vision_result.category_predictions or []
            if category_predictions:
                identifiers.append(
                    ProductIdentifier(
                        identifier_type=ProductIdentifierType.CATEGORY_KEYWORDS,
                        value=category_predictions[0],
                        confidence=0.7,
                        source="vision_category",
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to extract some identifiers: {e}")

        return identifiers

    @staticmethod
    def _create_market_data(
        vision_result: ImageAnalysisResult, identifiers: List[ProductIdentifier]
    ) -> MarketAgentData:
        """Create MarketAgent-specific data structure."""
        try:
            # Determine category
            category_predictions = vision_result.category_predictions or ["general"]
            category_str = category_predictions[0].lower()

            # Map to ProductCategory
            category_mapping = {
                "electronics": ProductCategory.ELECTRONICS,
                "clothing": ProductCategory.CLOTHING,
                "home_garden": ProductCategory.HOME_GARDEN,
                "automotive": ProductCategory.AUTOMOTIVE,
                "collectibles": ProductCategory.COLLECTIBLES,
                "books": ProductCategory.BOOKS,
                "toys": ProductCategory.TOYS,
                "health_beauty": ProductCategory.HEALTH_BEAUTY,
                "sports": ProductCategory.SPORTS,
            }
            category = category_mapping.get(category_str, ProductCategory.GENERAL)

            # Extract keywords from analysis
            analysis_words = vision_result.analysis.lower().split()
            search_keywords = [
                word for word in analysis_words if len(word) > 3 and word.isalpha()
            ][:10]

            # Estimate price range based on category
            price_ranges = {
                ProductCategory.ELECTRONICS: (20.0, 500.0),
                ProductCategory.CLOTHING: (10.0, 100.0),
                ProductCategory.HOME_GARDEN: (15.0, 200.0),
                ProductCategory.AUTOMOTIVE: (25.0, 300.0),
                ProductCategory.COLLECTIBLES: (5.0, 1000.0),
                ProductCategory.BOOKS: (5.0, 50.0),
                ProductCategory.TOYS: (10.0, 100.0),
                ProductCategory.HEALTH_BEAUTY: (5.0, 80.0),
                ProductCategory.SPORTS: (15.0, 250.0),
                ProductCategory.GENERAL: (10.0, 100.0),
            }
            estimated_price_range = price_ranges.get(category, (10.0, 100.0))

            return MarketAgentData(
                product_identifiers=identifiers,
                search_keywords=search_keywords,
                category=category,
                estimated_price_range=estimated_price_range,
                competitive_keywords=search_keywords[:5],
            )

        except Exception as e:
            logger.error(f"Failed to create market data: {e}")
            return MarketAgentData(
                product_identifiers=identifiers,
                search_keywords=["product"],
                category=ProductCategory.GENERAL,
                estimated_price_range=(10.0, 100.0),
                competitive_keywords=["product"],
            )

    @staticmethod
    def _create_content_data(vision_result: ImageAnalysisResult) -> ContentAgentData:
        """Create ContentAgent-specific data structure."""
        try:
            # Extract text content
            product_details = vision_result.product_details or {}
            extracted_text = product_details.get("extracted_text", [])

            description_text = []
            for text_item in extracted_text:
                if isinstance(text_item, dict):
                    text = text_item.get("text", "").strip()
                    if text and len(text) > 2:
                        description_text.append(text)

            # Extract features from analysis
            analysis_text = vision_result.analysis.lower()
            features = []

            # Look for common feature patterns
            feature_patterns = [
                r"(\d+gb|\d+mb)",
                r"(\d+mp)",
                r'(\d+inch|\d+")',
                r"(wireless|bluetooth|wifi)",
                r"(waterproof|water resistant)",
                r"(rechargeable|battery)",
                r"(led|lcd|oled)",
            ]

            for pattern in feature_patterns:
                matches = re.findall(pattern, analysis_text, re.IGNORECASE)
                features.extend(matches)

            # Generate SEO keywords
            words = analysis_text.split()
            seo_keywords = [word for word in words if len(word) > 4 and word.isalpha()][
                :8
            ]

            # Determine category
            category_predictions = vision_result.category_predictions or ["general"]
            category_str = category_predictions[0].lower()
            category_mapping = {
                "electronics": ProductCategory.ELECTRONICS,
                "clothing": ProductCategory.CLOTHING,
                "home_garden": ProductCategory.HOME_GARDEN,
                "automotive": ProductCategory.AUTOMOTIVE,
                "collectibles": ProductCategory.COLLECTIBLES,
                "books": ProductCategory.BOOKS,
                "toys": ProductCategory.TOYS,
                "health_beauty": ProductCategory.HEALTH_BEAUTY,
                "sports": ProductCategory.SPORTS,
            }
            category = category_mapping.get(category_str, ProductCategory.GENERAL)

            return ContentAgentData(
                title_keywords=seo_keywords[:5],
                description_text=description_text,
                category=category,
                features=features[:10],
                specifications={},
                seo_keywords=seo_keywords,
                quality_indicators=["high quality", "durable", "reliable"],
            )

        except Exception as e:
            logger.error(f"Failed to create content data: {e}")
            return ContentAgentData(
                title_keywords=["quality", "product"],
                description_text=["Quality product"],
                category=ProductCategory.GENERAL,
                features=[],
                specifications={},
                seo_keywords=["product", "quality"],
                quality_indicators=["reliable"],
            )

    @staticmethod
    def _create_executive_data(
        vision_result: ImageAnalysisResult,
    ) -> ExecutiveAgentData:
        """Create ExecutiveAgent-specific data structure."""
        try:
            product_details = vision_result.product_details or {}
            quality_metrics = product_details.get("quality_metrics", {})

            # Extract confidence factors
            confidence_factors = product_details.get("confidence_factors", {})

            # Assess risk factors
            risk_factors = []
            if vision_result.confidence < 0.3:
                risk_factors.append("low_confidence_analysis")
            if quality_metrics.get("overall_quality", 0.5) < 0.4:
                risk_factors.append("poor_image_quality")
            if not product_details.get("barcode_data"):
                risk_factors.append("no_barcode_identification")

            # Create investment indicators
            investment_indicators = {
                "confidence_score": vision_result.confidence,
                "quality_score": quality_metrics.get("overall_quality", 0.5),
                "text_clarity": quality_metrics.get("text_density", 0.3),
                "potential_roi": min(vision_result.confidence * 1.2, 1.0),
            }

            # Determine strategic category
            category_predictions = vision_result.category_predictions or ["general"]
            category_str = category_predictions[0].lower()
            category_mapping = {
                "electronics": ProductCategory.ELECTRONICS,
                "clothing": ProductCategory.CLOTHING,
                "home_garden": ProductCategory.HOME_GARDEN,
                "automotive": ProductCategory.AUTOMOTIVE,
                "collectibles": ProductCategory.COLLECTIBLES,
                "books": ProductCategory.BOOKS,
                "toys": ProductCategory.TOYS,
                "health_beauty": ProductCategory.HEALTH_BEAUTY,
                "sports": ProductCategory.SPORTS,
            }
            strategic_category = category_mapping.get(
                category_str, ProductCategory.GENERAL
            )

            return ExecutiveAgentData(
                confidence_score=vision_result.confidence,
                quality_metrics=quality_metrics,
                risk_factors=risk_factors,
                decision_factors=confidence_factors,
                strategic_category=strategic_category,
                investment_indicators=investment_indicators,
                processing_metadata={
                    "processing_method": vision_result.processing_method,
                    "cost_estimate": vision_result.cost_estimate,
                },
            )

        except Exception as e:
            logger.error(f"Failed to create executive data: {e}")
            return ExecutiveAgentData(
                confidence_score=vision_result.confidence,
                quality_metrics={"overall_quality": 0.5},
                risk_factors=["data_extraction_error"],
                decision_factors={},
                strategic_category=ProductCategory.GENERAL,
                investment_indicators={"potential_roi": 0.5},
                processing_metadata={},
            )

    @staticmethod
    def _create_logistics_data(
        vision_result: ImageAnalysisResult,
    ) -> LogisticsAgentData:
        """Create LogisticsAgent-specific data structure."""
        try:
            product_details = vision_result.product_details or {}
            quality_metrics = product_details.get("quality_metrics", {})

            # Estimate dimensions based on category
            category_predictions = vision_result.category_predictions or ["general"]
            category_str = category_predictions[0].lower()

            # Default dimensions by category
            dimension_defaults = {
                "electronics": ProductDimensions(8.0, 6.0, 4.0, 2.0),
                "clothing": ProductDimensions(12.0, 10.0, 2.0, 1.0),
                "home_garden": ProductDimensions(10.0, 8.0, 6.0, 3.0),
                "automotive": ProductDimensions(6.0, 4.0, 3.0, 2.5),
                "collectibles": ProductDimensions(4.0, 4.0, 4.0, 0.5),
                "books": ProductDimensions(9.0, 6.0, 1.0, 1.0),
                "toys": ProductDimensions(8.0, 6.0, 4.0, 1.5),
                "health_beauty": ProductDimensions(4.0, 3.0, 2.0, 0.5),
                "sports": ProductDimensions(12.0, 8.0, 6.0, 3.0),
            }

            dimensions = dimension_defaults.get(
                category_str, ProductDimensions(8.0, 6.0, 4.0, 2.0)
            )

            # Determine size category
            volume = dimensions.length * dimensions.width * dimensions.height
            if volume < 50:
                size_category = "small"
            elif volume < 200:
                size_category = "medium"
            elif volume < 500:
                size_category = "large"
            else:
                size_category = "oversized"

            # Assess fragility
            fragility_score = 0.3  # Default
            if category_str in ["electronics", "collectibles"]:
                fragility_score = 0.8
            elif category_str in ["clothing", "books"]:
                fragility_score = 0.2

            # Determine handling requirements
            handling_requirements = []
            if fragility_score > 0.7:
                handling_requirements.append("fragile")
            if dimensions.weight > 5.0:
                handling_requirements.append("heavy")

            return LogisticsAgentData(
                dimensions=dimensions,
                estimated_weight=dimensions.weight,
                shipping_category=category_str,
                handling_requirements=handling_requirements,
                fragility_score=fragility_score,
                size_category=size_category,
            )

        except Exception as e:
            logger.error(f"Failed to create logistics data: {e}")
            return LogisticsAgentData(
                dimensions=ProductDimensions(8.0, 6.0, 4.0, 2.0),
                estimated_weight=2.0,
                shipping_category="general",
                handling_requirements=[],
                fragility_score=0.3,
                size_category="medium",
            )

    @staticmethod
    def _calculate_completeness(vision_result: ImageAnalysisResult) -> float:
        """Calculate data completeness score."""
        try:
            completeness_factors = []

            # Check for barcode data
            product_details = vision_result.product_details or {}
            if product_details.get("barcode_data"):
                completeness_factors.append(0.3)

            # Check for extracted text
            extracted_text = product_details.get("extracted_text", [])
            if extracted_text:
                completeness_factors.append(0.2)

            # Check for category prediction
            if vision_result.category_predictions:
                completeness_factors.append(0.2)

            # Check for quality metrics
            quality_metrics = product_details.get("quality_metrics", {})
            if quality_metrics:
                completeness_factors.append(0.15)

            # Check for confidence score
            if vision_result.confidence > 0.3:
                completeness_factors.append(0.15)

            return sum(completeness_factors)

        except Exception as e:
            logger.warning(f"Failed to calculate completeness: {e}")
            return 0.5

    @staticmethod
    def _create_fallback_data(
        vision_result: ImageAnalysisResult,
    ) -> "StandardizedProductData":
        """Create minimal fallback data structure."""
        product_id = f"fallback_{int(datetime.now().timestamp())}"

        identifiers = [
            ProductIdentifier(
                identifier_type=ProductIdentifierType.TITLE_KEYWORDS,
                value="unknown product",
                confidence=0.1,
                source="fallback",
            )
        ]

        return StandardizedProductData(
            product_id=product_id,
            identifiers=identifiers,
            market_data=MarketAgentData(
                product_identifiers=identifiers,
                search_keywords=["product"],
                category=ProductCategory.GENERAL,
                estimated_price_range=(10.0, 100.0),
                competitive_keywords=["product"],
            ),
            content_data=ContentAgentData(
                title_keywords=["product"],
                description_text=["Product"],
                category=ProductCategory.GENERAL,
                features=[],
                specifications={},
                seo_keywords=["product"],
                quality_indicators=[],
            ),
            executive_data=ExecutiveAgentData(
                confidence_score=0.1,
                quality_metrics={},
                risk_factors=["fallback_data"],
                decision_factors={},
                strategic_category=ProductCategory.GENERAL,
                investment_indicators={"potential_roi": 0.1},
                processing_metadata={},
            ),
            logistics_data=LogisticsAgentData(
                dimensions=ProductDimensions(8.0, 6.0, 4.0, 2.0),
                estimated_weight=2.0,
                shipping_category="general",
                handling_requirements=[],
                fragility_score=0.3,
                size_category="medium",
            ),
            source_confidence=0.1,
            processing_method="fallback",
            data_completeness=0.1,
        )

    def to_comprehensive_product_data(self) -> ComprehensiveProductData:
        """Convert to ComprehensiveProductData for caching."""
        return ComprehensiveProductData(
            product_id=self.product_id,
            identifiers=self.identifiers,
            market_data={
                "search_keywords": self.market_data.search_keywords,
                "category": self.market_data.category.value,
                "price_range": self.market_data.estimated_price_range,
                "ebay_category_id": self.market_data.get_ebay_category_id(),
            },
            pricing_data={},
            competitive_analysis={},
            content_data={
                "title_keywords": self.content_data.title_keywords,
                "features": self.content_data.features,
                "seo_keywords": self.content_data.seo_keywords,
                "category": self.content_data.category.value,
            },
            category_data={
                "primary_category": self.content_data.category.value,
                "template_data": self.content_data.get_title_template_data(),
            },
            seo_data={
                "keywords": self.content_data.seo_keywords,
                "description_data": self.content_data.get_description_template_data(),
            },
            decision_data={
                "confidence_level": self.executive_data.get_confidence_level().value,
                "decision_context": self.executive_data.get_decision_context(),
            },
            confidence_metrics=self.executive_data.quality_metrics,
            strategic_data={
                "category": self.executive_data.strategic_category.value,
                "investment_indicators": self.executive_data.investment_indicators,
            },
            logistics_data={
                "shipping_profile": self.logistics_data.get_shipping_profile(),
                "size_category": self.logistics_data.size_category,
            },
            shipping_data={
                "estimated_weight": self.logistics_data.estimated_weight,
                "handling_requirements": self.logistics_data.handling_requirements,
            },
            dimensions_data={
                "length": self.logistics_data.dimensions.length,
                "width": self.logistics_data.dimensions.width,
                "height": self.logistics_data.dimensions.height,
                "weight": self.logistics_data.dimensions.weight,
            },
            created_at=self.created_at,
            updated_at=datetime.now(),
            data_sources=[self.processing_method],
            quality_score=self.source_confidence,
        )


# Export main components
__all__ = [
    "StandardizedProductData",
    "MarketAgentData",
    "ContentAgentData",
    "ExecutiveAgentData",
    "LogisticsAgentData",
    "ProductCategory",
    "ProductDimensions",
    "ConfidenceLevel",
]
