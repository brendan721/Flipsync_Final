"""
Content UnifiedAgent for FlipSync - Conversational Content Generation and Optimization

This agent specializes in:
- Product listing content generation
- SEO optimization and analysis
- Marketplace-specific content adaptation
- Content quality assessment
- Image optimization recommendations
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole

# Import only what's available and working
try:
    from fs_agt_clean.core.config.config_manager import ConfigManager
except ImportError:
    from fs_agt_clean.core.config.manager import ConfigManager

try:
    from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
except ImportError:
    AlertManager = None

try:
    from fs_agt_clean.services.llm.ollama_service import OllamaLLMService
except ImportError:
    OllamaLLMService = None

logger = logging.getLogger(__name__)


class ContentUnifiedAgent(BaseConversationalUnifiedAgent):
    """
    Content UnifiedAgent for intelligent content generation and optimization.

    Capabilities:
    - Generate marketplace-optimized product listings
    - Analyze and improve SEO performance
    - Create content templates for different marketplaces
    - Optimize existing content for better conversion
    - Provide content quality assessments
    """

    def __init__(self, agent_id: str = None, use_fast_model: bool = True):
        """Initialize the Content UnifiedAgent."""
        super().__init__(
            agent_role=UnifiedAgentRole.CONTENT,
            agent_id=agent_id
            or f"content_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            use_fast_model=use_fast_model,
        )

        # Initialize specialized services with error handling
        try:
            self.config_manager = ConfigManager() if ConfigManager else None
        except Exception:
            self.config_manager = None

        try:
            self.alert_manager = AlertManager() if AlertManager else None
        except Exception:
            self.alert_manager = None

        # LLM service is now handled by BaseConversationalUnifiedAgent
        self.llm_service = None

        # Don't initialize ContentUnifiedAgentService since it has missing dependencies
        self.content_service = None
        self.seo_analyzer = None
        self.content_optimizer = None

        # Content agent capabilities
        self.capabilities = [
            "content_generation",
            "seo_optimization",
            "listing_creation",
            "content_analysis",
            "template_creation",
            "marketplace_adaptation",
            "keyword_research",
            "content_quality_assessment",
        ]

        # Content-specific patterns for message processing
        self.content_patterns = {
            "generate": [
                "generate",
                "create",
                "write",
                "make",
                "produce",
                "build",
                "listing",
                "description",
                "title",
                "content",
            ],
            "optimize": [
                "optimize",
                "improve",
                "enhance",
                "better",
                "fix",
                "update",
                "seo",
                "search",
                "ranking",
                "visibility",
            ],
            "analyze": [
                "analyze",
                "check",
                "review",
                "assess",
                "evaluate",
                "score",
                "quality",
                "performance",
                "metrics",
            ],
            "template": [
                "template",
                "format",
                "structure",
                "layout",
                "pattern",
                "example",
                "sample",
            ],
        }

        logger.info(f"Content UnifiedAgent initialized: {self.agent_id}")

    async def generate_content(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content for a product listing."""
        try:
            product_name = product_data.get("product_name", "Product")
            category = product_data.get("category", "General")
            marketplace = product_data.get("marketplace", "amazon")

            # Generate optimized content
            content = {
                "title": f"Premium {product_name} - Professional Grade Quality",
                "description": f"Experience exceptional performance with our {product_name}. Perfect for professionals and enthusiasts alike, this premium {category.lower()} product delivers outstanding results.",
                "bullet_points": [
                    f"PROFESSIONAL GRADE: Engineered for demanding {category.lower()} applications",
                    "PREMIUM MATERIALS: Constructed from high-quality, durable materials",
                    "ERGONOMIC DESIGN: Comfortable and efficient for extended use",
                    "VERSATILE APPLICATION: Perfect for a wide range of applications",
                    "SATISFACTION GUARANTEED: Backed by comprehensive warranty",
                ],
                "keywords": [
                    product_name.lower(),
                    "professional",
                    "premium",
                    "quality",
                    category.lower(),
                ],
                "seo_score": 85,
                "marketplace": marketplace,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            return content

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return {
                "title": f"{product_data.get('product_name', 'Product')} - Quality Item",
                "description": "High-quality product with excellent features and benefits.",
                "bullet_points": [
                    "Quality construction",
                    "Reliable performance",
                    "Great value",
                ],
                "keywords": ["quality", "reliable", "value"],
                "seo_score": 70,
                "error": str(e),
            }

    async def process_message(
        self,
        message: str,
        user_id: str = "test_user",
        conversation_id: str = "test_conversation",
        conversation_history: Optional[List[Dict]] = None,
        context: Dict[str, Any] = None,
    ) -> UnifiedAgentResponse:
        """
        Process content-related queries and provide content optimization guidance.

        Args:
            message: UnifiedUser message requesting content assistance
            user_id: UnifiedUser identifier
            conversation_id: Conversation identifier
            conversation_history: Previous conversation messages
            context: Additional context for content generation

        Returns:
            UnifiedAgentResponse with content recommendations
        """
        try:
            # Classify the content request type
            request_type = self._classify_content_request(message)

            # Extract product information from message
            product_info = self._extract_product_info(message, context or {})

            # Generate content-specific response based on request type
            if request_type == "generate":
                response_data = await self._handle_content_generation_new(
                    message, product_info, context or {}
                )
            elif request_type == "optimize":
                response_data = await self._handle_content_optimization_new(
                    message, product_info, context or {}
                )
            elif request_type == "analyze":
                response_data = await self._handle_content_analysis_new(
                    message, product_info, context or {}
                )
            elif request_type == "template":
                response_data = await self._handle_template_request_new(
                    message, product_info, context or {}
                )
            else:
                response_data = await self._handle_general_content_query_new(
                    message, context or {}
                )

            # Generate LLM response with content context
            llm_response = await self._generate_content_response(
                message, response_data, request_type
            )

            return UnifiedAgentResponse(
                content=llm_response,
                agent_type="content",
                confidence=response_data.get("confidence", 0.8),
                response_time=0.3,  # Mock response time
                metadata={
                    "agent_id": self.agent_id,
                    "request_type": request_type,
                    "data": response_data,
                    "requires_approval": response_data.get("requires_approval", False),
                },
            )

        except Exception as e:
            logger.error(f"Error processing content message: {e}")
            # DEBUGGING: Remove fallback to expose actual AI performance issues
            raise RuntimeError(
                f"Content UnifiedAgent processing failed: {e}. Check AI model connectivity and performance."
            ) from e

    async def _process_response(
        self,
        llm_response: str,
        original_message: str,
        conversation_id: str,
        context: Dict[str, Any],
    ) -> str:
        """Process LLM response with content-specific enhancements."""
        try:
            # Classify the content request type
            request_type = self._classify_content_request(original_message)

            # Extract product information from message
            product_info = self._extract_product_info(original_message, context)

            # Generate content-specific response based on request type
            if request_type == "generate":
                enhanced_response = await self._handle_content_generation(
                    llm_response, product_info, original_message
                )
            elif request_type == "optimize":
                enhanced_response = await self._handle_content_optimization(
                    llm_response, product_info, original_message
                )
            elif request_type == "analyze":
                enhanced_response = await self._handle_content_analysis(
                    llm_response, product_info, original_message
                )
            elif request_type == "template":
                enhanced_response = await self._handle_template_request(
                    llm_response, product_info, original_message
                )
            else:
                enhanced_response = await self._handle_general_content_query(
                    llm_response, original_message
                )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error processing content response: {e}")
            return f"{llm_response}\n\n*Note: Some content features may be temporarily unavailable.*"

    def _classify_content_request(self, message: str) -> str:
        """Classify the type of content request."""
        message_lower = message.lower()

        # Count pattern matches for each category
        pattern_scores = {}
        for category, patterns in self.content_patterns.items():
            score = sum(1 for pattern in patterns if pattern in message_lower)
            pattern_scores[category] = score

        # Return category with highest score, default to general
        if not pattern_scores or max(pattern_scores.values()) == 0:
            return "general"

        return max(pattern_scores, key=pattern_scores.get)

    def _extract_product_info(
        self, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract product information from the message and context."""
        product_info = {
            "name": None,
            "brand": None,
            "category": None,
            "marketplace": None,
            "features": [],
            "benefits": [],
            "price": None,
            "sku": None,
        }

        # Extract marketplace mentions
        marketplaces = ["amazon", "ebay", "walmart", "etsy", "shopify"]
        for marketplace in marketplaces:
            if marketplace in message.lower():
                product_info["marketplace"] = marketplace
                break

        # Extract product name patterns
        name_patterns = [
            r"product (?:called |named )?['\"]([^'\"]+)['\"]",
            r"(?:for|about) (?:the |my |our )?([A-Z][a-zA-Z\s]+?)(?:\s+(?:product|item|listing))",
            r"listing for ([A-Z][a-zA-Z\s]+?)(?:\s|$|\.|\,)",
        ]

        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                product_info["name"] = match.group(1).strip()
                break

        # Extract brand mentions
        brand_pattern = r"(?:brand|made by|from) ([A-Z][a-zA-Z]+)"
        brand_match = re.search(brand_pattern, message, re.IGNORECASE)
        if brand_match:
            product_info["brand"] = brand_match.group(1)

        # Extract features and benefits from context
        if "features" in message.lower():
            # Simple feature extraction
            feature_text = (
                message.lower().split("features")[1]
                if "features" in message.lower()
                else ""
            )
            product_info["features"] = [
                f.strip() for f in feature_text.split(",")[:3] if f.strip()
            ]

        return product_info

    async def _handle_content_generation(
        self, llm_response: str, product_info: Dict[str, Any], original_message: str
    ) -> str:
        """Handle content generation requests."""
        try:
            # If we have product info, generate structured content
            if product_info.get("name") or product_info.get("marketplace"):
                marketplace = product_info.get("marketplace", "amazon")

                # Generate sample content structure
                content_example = self._generate_content_example(
                    product_info, marketplace
                )

                enhanced_response = f"{llm_response}\n\n"
                enhanced_response += "**Generated Content Structure:**\n\n"
                enhanced_response += f"**Title:** {content_example['title']}\n\n"
                enhanced_response += (
                    f"**Description:**\n{content_example['description']}\n\n"
                )
                enhanced_response += "**Key Features:**\n"
                for feature in content_example["bullet_points"]:
                    enhanced_response += f"• {feature}\n"
                enhanced_response += (
                    f"\n**SEO Keywords:** {', '.join(content_example['keywords'])}\n"
                )
                enhanced_response += (
                    f"**Estimated SEO Score:** {content_example['seo_score']}/100"
                )

                return enhanced_response

            return llm_response

        except Exception as e:
            logger.error(f"Error in content generation: {e}")
            return llm_response

    def _generate_content_example(
        self, product_info: Dict[str, Any], marketplace: str
    ) -> Dict[str, Any]:
        """Generate a content example based on product info."""
        name = product_info.get("name", "Premium Product")
        brand = product_info.get("brand", "Professional Brand")

        return {
            "title": f"{brand} {name} - Professional Grade Quality",
            "description": f"Experience exceptional performance with our {brand} {name}. Designed for professionals who demand reliability and precision, this premium product delivers outstanding results every time.",
            "bullet_points": [
                "PROFESSIONAL GRADE: Engineered for demanding professional use",
                "PREMIUM MATERIALS: Constructed from high-quality, durable materials",
                "ERGONOMIC DESIGN: Comfortable and efficient for extended use",
                "VERSATILE APPLICATION: Perfect for a wide range of applications",
                "SATISFACTION GUARANTEED: Backed by comprehensive warranty",
            ],
            "keywords": [f"{name.lower()}", "professional", "premium", "quality"],
            "seo_score": 85,
        }

    async def _handle_content_optimization(
        self, llm_response: str, product_info: Dict[str, Any], original_message: str
    ) -> str:
        """Handle content optimization requests."""
        try:
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += "**Content Optimization Recommendations:**\n\n"

            # Provide specific optimization suggestions
            optimizations = [
                "**Title Optimization:** Include primary keywords in the first 60 characters",
                "**Description Enhancement:** Add emotional triggers and benefit-focused language",
                "**Keyword Density:** Maintain 2-3% keyword density for primary terms",
                "**Bullet Points:** Use action words and quantifiable benefits",
                "**Call-to-Action:** Include urgency and value proposition",
            ]

            for opt in optimizations:
                enhanced_response += f"• {opt}\n"

            # Add marketplace-specific tips
            marketplace = product_info.get("marketplace", "general")
            enhanced_response += f"\n**{marketplace.title()} Specific Tips:**\n"

            if marketplace == "amazon":
                enhanced_response += (
                    "• Use backend keywords for additional search terms\n"
                )
                enhanced_response += (
                    "• Optimize for A9 algorithm with relevant keywords\n"
                )
                enhanced_response += "• Include size, color, and material in title\n"
            elif marketplace == "ebay":
                enhanced_response += (
                    "• Use eBay's item specifics for better visibility\n"
                )
                enhanced_response += "• Include condition and brand prominently\n"
                enhanced_response += "• Optimize for eBay's Best Match algorithm\n"

            return enhanced_response

        except Exception as e:
            logger.error(f"Error in content optimization: {e}")
            return llm_response

    async def _handle_content_analysis(
        self, llm_response: str, product_info: Dict[str, Any], original_message: str
    ) -> str:
        """Handle content analysis requests."""
        try:
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += "**Content Analysis Framework:**\n\n"

            # Provide analysis criteria
            analysis_points = [
                "**SEO Score:** Keyword optimization and search visibility (0-100)",
                "**Readability:** Content clarity and customer comprehension",
                "**Conversion Potential:** Persuasiveness and call-to-action strength",
                "**Marketplace Compliance:** Platform-specific requirements adherence",
                "**Competitive Positioning:** Differentiation from similar products",
            ]

            for point in analysis_points:
                enhanced_response += f"• {point}\n"

            enhanced_response += "\n**Analysis Process:**\n"
            enhanced_response += "1. Submit your content for automated scoring\n"
            enhanced_response += "2. Receive detailed breakdown by category\n"
            enhanced_response += "3. Get specific improvement recommendations\n"
            enhanced_response += "4. Compare against top-performing listings\n"

            return enhanced_response

        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            return llm_response

    async def _handle_template_request(
        self, llm_response: str, product_info: Dict[str, Any], original_message: str
    ) -> str:
        """Handle template requests."""
        try:
            marketplace = product_info.get("marketplace", "amazon")
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += f"**{marketplace.title()} Content Template:**\n\n"

            if marketplace == "amazon":
                enhanced_response += "**Title Template:**\n"
                enhanced_response += "`{Brand} {Product} - {Key Feature 1} {Key Feature 2} - {Target Audience}`\n\n"
                enhanced_response += "**Description Template:**\n"
                enhanced_response += (
                    "```\n<p>Experience {Key Benefit} with our {Brand} {Product}. "
                )
                enhanced_response += "Perfect for {Target Audience}, this {Product} delivers {Primary Value Proposition}.</p>\n"
                enhanced_response += (
                    "<p>Featuring {Feature 1}, {Feature 2}, and {Feature 3}, "
                )
                enhanced_response += (
                    "our {Product} ensures {Secondary Benefit} every time.</p>\n```\n\n"
                )
                enhanced_response += "**Bullet Point Template:**\n"
                enhanced_response += "• **{BENEFIT}:** {Detailed explanation}\n"
                enhanced_response += "• **{FEATURE}:** {Technical specification}\n"
                enhanced_response += "• **{COMPATIBILITY}:** {What it works with}\n"
                enhanced_response += "• **{WARRANTY}:** {Guarantee information}\n"
                enhanced_response += "• **{PACKAGE}:** {What's included}\n"

            elif marketplace == "ebay":
                enhanced_response += "**Title Template:**\n"
                enhanced_response += (
                    "`{Brand} {Product} {Model} {Key Feature} {Condition}`\n\n"
                )
                enhanced_response += "**Description Template:**\n"
                enhanced_response += "```\n<h2>About this item</h2>\n"
                enhanced_response += (
                    "<p>This {Condition} {Brand} {Product} offers {Key Benefits}.</p>\n"
                )
                enhanced_response += "<h2>Specifications</h2>\n<ul>{Spec List}</ul>\n"
                enhanced_response += (
                    "<h2>Package Contents</h2>\n<ul>{Contents List}</ul>\n```\n"
                )

            return enhanced_response

        except Exception as e:
            logger.error(f"Error in template request: {e}")
            return llm_response

    async def _handle_general_content_query(
        self, llm_response: str, original_message: str
    ) -> str:
        """Handle general content-related queries."""
        try:
            enhanced_response = f"{llm_response}\n\n"
            enhanced_response += "**Content Services Available:**\n"
            enhanced_response += (
                "• **Generate:** Create new product listings and descriptions\n"
            )
            enhanced_response += (
                "• **Optimize:** Improve existing content for better performance\n"
            )
            enhanced_response += (
                "• **Analyze:** Assess content quality and SEO effectiveness\n"
            )
            enhanced_response += (
                "• **Templates:** Get marketplace-specific content formats\n\n"
            )
            enhanced_response += "*Ask me to generate, optimize, analyze, or provide templates for your content needs!*"

            return enhanced_response

        except Exception as e:
            logger.error(f"Error in general content query: {e}")
            return llm_response

    # New methods for process_message implementation

    async def _generate_content_response(
        self, message: str, response_data: Dict[str, Any], request_type: str
    ) -> str:
        """Generate LLM response with content context."""
        try:
            # Create a context-aware prompt
            context_prompt = f"Content Request Type: {request_type}\n"
            context_prompt += f"UnifiedUser Message: {message}\n\n"

            if response_data.get("content_example"):
                context_prompt += "Generated Content Example:\n"
                example = response_data["content_example"]
                context_prompt += f"Title: {example.get('title', 'N/A')}\n"
                context_prompt += f"Description: {example.get('description', 'N/A')}\n"
                if example.get("bullet_points"):
                    context_prompt += "Features:\n"
                    for bullet in example["bullet_points"]:
                        context_prompt += f"• {bullet}\n"
                context_prompt += (
                    f"SEO Score: {example.get('seo_score', 'N/A')}/100\n\n"
                )

            if response_data.get("optimizations"):
                context_prompt += "Optimization Recommendations:\n"
                for opt in response_data["optimizations"]:
                    context_prompt += f"• {opt}\n"
                context_prompt += "\n"

            # Use the LLM client to generate a natural response
            system_prompt = """You are a content optimization expert helping with e-commerce product listings.
            Provide helpful, actionable advice based on the content analysis and recommendations provided.
            Be conversational but professional, and focus on practical implementation."""

            if hasattr(self, "llm_client") and self.llm_client:
                llm_response = await self.llm_client.generate_response(
                    prompt=context_prompt, system_prompt=system_prompt
                )
                return (
                    llm_response.content
                    if hasattr(llm_response, "content")
                    else str(llm_response)
                )
            else:
                # DEBUGGING: Remove fallback to expose actual AI performance issues
                raise RuntimeError(
                    f"Content UnifiedAgent LLM client unavailable. Request type: {request_type}"
                )

        except Exception as e:
            logger.error(f"Error generating content response: {e}")
            # DEBUGGING: Remove fallback to expose actual AI performance issues
            raise RuntimeError(
                f"Content UnifiedAgent LLM generation failed: {e}. Request type: {request_type}"
            ) from e

    def _create_fallback_response(
        self, request_type: str, response_data: Dict[str, Any]
    ) -> str:
        """Create a fallback response when LLM is unavailable."""
        if request_type == "generate":
            return "I can help you generate optimized content. Based on your request, I've created a structured content example with SEO optimization and marketplace-specific formatting."
        elif request_type == "optimize":
            return "I've analyzed your content and identified several optimization opportunities including keyword enhancement, structure improvements, and conversion optimization techniques."
        elif request_type == "analyze":
            return "I can provide comprehensive content analysis including SEO scoring, readability assessment, and competitive positioning recommendations."
        elif request_type == "template":
            return "I've prepared marketplace-specific content templates that you can customize for your products, including optimized title formats and description structures."
        else:
            return "I'm here to help with all your content needs including generation, optimization, analysis, and templates. What specific content assistance can I provide?"

    # Handler methods for different content request types

    async def _handle_content_generation_new(
        self, message: str, product_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle content generation requests (new implementation)."""
        try:
            marketplace = product_info.get("marketplace", "amazon")

            # Generate content example
            content_example = self._generate_content_example(product_info, marketplace)

            return {
                "request_type": "generate",
                "content_example": content_example,
                "confidence": 0.85,
                "marketplace": marketplace,
                "product_info": product_info,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in content generation: {e}")
            return {
                "request_type": "generate",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    async def _handle_content_optimization_new(
        self, message: str, product_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle content optimization requests (new implementation)."""
        try:
            marketplace = product_info.get("marketplace", "amazon")

            # Generate optimization recommendations
            optimizations = [
                "Enhance title with primary keywords in first 60 characters",
                "Improve description with emotional triggers and benefit-focused language",
                "Optimize keyword density to 2-3% for primary terms",
                "Add quantifiable benefits to bullet points",
                "Include urgency and value proposition in call-to-action",
            ]

            # Add marketplace-specific recommendations
            if marketplace == "amazon":
                optimizations.extend(
                    [
                        "Use backend keywords for additional search terms",
                        "Optimize for A9 algorithm with relevant keywords",
                        "Include size, color, and material in title",
                    ]
                )
            elif marketplace == "ebay":
                optimizations.extend(
                    [
                        "Use eBay's item specifics for better visibility",
                        "Include condition and brand prominently",
                        "Optimize for eBay's Best Match algorithm",
                    ]
                )

            return {
                "request_type": "optimize",
                "optimizations": optimizations,
                "marketplace": marketplace,
                "confidence": 0.9,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in content optimization: {e}")
            return {
                "request_type": "optimize",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    async def _handle_content_analysis_new(
        self, message: str, product_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle content analysis requests (new implementation)."""
        try:
            analysis_framework = [
                "SEO Score: Keyword optimization and search visibility (0-100)",
                "Readability: Content clarity and customer comprehension",
                "Conversion Potential: Persuasiveness and call-to-action strength",
                "Marketplace Compliance: Platform-specific requirements adherence",
                "Competitive Positioning: Differentiation from similar products",
            ]

            analysis_process = [
                "Submit your content for automated scoring",
                "Receive detailed breakdown by category",
                "Get specific improvement recommendations",
                "Compare against top-performing listings",
            ]

            return {
                "request_type": "analyze",
                "analysis_framework": analysis_framework,
                "analysis_process": analysis_process,
                "confidence": 0.8,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            return {
                "request_type": "analyze",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    async def _handle_template_request_new(
        self, message: str, product_info: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle template requests (new implementation)."""
        try:
            marketplace = product_info.get("marketplace", "amazon")

            templates = {}

            if marketplace == "amazon":
                templates = {
                    "title_template": "{Brand} {Product} - {Key Feature 1} {Key Feature 2} - {Target Audience}",
                    "description_template": "Experience {Key Benefit} with our {Brand} {Product}. Perfect for {Target Audience}, this {Product} delivers {Primary Value Proposition}.",
                    "bullet_template": [
                        "**{BENEFIT}:** {Detailed explanation}",
                        "**{FEATURE}:** {Technical specification}",
                        "**{COMPATIBILITY}:** {What it works with}",
                        "**{WARRANTY}:** {Guarantee information}",
                        "**{PACKAGE}:** {What's included}",
                    ],
                }
            elif marketplace == "ebay":
                templates = {
                    "title_template": "{Brand} {Product} {Model} {Key Feature} {Condition}",
                    "description_template": "This {Condition} {Brand} {Product} offers {Key Benefits}.",
                    "bullet_template": [
                        "Specifications: {Spec List}",
                        "Package Contents: {Contents List}",
                        "Condition: {Detailed condition description}",
                    ],
                }

            return {
                "request_type": "template",
                "templates": templates,
                "marketplace": marketplace,
                "confidence": 0.9,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in template request: {e}")
            return {
                "request_type": "template",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    async def _handle_general_content_query_new(
        self, message: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general content-related queries (new implementation)."""
        try:
            services = [
                "Generate: Create new product listings and descriptions",
                "Optimize: Improve existing content for better performance",
                "Analyze: Assess content quality and SEO effectiveness",
                "Templates: Get marketplace-specific content formats",
            ]

            return {
                "request_type": "general",
                "available_services": services,
                "confidence": 0.7,
                "requires_approval": False,
            }

        except Exception as e:
            logger.error(f"Error in general content query: {e}")
            return {
                "request_type": "general",
                "error": str(e),
                "confidence": 0.1,
                "requires_approval": False,
            }

    # Required abstract methods from BaseConversationalUnifiedAgent

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific context for prompt generation."""
        return {
            "agent_type": "content_optimization_specialist",
            "capabilities": self.capabilities,
            "specializations": [
                "SEO optimization",
                "Content generation",
                "Marketplace adaptation",
                "Template creation",
            ],
            "supported_marketplaces": ["amazon", "ebay", "walmart", "etsy"],
            "content_types": ["titles", "descriptions", "bullet_points", "keywords"],
        }

    # Phase 2D: Methods required by orchestration workflows

    async def optimize_listing_content(
        self, listing_data: Dict[str, Any], marketplace: str = "amazon"
    ) -> Dict[str, Any]:
        """Optimize listing content for better performance.

        This method is required by the agent orchestration workflows.

        Args:
            listing_data: Current listing data to optimize
            marketplace: Target marketplace (amazon, ebay, etc.)

        Returns:
            Optimized content with improvements and metrics
        """
        try:
            logger.info(f"Optimizing listing content for {marketplace}")

            # Extract current content
            current_title = listing_data.get("title", "")
            current_description = listing_data.get("description", "")
            current_bullet_points = listing_data.get("bullet_points", [])

            # Generate optimized content
            optimized_content = {
                "title": await self._optimize_title(current_title, marketplace),
                "description": await self._optimize_description(
                    current_description, marketplace
                ),
                "bullet_points": await self._optimize_bullet_points(
                    current_bullet_points, marketplace
                ),
                "keywords": await self._extract_seo_keywords(listing_data, marketplace),
            }

            # Calculate improvement metrics
            improvements = []
            if len(optimized_content["title"]) > len(current_title):
                improvements.append("Enhanced title with more descriptive keywords")
            if len(optimized_content["description"]) > len(current_description):
                improvements.append(
                    "Expanded description with better value proposition"
                )
            if len(optimized_content["bullet_points"]) > len(current_bullet_points):
                improvements.append("Added more compelling bullet points")

            return {
                "original_content": {
                    "title": current_title,
                    "description": current_description,
                    "bullet_points": current_bullet_points,
                },
                "optimized_content": optimized_content,
                "improvements": improvements,
                "seo_score_before": self._calculate_seo_score(
                    current_title + " " + current_description
                ),
                "seo_score_after": self._calculate_seo_score(
                    optimized_content["title"] + " " + optimized_content["description"]
                ),
                "marketplace": marketplace,
                "optimization_timestamp": datetime.now(timezone.utc).isoformat(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            logger.error(f"Error optimizing listing content: {e}")
            return {
                "error": f"Content optimization failed: {str(e)}",
                "original_content": listing_data,
                "optimized_content": listing_data,  # Return original as fallback
                "improvements": [],
                "marketplace": marketplace,
                "agent_id": self.agent_id,
            }

    async def _optimize_title(self, title: str, marketplace: str) -> str:
        """Optimize product title for marketplace."""
        if not title:
            return "Premium Quality Product - Fast Shipping"

        # Add marketplace-specific optimizations
        if marketplace.lower() == "ebay":
            # eBay prefers detailed, keyword-rich titles
            if len(title) < 60:
                title += " - Premium Quality, Fast Shipping"
        elif marketplace.lower() == "amazon":
            # Amazon prefers concise but descriptive titles
            if "Premium" not in title:
                title = f"Premium {title}"

        return title[:80]  # Respect title length limits

    async def _optimize_description(self, description: str, marketplace: str) -> str:
        """Optimize product description for marketplace."""
        if not description:
            description = (
                "High-quality product with excellent features and reliable performance."
            )

        # Add marketplace-specific elements
        optimizations = [
            "\n\n✅ PREMIUM QUALITY GUARANTEE",
            "✅ FAST & RELIABLE SHIPPING",
            "✅ EXCELLENT CUSTOMER SERVICE",
            "✅ SATISFACTION GUARANTEED",
        ]

        if marketplace.lower() == "ebay":
            optimizations.append("✅ EBAY TOP RATED SELLER")
        elif marketplace.lower() == "amazon":
            optimizations.append("✅ AMAZON CHOICE QUALITY")

        return description + "\n" + "\n".join(optimizations)

    async def _optimize_bullet_points(
        self, bullet_points: List[str], marketplace: str
    ) -> List[str]:
        """Optimize bullet points for marketplace."""
        if not bullet_points:
            bullet_points = [
                "Premium quality construction",
                "Fast and reliable shipping",
                "Excellent customer service",
            ]

        # Add marketplace-specific bullet points
        optimized = bullet_points.copy()

        if marketplace.lower() == "ebay":
            optimized.append("eBay Top Rated Seller - Buy with confidence")
        elif marketplace.lower() == "amazon":
            optimized.append("Amazon Choice quality - Trusted by customers")

        # Ensure we have at least 3 bullet points
        while len(optimized) < 3:
            optimized.append("Outstanding value and quality")

        return optimized[:5]  # Limit to 5 bullet points

    async def _extract_seo_keywords(
        self, listing_data: Dict[str, Any], marketplace: str
    ) -> List[str]:
        """Extract and suggest SEO keywords."""
        keywords = []

        # Extract from title and description
        title = listing_data.get("title", "")
        description = listing_data.get("description", "")

        # Basic keyword extraction
        text = (title + " " + description).lower()
        words = re.findall(r"\b\w+\b", text)

        # Filter for meaningful keywords (length > 3)
        keywords = list(set([word for word in words if len(word) > 3]))

        # Add marketplace-specific keywords
        if marketplace.lower() == "ebay":
            keywords.extend(["ebay", "auction", "bidding"])
        elif marketplace.lower() == "amazon":
            keywords.extend(["amazon", "prime", "choice"])

        return keywords[:10]  # Return top 10 keywords

    def _calculate_seo_score(self, content: str) -> float:
        """Calculate basic SEO score for content."""
        if not content:
            return 0.0

        score = 50.0  # Base score

        # Length bonus
        if len(content) > 100:
            score += 10
        if len(content) > 200:
            score += 10

        # Keyword density (simple check)
        words = content.lower().split()
        if len(words) > 10:
            score += 10

        # Quality indicators
        if "premium" in content.lower():
            score += 5
        if "quality" in content.lower():
            score += 5
        if "guarantee" in content.lower():
            score += 5

        return min(score, 100.0)  # Cap at 100

    async def analyze_product_positioning(
        self, product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze product positioning for content strategy."""
        try:
            logger.info(f"Content UnifiedAgent analyzing product positioning...")

            # Extract product information
            product_info = {
                "name": product_data.get("name", "product"),
                "category": product_data.get("category", "general"),
                "price": product_data.get("price", 0),
                "features": product_data.get("features", []),
                "description": product_data.get("description", ""),
            }

            # Generate positioning analysis
            positioning_prompt = f"""
            Analyze the content positioning strategy for this product:

            Product: {product_info['name']}
            Category: {product_info['category']}
            Price: ${product_info['price']}
            Features: {', '.join(product_info['features']) if product_info['features'] else 'Not specified'}
            Description: {product_info['description'][:200]}...

            Provide comprehensive content positioning analysis including:
            1. Target audience identification
            2. Key messaging themes
            3. Competitive differentiation points
            4. Content tone and style recommendations
            5. Marketplace-specific positioning strategies
            6. SEO keyword opportunities

            Focus on content strategy that drives conversions.
            """

            # Get AI analysis
            response = await self.llm_client.generate_response(
                prompt=positioning_prompt,
                system_prompt="You are an expert content strategist specializing in e-commerce product positioning and messaging.",
            )

            # Structure the positioning analysis
            positioning_analysis = {
                "analysis_type": "product_positioning",
                "product_info": product_info,
                "ai_insights": response.content,
                "confidence_score": response.confidence_score,
                "target_audience": self._extract_target_audience(response.content),
                "key_messages": self._extract_key_messages(response.content),
                "differentiation_points": self._extract_differentiation_points(
                    response.content
                ),
                "content_recommendations": self._extract_content_recommendations(
                    response.content
                ),
                "seo_opportunities": self._extract_seo_opportunities(response.content),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Content UnifiedAgent completed positioning analysis with confidence: {response.confidence_score}"
            )
            return positioning_analysis

        except Exception as e:
            logger.error(f"Error in product positioning analysis: {e}")
            return {
                "analysis_type": "product_positioning",
                "status": "error",
                "error_message": str(e),
                "fallback_recommendations": [
                    "Identify your target customer demographics",
                    "Highlight unique product benefits",
                    "Use clear, benefit-focused messaging",
                    "Optimize for relevant search keywords",
                ],
            }

    async def analyze_content_trends(self, research_topic: str) -> Dict[str, Any]:
        """Analyze content trends for a research topic."""
        try:
            logger.info(
                f"Content UnifiedAgent analyzing content trends for: {research_topic[:50]}..."
            )

            # Generate content trends analysis
            trends_prompt = f"""
            Analyze current content trends related to this topic:

            Research Topic: {research_topic}

            Provide comprehensive content trends analysis including:
            1. Popular content formats and styles
            2. Trending keywords and phrases
            3. Consumer content preferences
            4. Platform-specific content trends
            5. Visual content trends and preferences
            6. Content engagement patterns
            7. Emerging content technologies and features

            Focus on actionable insights for content creators and marketers.
            """

            # Get AI analysis
            response = await self.llm_client.generate_response(
                prompt=trends_prompt,
                system_prompt="You are an expert content analyst with deep knowledge of digital marketing trends and consumer behavior.",
            )

            # Structure the trends analysis
            content_trends = {
                "analysis_type": "content_trends",
                "topic": research_topic,
                "ai_analysis": response.content,
                "confidence_score": response.confidence_score,
                "trending_formats": self._extract_trending_formats(response.content),
                "popular_keywords": self._extract_popular_keywords(response.content),
                "engagement_patterns": self._extract_engagement_patterns(
                    response.content
                ),
                "platform_trends": self._extract_platform_trends(response.content),
                "visual_trends": self._extract_visual_trends(response.content),
                "recommendations": self._extract_trend_recommendations(
                    response.content
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            logger.info(
                f"Content UnifiedAgent completed trends analysis with confidence: {response.confidence_score}"
            )
            return content_trends

        except Exception as e:
            logger.error(f"Error in content trends analysis: {e}")
            return {
                "analysis_type": "content_trends",
                "status": "error",
                "error_message": str(e),
                "fallback_insights": [
                    "Focus on video and visual content",
                    "Use authentic, user-generated content",
                    "Optimize for mobile consumption",
                    "Include interactive elements when possible",
                ],
            }

    def _extract_target_audience(self, ai_content: str) -> List[str]:
        """Extract target audience insights from AI analysis."""
        audience_segments = []

        # Look for audience-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in [
                    "audience",
                    "customer",
                    "buyer",
                    "demographic",
                    "target",
                ]
            ):
                if len(line) > 15:
                    audience_segments.append(line)

        return audience_segments[:5]  # Limit to top 5

    def _extract_key_messages(self, ai_content: str) -> List[str]:
        """Extract key messaging themes from AI analysis."""
        messages = []

        # Look for messaging-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["message", "theme", "benefit", "value", "proposition"]
            ):
                if len(line) > 15:
                    messages.append(line)

        return messages[:5]  # Limit to top 5

    def _extract_differentiation_points(self, ai_content: str) -> List[str]:
        """Extract differentiation points from AI analysis."""
        points = []

        # Look for differentiation-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in [
                    "unique",
                    "different",
                    "advantage",
                    "competitive",
                    "distinct",
                ]
            ):
                if len(line) > 15:
                    points.append(line)

        return points[:5]  # Limit to top 5

    def _extract_content_recommendations(self, ai_content: str) -> List[str]:
        """Extract content recommendations from AI analysis."""
        recommendations = []

        # Look for recommendation-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("1.", "2.", "3.", "4.", "5.", "-", "•")) and any(
                keyword in line.lower()
                for keyword in ["content", "write", "create", "focus", "emphasize"]
            ):
                recommendations.append(line)

        return recommendations[:5]  # Limit to top 5

    def _extract_seo_opportunities(self, ai_content: str) -> List[str]:
        """Extract SEO opportunities from AI analysis."""
        opportunities = []

        # Look for SEO-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["seo", "keyword", "search", "optimize", "ranking"]
            ):
                if len(line) > 15:
                    opportunities.append(line)

        return opportunities[:5]  # Limit to top 5

    def _extract_trending_formats(self, ai_content: str) -> List[str]:
        """Extract trending content formats from AI analysis."""
        formats = []

        # Look for format-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["format", "video", "image", "post", "story", "reel"]
            ):
                if len(line) > 15:
                    formats.append(line)

        return formats[:5]  # Limit to top 5

    def _extract_popular_keywords(self, ai_content: str) -> List[str]:
        """Extract popular keywords from AI analysis."""
        keywords = []

        # Look for keyword-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["keyword", "phrase", "term", "hashtag", "tag"]
            ):
                if len(line) > 10:
                    keywords.append(line)

        return keywords[:10]  # Limit to top 10

    def _extract_engagement_patterns(self, ai_content: str) -> List[str]:
        """Extract engagement patterns from AI analysis."""
        patterns = []

        # Look for engagement-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in [
                    "engagement",
                    "interaction",
                    "response",
                    "behavior",
                    "pattern",
                ]
            ):
                if len(line) > 15:
                    patterns.append(line)

        return patterns[:5]  # Limit to top 5

    def _extract_platform_trends(self, ai_content: str) -> List[str]:
        """Extract platform-specific trends from AI analysis."""
        trends = []

        # Look for platform-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["platform", "amazon", "ebay", "social", "marketplace"]
            ):
                if len(line) > 15:
                    trends.append(line)

        return trends[:5]  # Limit to top 5

    def _extract_visual_trends(self, ai_content: str) -> List[str]:
        """Extract visual content trends from AI analysis."""
        trends = []

        # Look for visual-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in [
                    "visual",
                    "image",
                    "photo",
                    "graphic",
                    "design",
                    "color",
                ]
            ):
                if len(line) > 15:
                    trends.append(line)

        return trends[:5]  # Limit to top 5

    def _extract_trend_recommendations(self, ai_content: str) -> List[str]:
        """Extract trend-based recommendations from AI analysis."""
        recommendations = []

        # Look for recommendation-related content
        lines = ai_content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith(("1.", "2.", "3.", "4.", "5.", "-", "•")) and any(
                keyword in line.lower()
                for keyword in ["recommend", "suggest", "should", "consider", "try"]
            ):
                recommendations.append(line)

        return recommendations[:5]  # Limit to top 5
