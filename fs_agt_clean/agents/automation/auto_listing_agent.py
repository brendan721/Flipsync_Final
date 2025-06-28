"""
Auto Listing UnifiedAgent for FlipSync
Automated listing creation, optimization, and management.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole

logger = logging.getLogger(__name__)


class ListingStatus(str, Enum):
    """Listing status types."""

    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    SOLD = "sold"
    ENDED = "ended"
    ERROR = "error"


class ListingPlatform(str, Enum):
    """Supported listing platforms."""

    EBAY = "ebay"
    AMAZON = "amazon"
    WALMART = "walmart"
    ETSY = "etsy"
    FACEBOOK = "facebook"


class OptimizationType(str, Enum):
    """Types of listing optimizations."""

    TITLE = "title"
    DESCRIPTION = "description"
    IMAGES = "images"
    PRICING = "pricing"
    KEYWORDS = "keywords"
    CATEGORY = "category"


@dataclass
class ListingTemplate:
    """Template for automated listing creation."""

    name: str
    platform: ListingPlatform
    category: str
    title_template: str
    description_template: str
    keywords: List[str]
    pricing_strategy: str
    shipping_template: str
    return_policy: str
    enabled: bool = True


@dataclass
class AutoListingResult:
    """Result of automated listing creation."""

    listing_id: str
    platform: ListingPlatform
    title: str
    price: float
    status: ListingStatus
    optimizations_applied: List[OptimizationType]
    confidence: float
    created_at: datetime
    metadata: Dict[str, Any]


class AutoListingUnifiedAgent(BaseConversationalUnifiedAgent):
    """
    Automated listing agent that creates and optimizes marketplace listings.

    Capabilities:
    - Automated listing creation from product data
    - SEO-optimized titles and descriptions
    - Multi-platform listing management
    - Image optimization and enhancement
    - Keyword research and optimization
    - Performance monitoring and adjustments
    """

    def __init__(
        self, agent_id: str = "auto_listing_agent", use_fast_model: bool = True
    ):
        """Initialize the auto listing agent."""
        super().__init__(
            agent_role=UnifiedAgentRole.CONTENT,
            agent_id=agent_id,
            use_fast_model=use_fast_model,
        )

        # Listing configuration
        self.listing_templates: List[ListingTemplate] = []
        self.active_listings: Dict[str, AutoListingResult] = {}
        self.auto_optimization_enabled = True

        # Initialize default templates
        self._initialize_default_templates()

        logger.info(f"AutoListingUnifiedAgent initialized: {self.agent_id}")

    def _initialize_default_templates(self):
        """Initialize default listing templates."""
        self.listing_templates = [
            ListingTemplate(
                name="electronics_ebay",
                platform=ListingPlatform.EBAY,
                category="electronics",
                title_template="{brand} {model} {condition} - {key_features}",
                description_template="""
                <h2>{title}</h2>
                <p><strong>Condition:</strong> {condition}</p>
                <p><strong>Key Features:</strong></p>
                <ul>{feature_list}</ul>
                <p><strong>What's Included:</strong> {included_items}</p>
                <p><strong>Shipping:</strong> {shipping_info}</p>
                """,
                keywords=["electronics", "gadget", "tech", "device"],
                pricing_strategy="competitive",
                shipping_template="Fast & Free shipping with tracking",
                return_policy="30-day returns accepted",
            ),
            ListingTemplate(
                name="clothing_amazon",
                platform=ListingPlatform.AMAZON,
                category="clothing",
                title_template="{brand} {type} {size} {color} - {style}",
                description_template="""
                {brand} {type} in {color}
                
                Size: {size}
                Material: {material}
                Style: {style}
                
                Perfect for {occasion}. High-quality {material} construction.
                """,
                keywords=["fashion", "clothing", "apparel", "style"],
                pricing_strategy="premium",
                shipping_template="Prime eligible - Free 2-day shipping",
                return_policy="Amazon return policy applies",
            ),
        ]

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific context for prompt generation."""
        return {
            "agent_type": "automated_listing_specialist",
            "capabilities": [
                "Automated listing creation",
                "SEO optimization",
                "Multi-platform management",
                "Content generation",
                "Performance optimization",
            ],
            "supported_platforms": [platform.value for platform in ListingPlatform],
            "active_templates": len([t for t in self.listing_templates if t.enabled]),
            "active_listings": len(self.active_listings),
        }

    async def create_automated_listing(
        self,
        product_data: Dict[str, Any],
        platform: ListingPlatform,
        template_name: Optional[str] = None,
    ) -> AutoListingResult:
        """Create an automated listing from product data."""
        try:
            # Select appropriate template
            template = self._select_template(
                platform, product_data.get("category"), template_name
            )

            if not template:
                raise ValueError(f"No suitable template found for {platform.value}")

            # Generate optimized title
            title = await self._generate_optimized_title(product_data, template)

            # Generate optimized description
            description = await self._generate_optimized_description(
                product_data, template
            )

            # Calculate optimal price
            price = await self._calculate_listing_price(product_data, platform)

            # Apply SEO optimizations
            optimizations = await self._apply_seo_optimizations(
                title, description, product_data
            )

            # Create listing result
            listing_result = AutoListingResult(
                listing_id=f"auto_{platform.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                platform=platform,
                title=optimizations.get("optimized_title", title),
                price=price,
                status=ListingStatus.DRAFT,
                optimizations_applied=list(optimizations.keys()),
                confidence=self._calculate_listing_confidence(product_data, template),
                created_at=datetime.now(timezone.utc),
                metadata={
                    "template_used": template.name,
                    "original_title": title,
                    "description": optimizations.get(
                        "optimized_description", description
                    ),
                    "keywords": optimizations.get("keywords", []),
                    "category": product_data.get("category", "unknown"),
                },
            )

            # Store listing
            self.active_listings[listing_result.listing_id] = listing_result

            return listing_result

        except Exception as e:
            logger.error(f"Error creating automated listing: {e}")
            raise

    def _select_template(
        self,
        platform: ListingPlatform,
        category: Optional[str],
        template_name: Optional[str],
    ) -> Optional[ListingTemplate]:
        """Select the best template for the listing."""
        if template_name:
            # Find specific template by name
            for template in self.listing_templates:
                if template.name == template_name and template.enabled:
                    return template

        # Find template by platform and category
        for template in self.listing_templates:
            if (
                template.platform == platform
                and template.enabled
                and (not category or template.category == category)
            ):
                return template

        # Find any template for the platform
        for template in self.listing_templates:
            if template.platform == platform and template.enabled:
                return template

        return None

    async def _generate_optimized_title(
        self, product_data: Dict[str, Any], template: ListingTemplate
    ) -> str:
        """Generate SEO-optimized title using AI."""
        try:
            prompt = f"""
            Create an optimized marketplace listing title for this product:
            
            Product Data:
            - Brand: {product_data.get('brand', 'Unknown')}
            - Model: {product_data.get('model', 'Unknown')}
            - Category: {product_data.get('category', 'Unknown')}
            - Condition: {product_data.get('condition', 'Used')}
            - Key Features: {product_data.get('features', [])}
            
            Platform: {template.platform.value}
            Template: {template.title_template}
            
            Requirements:
            - Maximum 80 characters for eBay, 200 for Amazon
            - Include key search terms
            - Highlight unique selling points
            - Follow platform best practices
            
            Generate an optimized title:
            """

            response = await self.llm_client.generate_response(
                prompt=prompt,
                system_prompt="You are an expert marketplace listing optimizer. Create compelling, SEO-friendly titles.",
            )

            return response.content.strip()

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            # Fallback to template-based title
            return template.title_template.format(
                brand=product_data.get("brand", "Unknown"),
                model=product_data.get("model", ""),
                condition=product_data.get("condition", "Used"),
                key_features=", ".join(product_data.get("features", [])[:2]),
            )

    async def _generate_optimized_description(
        self, product_data: Dict[str, Any], template: ListingTemplate
    ) -> str:
        """Generate SEO-optimized description using AI."""
        try:
            prompt = f"""
            Create an optimized marketplace listing description for this product:
            
            Product Data:
            {product_data}
            
            Platform: {template.platform.value}
            Template Structure: {template.description_template}
            
            Requirements:
            - Engaging and informative
            - Include key features and benefits
            - Use relevant keywords naturally
            - Follow platform formatting guidelines
            - Include shipping and return information
            
            Generate an optimized description:
            """

            response = await self.llm_client.generate_response(
                prompt=prompt,
                system_prompt="You are an expert marketplace copywriter. Create compelling, detailed product descriptions.",
            )

            return response.content

        except Exception as e:
            logger.error(f"Error generating description: {e}")
            # Fallback to basic description
            return f"High-quality {product_data.get('category', 'item')} in {product_data.get('condition', 'good')} condition."

    async def _calculate_listing_price(
        self, product_data: Dict[str, Any], platform: ListingPlatform
    ) -> float:
        """Calculate optimal listing price."""
        base_price = product_data.get("price", 0.0)
        cost = product_data.get("cost", base_price * 0.7)

        # Platform-specific pricing adjustments
        if platform == ListingPlatform.AMAZON:
            # Amazon typically allows higher prices
            return base_price * 1.05
        elif platform == ListingPlatform.EBAY:
            # eBay is more price-sensitive
            return base_price * 0.98
        else:
            return base_price

    async def _apply_seo_optimizations(
        self, title: str, description: str, product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply SEO optimizations to listing content."""
        try:
            prompt = f"""
            Optimize this listing for search visibility:
            
            Title: {title}
            Description: {description[:500]}...
            Category: {product_data.get('category', 'Unknown')}
            
            Provide optimizations for:
            1. Title (if improvements needed)
            2. Description (if improvements needed)
            3. Keywords to target
            4. Category suggestions
            
            Return as JSON format with keys: optimized_title, optimized_description, keywords, category
            """

            response = await self.llm_client.generate_response(
                prompt=prompt,
                system_prompt="You are an SEO expert for marketplace listings. Optimize for search visibility and conversion.",
            )

            # Parse response (simplified - in production would use proper JSON parsing)
            return {
                "optimized_title": title,  # Would parse from AI response
                "optimized_description": description,  # Would parse from AI response
                "keywords": product_data.get("keywords", []),
                "category": product_data.get("category", "unknown"),
            }

        except Exception as e:
            logger.error(f"Error applying SEO optimizations: {e}")
            return {
                "keywords": product_data.get("keywords", []),
                "category": product_data.get("category", "unknown"),
            }

    def _calculate_listing_confidence(
        self, product_data: Dict[str, Any], template: ListingTemplate
    ) -> float:
        """Calculate confidence in the automated listing."""
        confidence = 0.5  # Base confidence

        # More product data = higher confidence
        required_fields = ["brand", "model", "condition", "category", "price"]
        available_fields = sum(
            1 for field in required_fields if product_data.get(field)
        )
        confidence += (available_fields / len(required_fields)) * 0.3

        # Template match = higher confidence
        if template.category == product_data.get("category"):
            confidence += 0.2

        return min(1.0, confidence)

    async def _process_response(self, response: Any) -> str:
        """Process and format the response for listing queries."""
        if hasattr(response, "content"):
            return response.content
        return str(response)

    async def handle_message(
        self, message: str, conversation_id: str, user_id: str
    ) -> UnifiedAgentResponse:
        """Handle listing-related queries and requests."""
        try:
            system_prompt = """You are FlipSync's Auto Listing UnifiedAgent, an expert in automated marketplace listing creation and optimization.

Your capabilities include:
- Automated listing creation from product data
- SEO-optimized titles and descriptions
- Multi-platform listing management (eBay, Amazon, Walmart, etc.)
- Content optimization and keyword research
- Performance monitoring and improvements

Provide specific, actionable advice for listing optimization and automation."""

            response = await self.llm_client.generate_response(
                prompt=message, system_prompt=system_prompt
            )

            return UnifiedAgentResponse(
                content=response.content,
                agent_type="auto_listing",
                confidence=0.9,
                response_time=response.response_time,
                metadata={
                    "active_templates": len(self.listing_templates),
                    "active_listings": len(self.active_listings),
                    "optimization_enabled": self.auto_optimization_enabled,
                },
            )

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return UnifiedAgentResponse(
                content="I'm having trouble processing your listing request right now. Please try again.",
                agent_type="auto_listing",
                confidence=0.1,
                response_time=0.0,
            )
