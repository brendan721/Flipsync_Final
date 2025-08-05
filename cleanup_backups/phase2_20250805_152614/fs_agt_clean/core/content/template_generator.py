"""
FlipSync Template-Based Content Generation
=========================================

High-performance content generation using templates, NLP, and fine-tuned models.
Replaces OpenAI dependency for content creation with cost-effective alternatives.

Features:
- Template-based generation with dynamic content
- spaCy NLP for text enhancement
- Keyword optimization and SEO
- A/B testing for content variants
- Performance tracking and optimization
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from collections import defaultdict

try:
    import spacy
    from spacy.lang.en import English

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    """Types of content that can be generated."""

    PRODUCT_TITLE = "product_title"
    PRODUCT_DESCRIPTION = "product_description"
    SEO_KEYWORDS = "seo_keywords"
    BULLET_POINTS = "bullet_points"
    CATEGORY_DESCRIPTION = "category_description"
    SEARCH_TERMS = "search_terms"


class TemplateVariant(str, Enum):
    """Template variants for A/B testing."""

    STANDARD = "standard"
    PREMIUM = "premium"
    BUDGET = "budget"
    TECHNICAL = "technical"
    LIFESTYLE = "lifestyle"


@dataclass
class ContentTemplate:
    """Template definition for content generation."""

    template_id: str
    content_type: ContentType
    variant: TemplateVariant
    template_text: str
    required_fields: List[str]
    optional_fields: List[str] = field(default_factory=list)
    seo_weight: float = 1.0
    performance_score: float = 0.0
    usage_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentRequest:
    """Request for content generation."""

    request_id: str
    content_type: ContentType
    product_data: Dict[str, Any]
    target_variant: Optional[TemplateVariant] = None
    seo_keywords: List[str] = field(default_factory=list)
    max_length: Optional[int] = None
    style_preferences: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentResult:
    """Result of content generation."""

    content_id: str
    request_id: str
    generated_content: str
    template_used: str
    variant_used: TemplateVariant
    seo_score: float
    processing_time_ms: int
    confidence_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class NLPProcessor:
    """NLP processing using spaCy for text enhancement."""

    def __init__(self):
        self.nlp = None
        self._initialize_nlp()

    def _initialize_nlp(self):
        """Initialize spaCy NLP pipeline."""
        if SPACY_AVAILABLE:
            try:
                # Try to load English model
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                # Fallback to basic English
                self.nlp = English()
                logger.warning(
                    "Using basic English model, install en_core_web_sm for better results"
                )
        else:
            logger.warning("spaCy not available, using basic text processing")

    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """Extract keywords from text."""
        if not self.nlp:
            return self._basic_keyword_extraction(text, max_keywords)

        doc = self.nlp(text)

        # Extract meaningful tokens
        keywords = []
        for token in doc:
            if (
                token.is_alpha
                and not token.is_stop
                and not token.is_punct
                and len(token.text) > 2
            ):
                keywords.append(token.lemma_.lower())

        # Remove duplicates and return top keywords
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:max_keywords]

    def _basic_keyword_extraction(self, text: str, max_keywords: int) -> List[str]:
        """Basic keyword extraction without spaCy."""
        # Simple word extraction
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

        # Basic stop words
        stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "among",
            "this",
            "that",
            "these",
            "those",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
        }

        # Filter stop words
        keywords = [word for word in words if word not in stop_words]

        # Remove duplicates and return top keywords
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:max_keywords]

    def enhance_text(self, text: str, keywords: List[str]) -> str:
        """Enhance text with better keyword integration."""
        if not keywords:
            return text

        # Simple keyword integration
        enhanced_text = text

        # Add keywords naturally if not present
        for keyword in keywords[:3]:  # Use top 3 keywords
            if keyword.lower() not in enhanced_text.lower():
                # Try to integrate keyword naturally
                if enhanced_text.endswith("."):
                    enhanced_text = enhanced_text[:-1] + f" with {keyword}."
                else:
                    enhanced_text += f" Features {keyword}."

        return enhanced_text

    def calculate_seo_score(self, text: str, target_keywords: List[str]) -> float:
        """Calculate SEO score based on keyword presence and density."""
        if not target_keywords:
            return 0.5

        text_lower = text.lower()
        total_words = len(text.split())

        keyword_score = 0.0
        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            count = text_lower.count(keyword_lower)

            if count > 0:
                # Keyword present
                keyword_score += 0.3

                # Optimal density (1-3%)
                density = count / total_words
                if 0.01 <= density <= 0.03:
                    keyword_score += 0.2
                elif density > 0.03:
                    keyword_score += 0.1  # Penalize over-optimization

        # Normalize score
        max_possible_score = len(target_keywords) * 0.5
        return (
            min(keyword_score / max_possible_score, 1.0)
            if max_possible_score > 0
            else 0.5
        )


class TemplateEngine:
    """Template engine for content generation."""

    def __init__(self):
        self.templates: Dict[str, List[ContentTemplate]] = defaultdict(list)
        self.nlp_processor = NLPProcessor()
        self._load_default_templates()

    def _load_default_templates(self):
        """Load default templates for common content types."""

        # Product title templates
        title_templates = [
            {
                "template_id": "title_standard_1",
                "content_type": ContentType.PRODUCT_TITLE,
                "variant": TemplateVariant.STANDARD,
                "template_text": "{brand} {product_name} - {key_feature} | {category}",
                "required_fields": ["product_name", "category"],
                "optional_fields": ["brand", "key_feature"],
                "seo_weight": 1.0,
            },
            {
                "template_id": "title_premium_1",
                "content_type": ContentType.PRODUCT_TITLE,
                "variant": TemplateVariant.PREMIUM,
                "template_text": "Premium {product_name} with {key_feature} - {brand} Quality",
                "required_fields": ["product_name"],
                "optional_fields": ["brand", "key_feature"],
                "seo_weight": 1.2,
            },
        ]

        # Product description templates
        description_templates = [
            {
                "template_id": "desc_standard_1",
                "content_type": ContentType.PRODUCT_DESCRIPTION,
                "variant": TemplateVariant.STANDARD,
                "template_text": "Discover the {product_name} from {brand}. This {category} features {key_features} and delivers exceptional {main_benefit}. Perfect for {target_audience}, it offers {unique_selling_point}. {call_to_action}",
                "required_fields": ["product_name", "category"],
                "optional_fields": [
                    "brand",
                    "key_features",
                    "main_benefit",
                    "target_audience",
                    "unique_selling_point",
                    "call_to_action",
                ],
                "seo_weight": 1.0,
            }
        ]

        # Load templates
        for template_data in title_templates + description_templates:
            template = ContentTemplate(**template_data)
            self.templates[template.content_type.value].append(template)

    def add_template(self, template: ContentTemplate):
        """Add a new template."""
        self.templates[template.content_type.value].append(template)

    def select_template(
        self, content_type: ContentType, variant: Optional[TemplateVariant] = None
    ) -> Optional[ContentTemplate]:
        """Select best template for content generation."""
        available_templates = self.templates.get(content_type.value, [])

        if not available_templates:
            return None

        # Filter by variant if specified
        if variant:
            variant_templates = [t for t in available_templates if t.variant == variant]
            if variant_templates:
                available_templates = variant_templates

        # Select template with best performance score
        return max(
            available_templates, key=lambda t: t.performance_score + t.seo_weight
        )

    def generate_content(self, template: ContentTemplate, data: Dict[str, Any]) -> str:
        """Generate content using template and data."""
        content = template.template_text

        # Replace required fields
        for field in template.required_fields:
            value = data.get(field, f"[{field}]")
            content = content.replace(f"{{{field}}}", str(value))

        # Replace optional fields
        for field in template.optional_fields:
            value = data.get(field, "")
            if value:
                content = content.replace(f"{{{field}}}", str(value))
            else:
                # Remove placeholder and clean up
                content = re.sub(rf"\s*\{{{field}\}}\s*", " ", content)
                content = re.sub(r"\s+", " ", content)  # Clean multiple spaces

        # Clean up any remaining placeholders
        content = re.sub(r"\{[^}]+\}", "", content)
        content = re.sub(r"\s+", " ", content).strip()

        return content


class FlipSyncContentGenerator:
    """Main content generator for FlipSync."""

    def __init__(self):
        self.template_engine = TemplateEngine()
        self.nlp_processor = NLPProcessor()
        self.performance_metrics = defaultdict(list)
        self.ab_test_results = defaultdict(dict)

    async def generate_content(self, request: ContentRequest) -> ContentResult:
        """Generate content based on request."""
        start_time = time.perf_counter()

        try:
            # Select template
            template = self.template_engine.select_template(
                request.content_type, request.target_variant
            )

            if not template:
                raise ValueError(f"No template available for {request.content_type}")

            # Generate base content
            generated_content = self.template_engine.generate_content(
                template, request.product_data
            )

            # Enhance with NLP if keywords provided
            if request.seo_keywords:
                generated_content = self.nlp_processor.enhance_text(
                    generated_content, request.seo_keywords
                )

            # Apply length constraints
            if request.max_length and len(generated_content) > request.max_length:
                generated_content = generated_content[: request.max_length - 3] + "..."

            # Calculate SEO score
            seo_score = self.nlp_processor.calculate_seo_score(
                generated_content, request.seo_keywords
            )

            # Calculate confidence based on template performance and data completeness
            data_completeness = len(
                [f for f in template.required_fields if f in request.product_data]
            ) / len(template.required_fields)
            confidence_score = (
                (template.performance_score * 0.5)
                + (data_completeness * 0.3)
                + (seo_score * 0.2)
            )

            processing_time = int((time.perf_counter() - start_time) * 1000)

            # Update template usage
            template.usage_count += 1

            # Track performance
            self.performance_metrics[request.content_type.value].append(processing_time)

            result = ContentResult(
                content_id=f"content_{int(time.time() * 1000)}",
                request_id=request.request_id,
                generated_content=generated_content,
                template_used=template.template_id,
                variant_used=template.variant,
                seo_score=seo_score,
                processing_time_ms=processing_time,
                confidence_score=confidence_score,
                metadata={
                    "template_performance": template.performance_score,
                    "data_completeness": data_completeness,
                    "keywords_used": len(request.seo_keywords),
                },
            )

            return result

        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise

    def update_template_performance(self, template_id: str, performance_score: float):
        """Update template performance based on results."""
        for templates in self.template_engine.templates.values():
            for template in templates:
                if template.template_id == template_id:
                    # Weighted average with existing score
                    template.performance_score = (
                        template.performance_score * template.usage_count
                        + performance_score
                    ) / (template.usage_count + 1)
                    break

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}

        for content_type, times in self.performance_metrics.items():
            if times:
                stats[content_type] = {
                    "avg_time_ms": sum(times) / len(times),
                    "min_time_ms": min(times),
                    "max_time_ms": max(times),
                    "total_generations": len(times),
                }

        return stats
