"""Enhanced listing content agent for marketplace-optimized content generation."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.agents.content.base_content_agent import BaseContentUnifiedAgent
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer

logger = logging.getLogger(__name__)


class ListingContentUnifiedAgent(BaseContentUnifiedAgent):
    """
    Enhanced agent for generating and optimizing marketplace listing content.

    Capabilities:
    - SEO-optimized title generation
    - Compelling product descriptions
    - Bullet point optimization
    - Keyword integration
    - Marketplace-specific formatting
    - A/B testing content variants
    """

    def __init__(
        self,
        marketplace: str = "ebay",
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the listing content agent.

        Args:
            marketplace: Target marketplace (ebay, amazon, etc.)
            config_manager: Configuration manager
            alert_manager: Alert manager for monitoring
            battery_optimizer: Battery optimizer for mobile efficiency
            config: Optional configuration overrides
        """
        agent_id = f"listing_content_agent_{marketplace}_{uuid4()}"
        super().__init__(
            agent_id=agent_id,
            content_type="listing",
            config_manager=config_manager,
            alert_manager=alert_manager,
            battery_optimizer=battery_optimizer,
            config=config,
        )

        self.marketplace = marketplace
        self.content_templates = {}
        self.seo_keywords = {}
        self.marketplace_rules = {}

        # Marketplace-specific configurations
        self.marketplace_configs = {
            "ebay": {
                "title_max_length": 80,
                "description_max_length": 500000,
                "bullet_points_max": 5,
                "keyword_density_target": 0.02,
                "cassini_optimization": {
                    "relevance_weight": 0.4,
                    "performance_weight": 0.3,
                    "seller_quality_weight": 0.3,
                    "title_keyword_positions": [0, 1, 2],  # Best positions for keywords
                    "optimal_title_length": 65,  # Sweet spot for eBay titles
                    "item_specifics_importance": 0.25,
                    "description_keyword_density": 0.015,
                },
            },
            "amazon": {
                "title_max_length": 200,
                "description_max_length": 2000,
                "bullet_points_max": 5,
                "keyword_density_target": 0.015,
                "cassini_optimization": {
                    "relevance_weight": 0.5,
                    "performance_weight": 0.25,
                    "seller_quality_weight": 0.25,
                    "title_keyword_positions": [0, 1, 2, 3],
                    "optimal_title_length": 150,
                    "item_specifics_importance": 0.2,
                    "description_keyword_density": 0.012,
                },
            },
        }

        # Initialize Cassini optimizer
        self.cassini_optimizer = None

    def _get_required_config_fields(self) -> List[str]:
        """Get required configuration fields."""
        fields = super()._get_required_config_fields()
        fields.extend(
            [
                "ai_service_url",
                "content_model",
                "seo_optimization_enabled",
                "marketplace_rules_enabled",
            ]
        )
        return fields

    async def _setup_content_resources(self) -> None:
        """Set up content generation resources."""
        # Initialize AI service connection
        # Load marketplace-specific templates and rules
        await self._load_marketplace_templates()
        await self._load_seo_keywords()

        # Initialize Cassini optimizer for eBay
        if self.marketplace == "ebay":
            self.cassini_optimizer = CassiniOptimizer(
                self.marketplace_configs["ebay"]["cassini_optimization"]
            )

        logger.info(f"Content resources initialized for {self.marketplace}")

    async def _cleanup_content_resources(self) -> None:
        """Clean up content generation resources."""
        self.content_templates.clear()
        self.seo_keywords.clear()
        self.marketplace_rules.clear()

    async def _load_marketplace_templates(self) -> None:
        """Load marketplace-specific content templates."""
        self.content_templates = {
            "title": {
                "electronics": "{brand} {model} - {key_feature} | {condition} | {unique_selling_point}",
                "clothing": "{brand} {type} - {size} {color} | {style} | {condition}",
                "home": "{brand} {product_name} - {material} | {dimensions} | {condition}",
                "default": "{brand} {product_name} - {key_feature} | {condition}",
            },
            "description": {
                "intro": "Experience premium quality with this {product_name} from {brand}.",
                "features": "Key features include: {features_list}",
                "benefits": "Perfect for {use_cases}. {value_proposition}",
                "closing": "Order now for fast shipping and satisfaction guarantee!",
            },
            "bullet_points": [
                "Premium {material} construction for durability",
                "Perfect for {primary_use_case}",
                "Includes {included_items}",
                "{warranty_info}",
                "Fast shipping and excellent customer service",
            ],
        }

    async def _load_seo_keywords(self) -> None:
        """Load SEO keywords for different categories."""
        self.seo_keywords = {
            "electronics": [
                "premium",
                "professional",
                "high-quality",
                "durable",
                "reliable",
            ],
            "clothing": ["comfortable", "stylish", "trendy", "premium", "quality"],
            "home": ["elegant", "functional", "durable", "premium", "quality"],
            "default": ["premium", "quality", "professional", "reliable", "excellent"],
        }

    async def _handle_generation_event(self, event: Dict[str, Any]) -> None:
        """Handle content generation events."""
        try:
            product_data = event.get("product_data", {})
            content_type = event.get("content_type", "full_listing")

            if content_type == "title":
                result = await self.generate_optimized_title(product_data)
            elif content_type == "description":
                result = await self.generate_product_description(product_data)
            elif content_type == "bullet_points":
                result = await self.generate_bullet_points(product_data)
            else:
                result = await self.generate_complete_listing(product_data)

            self.metrics["content_generated"] += 1
            logger.info(
                f"Generated {content_type} content for product {product_data.get('sku', 'unknown')}"
            )

        except Exception as e:
            logger.error(f"Error handling generation event: {e}")

    async def _handle_optimization_event(self, event: Dict[str, Any]) -> None:
        """Handle content optimization events."""
        try:
            existing_content = event.get("content", {})
            optimization_goals = event.get("goals", ["seo", "conversion"])

            result = await self.optimize_listing_content(
                existing_content, optimization_goals
            )
            self.metrics["content_optimized"] += 1
            logger.info(f"Optimized content with goals: {optimization_goals}")

        except Exception as e:
            logger.error(f"Error handling optimization event: {e}")

    async def _generate_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate new listing content."""
        try:
            product_data = task.get("product_data", {})
            content_type = task.get("content_type", "full_listing")

            start_time = datetime.now(timezone.utc)

            if content_type == "title":
                content = await self.generate_optimized_title(product_data)
            elif content_type == "description":
                content = await self.generate_product_description(product_data)
            elif content_type == "bullet_points":
                content = await self.generate_bullet_points(product_data)
            else:
                content = await self.generate_complete_listing(product_data)

            end_time = datetime.now(timezone.utc)
            self.metrics["generation_latency"] = (end_time - start_time).total_seconds()

            return {
                "content": content,
                "success": True,
                "generation_time": self.metrics["generation_latency"],
            }

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            return {"error": str(e), "success": False}

    async def _optimize_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize existing listing content."""
        try:
            content = task.get("content", {})
            goals = task.get("optimization_goals", ["seo", "conversion"])

            start_time = datetime.now(timezone.utc)
            optimized_content = await self.optimize_listing_content(content, goals)
            end_time = datetime.now(timezone.utc)

            self.metrics["optimization_latency"] = (
                end_time - start_time
            ).total_seconds()

            return {
                "original_content": content,
                "optimized_content": optimized_content,
                "optimization_goals": goals,
                "success": True,
                "optimization_time": self.metrics["optimization_latency"],
            }

        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            return {"error": str(e), "success": False}

    async def generate_optimized_title(self, product_data: Dict[str, Any]) -> str:
        """Generate SEO-optimized product title."""
        try:
            category = product_data.get("category", "default")
            brand = product_data.get("brand", "Brand")
            model = product_data.get("model", product_data.get("name", "Product"))
            condition = product_data.get("condition", "New")

            # Get marketplace constraints
            max_length = self.marketplace_configs.get(self.marketplace, {}).get(
                "title_max_length", 80
            )

            # Get template for category
            template = self.content_templates["title"].get(
                category, self.content_templates["title"]["default"]
            )

            # Generate title components
            key_feature = self._extract_key_feature(product_data)
            unique_selling_point = self._generate_unique_selling_point(product_data)

            # Format title
            title = template.format(
                brand=brand,
                model=model,
                key_feature=key_feature,
                condition=condition,
                unique_selling_point=unique_selling_point,
                product_name=model,
            )

            # Ensure title fits marketplace constraints
            if len(title) > max_length:
                title = title[: max_length - 3] + "..."

            return title

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return f"{product_data.get('brand', 'Brand')} {product_data.get('name', 'Product')}"

    async def generate_product_description(self, product_data: Dict[str, Any]) -> str:
        """Generate compelling product description."""
        try:
            brand = product_data.get("brand", "Brand")
            product_name = product_data.get("name", "Product")
            features = product_data.get("features", [])

            # Build description sections
            intro = self.content_templates["description"]["intro"].format(
                product_name=product_name, brand=brand
            )

            features_text = ""
            if features:
                features_list = ", ".join(features[:5])  # Limit to top 5 features
                features_text = self.content_templates["description"][
                    "features"
                ].format(features_list=features_list)

            benefits = self.content_templates["description"]["benefits"].format(
                use_cases=self._generate_use_cases(product_data),
                value_proposition=self._generate_value_proposition(product_data),
            )

            closing = self.content_templates["description"]["closing"]

            # Combine sections
            description = f"{intro}\n\n{features_text}\n\n{benefits}\n\n{closing}"

            # Add SEO keywords naturally
            description = await self._enhance_with_seo_keywords(
                description, product_data
            )

            return description

        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return f"High-quality {product_data.get('name', 'product')} from {product_data.get('brand', 'Brand')}."

    async def generate_bullet_points(self, product_data: Dict[str, Any]) -> List[str]:
        """Generate optimized bullet points."""
        try:
            bullet_points = []
            max_bullets = self.marketplace_configs.get(self.marketplace, {}).get(
                "bullet_points_max", 5
            )

            # Generate bullet points based on product data
            material = product_data.get("material", "premium materials")
            primary_use = product_data.get("primary_use", "everyday use")
            included_items = product_data.get(
                "included_items", "all necessary components"
            )
            warranty = product_data.get("warranty", "Manufacturer warranty included")

            template_bullets = self.content_templates["bullet_points"]

            for i, template in enumerate(template_bullets[:max_bullets]):
                bullet = template.format(
                    material=material,
                    primary_use_case=primary_use,
                    included_items=included_items,
                    warranty_info=warranty,
                )
                bullet_points.append(bullet)

            return bullet_points

        except Exception as e:
            logger.error(f"Error generating bullet points: {e}")
            return [
                "Premium quality product",
                "Professional grade",
                "Satisfaction guaranteed",
            ]

    async def generate_complete_listing(
        self, product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate complete listing content."""
        try:
            title = await self.generate_optimized_title(product_data)
            description = await self.generate_product_description(product_data)
            bullet_points = await self.generate_bullet_points(product_data)

            # Calculate quality scores
            title_score = self._calculate_quality_score(title)
            description_score = self._calculate_quality_score(description)
            seo_score = self._calculate_seo_score(
                f"{title} {description}", self._get_relevant_keywords(product_data)
            )

            return {
                "title": title,
                "description": description,
                "bullet_points": bullet_points,
                "quality_scores": {
                    "title": title_score,
                    "description": description_score,
                    "seo": seo_score,
                    "overall": (title_score + description_score + seo_score) / 3,
                },
                "marketplace": self.marketplace,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating complete listing: {e}")
            return {"error": str(e)}

    async def optimize_listing_content(
        self, content: Dict[str, Any], optimization_goals: List[str]
    ) -> Dict[str, Any]:
        """Optimize existing listing content."""
        try:
            optimized = content.copy()
            improvements = []

            if "seo" in optimization_goals:
                optimized, seo_improvements = await self._optimize_for_seo(optimized)
                improvements.extend(seo_improvements)

            if "conversion" in optimization_goals:
                optimized, conversion_improvements = (
                    await self._optimize_for_conversion(optimized)
                )
                improvements.extend(conversion_improvements)

            if "readability" in optimization_goals:
                optimized, readability_improvements = (
                    await self._optimize_for_readability(optimized)
                )
                improvements.extend(readability_improvements)

            optimized["improvements"] = improvements
            optimized["optimization_goals"] = optimization_goals
            optimized["optimized_at"] = datetime.now(timezone.utc).isoformat()

            return optimized

        except Exception as e:
            logger.error(f"Error optimizing content: {e}")
            return content

    # Helper methods
    def _extract_key_feature(self, product_data: Dict[str, Any]) -> str:
        """Extract the most important feature for the title."""
        features = product_data.get("features", [])
        if features:
            return features[0]
        return product_data.get("key_benefit", "Premium Quality")

    def _generate_unique_selling_point(self, product_data: Dict[str, Any]) -> str:
        """Generate a unique selling point."""
        usp_options = [
            "Fast Shipping",
            "Satisfaction Guaranteed",
            "Premium Quality",
            "Professional Grade",
        ]
        return product_data.get("usp", usp_options[0])

    def _generate_use_cases(self, product_data: Dict[str, Any]) -> str:
        """Generate relevant use cases."""
        category = product_data.get("category", "general")
        use_cases = {
            "electronics": "professionals, enthusiasts, and everyday users",
            "clothing": "casual wear, professional settings, and special occasions",
            "home": "modern homes, offices, and commercial spaces",
            "default": "various applications and everyday use",
        }
        return use_cases.get(category, use_cases["default"])

    def _generate_value_proposition(self, product_data: Dict[str, Any]) -> str:
        """Generate value proposition."""
        return "Combining quality, reliability, and exceptional value in one premium product."

    async def _enhance_with_seo_keywords(
        self, text: str, product_data: Dict[str, Any]
    ) -> str:
        """Enhance text with relevant SEO keywords."""
        category = product_data.get("category", "default")
        keywords = self.seo_keywords.get(category, self.seo_keywords["default"])

        # Simple keyword integration (in a real implementation, this would be more sophisticated)
        enhanced_text = text
        for keyword in keywords[:2]:  # Add top 2 keywords naturally
            if keyword not in enhanced_text.lower():
                enhanced_text = enhanced_text.replace(
                    "quality", f"{keyword} quality", 1
                )

        return enhanced_text

    def _get_relevant_keywords(self, product_data: Dict[str, Any]) -> List[str]:
        """Get relevant keywords for SEO analysis."""
        category = product_data.get("category", "default")
        base_keywords = self.seo_keywords.get(category, self.seo_keywords["default"])

        # Add product-specific keywords
        product_keywords = [
            product_data.get("brand", "").lower(),
            product_data.get("name", "").lower(),
            product_data.get("model", "").lower(),
        ]

        return base_keywords + [k for k in product_keywords if k]

    async def _optimize_for_seo(
        self, content: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Optimize content for SEO."""
        improvements = []

        # Add SEO improvements logic here
        if "title" in content and len(content["title"]) < 50:
            content["title"] += " - Premium Quality"
            improvements.append("Enhanced title with SEO keywords")

        return content, improvements

    async def _optimize_for_conversion(
        self, content: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Optimize content for conversion."""
        improvements = []

        # Add conversion optimization logic here
        if (
            "description" in content
            and "guarantee" not in content["description"].lower()
        ):
            content["description"] += " Backed by our satisfaction guarantee!"
            improvements.append("Added satisfaction guarantee for better conversion")

        return content, improvements

    async def _optimize_for_readability(
        self, content: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Optimize content for readability."""
        improvements = []

        # Add readability improvements logic here
        if "description" in content:
            # Simple sentence break improvement
            description = content["description"]
            if ". " not in description and len(description) > 100:
                # Add sentence breaks for better readability
                content["description"] = description.replace(", ", ". ", 1)
                improvements.append(
                    "Improved sentence structure for better readability"
                )

        return content, improvements

    def _calculate_quality_score(self, text: str) -> int:
        """Calculate quality score for text content."""
        # Simple quality scoring (in a real implementation, this would be more sophisticated)
        score = 50  # Base score

        # Length bonus
        if 50 <= len(text) <= 200:
            score += 20

        # Keyword presence
        quality_indicators = ["premium", "quality", "professional", "excellent"]
        for indicator in quality_indicators:
            if indicator in text.lower():
                score += 5

        return min(score, 100)

    def _calculate_seo_score(self, text: str, keywords: List[str]) -> int:
        """Calculate SEO score based on keyword presence."""
        score = 0
        text_lower = text.lower()

        for keyword in keywords:
            if keyword and keyword in text_lower:
                score += 10

        return min(score, 100)


class CassiniOptimizer:
    """
    Advanced eBay Cassini algorithm optimizer for listing content.

    The Cassini algorithm is eBay's search ranking system that determines
    which listings appear in search results and their order. This optimizer
    implements strategies to improve listing visibility and ranking.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Cassini optimizer.

        Args:
            config: Cassini optimization configuration
        """
        self.config = config
        self.relevance_weight = config.get("relevance_weight", 0.4)
        self.performance_weight = config.get("performance_weight", 0.3)
        self.seller_quality_weight = config.get("seller_quality_weight", 0.3)
        self.optimal_title_length = config.get("optimal_title_length", 65)
        self.title_keyword_positions = config.get("title_keyword_positions", [0, 1, 2])
        self.item_specifics_importance = config.get("item_specifics_importance", 0.25)
        self.description_keyword_density = config.get(
            "description_keyword_density", 0.015
        )

    async def optimize_for_cassini(
        self,
        content: Dict[str, Any],
        product_data: Dict[str, Any],
        target_keywords: List[str],
    ) -> Dict[str, Any]:
        """
        Optimize listing content for eBay's Cassini algorithm.

        Args:
            content: Current listing content
            product_data: Product information
            target_keywords: Keywords to optimize for

        Returns:
            Optimized content with Cassini improvements
        """
        optimized = content.copy()
        cassini_score = 0
        improvements = []

        # 1. Title Optimization for Relevance (40% weight)
        if "title" in optimized:
            title_result = await self._optimize_title_for_cassini(
                optimized["title"], target_keywords, product_data
            )
            optimized["title"] = title_result["optimized_title"]
            cassini_score += title_result["relevance_score"] * self.relevance_weight
            improvements.extend(title_result["improvements"])

        # 2. Item Specifics Optimization (25% weight)
        if "item_specifics" in optimized or product_data:
            specifics_result = await self._optimize_item_specifics_for_cassini(
                optimized.get("item_specifics", {}), product_data
            )
            optimized["item_specifics"] = specifics_result["optimized_specifics"]
            cassini_score += (
                specifics_result["completeness_score"] * self.item_specifics_importance
            )
            improvements.extend(specifics_result["improvements"])

        # 3. Description Keyword Optimization (15% weight)
        if "description" in optimized:
            desc_result = await self._optimize_description_for_cassini(
                optimized["description"], target_keywords
            )
            optimized["description"] = desc_result["optimized_description"]
            cassini_score += desc_result["keyword_score"] * 0.15
            improvements.extend(desc_result["improvements"])

        # 4. Performance Prediction (20% weight)
        performance_score = await self._predict_performance_score(
            optimized, product_data
        )
        cassini_score += performance_score * self.performance_weight

        optimized["cassini_optimization"] = {
            "overall_score": int(cassini_score * 100),
            "relevance_score": (
                title_result.get("relevance_score", 0) if "title" in optimized else 0
            ),
            "specifics_completeness": (
                specifics_result.get("completeness_score", 0)
                if "item_specifics" in optimized or product_data
                else 0
            ),
            "keyword_optimization": (
                desc_result.get("keyword_score", 0) if "description" in optimized else 0
            ),
            "performance_prediction": performance_score,
            "improvements": improvements,
            "optimization_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return optimized

    async def _optimize_title_for_cassini(
        self, title: str, keywords: List[str], product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize title for Cassini relevance scoring."""
        improvements = []
        optimized_title = title
        relevance_score = 0.5  # Base score

        # 1. Keyword positioning optimization
        primary_keywords = keywords[:3]  # Focus on top 3 keywords

        for keyword in primary_keywords:
            if keyword.lower() in optimized_title.lower():
                # Check if keyword is in optimal positions
                keyword_position = self._find_keyword_position(optimized_title, keyword)
                if keyword_position in self.title_keyword_positions:
                    relevance_score += 0.15
                else:
                    # Try to move keyword to better position
                    optimized_title = self._reposition_keyword(
                        optimized_title, keyword, 0
                    )
                    improvements.append(f"Moved '{keyword}' to optimal position")
                    relevance_score += 0.1

        # 2. Title length optimization
        if len(optimized_title) > self.optimal_title_length:
            optimized_title = self._truncate_title_smartly(
                optimized_title, self.optimal_title_length
            )
            improvements.append("Optimized title length for Cassini")
            relevance_score += 0.05
        elif len(optimized_title) < 40:
            # Title too short, add relevant keywords
            brand = product_data.get("brand", "")
            if brand and brand.lower() not in optimized_title.lower():
                optimized_title = f"{brand} {optimized_title}"
                improvements.append("Added brand for better relevance")
                relevance_score += 0.1

        # 3. Remove stop words from critical positions
        optimized_title = self._optimize_stop_words(optimized_title)

        return {
            "optimized_title": optimized_title,
            "relevance_score": min(relevance_score, 1.0),
            "improvements": improvements,
        }

    async def _optimize_item_specifics_for_cassini(
        self, current_specifics: Dict[str, str], product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize item specifics for Cassini completeness scoring."""
        improvements = []
        optimized_specifics = current_specifics.copy()
        completeness_score = 0.3  # Base score

        # Essential specifics for Cassini
        essential_specifics = ["Brand", "MPN", "Model", "Condition", "Color", "Size"]

        filled_essentials = 0
        for specific in essential_specifics:
            if specific in optimized_specifics and optimized_specifics[specific]:
                filled_essentials += 1
            elif specific.lower() in product_data:
                # Auto-fill from product data
                optimized_specifics[specific] = str(product_data[specific.lower()])
                filled_essentials += 1
                improvements.append(f"Auto-filled {specific} from product data")

        # Calculate completeness score
        completeness_score += (filled_essentials / len(essential_specifics)) * 0.7

        # Add category-specific specifics
        category = product_data.get("category", "")
        if category:
            category_specifics = self._get_category_specific_fields(category)
            for specific in category_specifics:
                if (
                    specific not in optimized_specifics
                    and specific.lower() in product_data
                ):
                    optimized_specifics[specific] = str(product_data[specific.lower()])
                    improvements.append(f"Added category-specific {specific}")
                    completeness_score += 0.05

        return {
            "optimized_specifics": optimized_specifics,
            "completeness_score": min(completeness_score, 1.0),
            "improvements": improvements,
        }

    # Helper methods for Cassini optimization
    def _find_keyword_position(self, title: str, keyword: str) -> int:
        """Find the word position of a keyword in the title."""
        words = title.lower().split()
        keyword_lower = keyword.lower()

        for i, word in enumerate(words):
            if keyword_lower in word:
                return i
        return -1

    def _reposition_keyword(
        self, title: str, keyword: str, target_position: int
    ) -> str:
        """Move a keyword to the target position in the title."""
        words = title.split()
        keyword_lower = keyword.lower()

        # Find and remove the keyword
        keyword_word = None
        for i, word in enumerate(words):
            if keyword_lower in word.lower():
                keyword_word = words.pop(i)
                break

        if keyword_word:
            # Insert at target position
            words.insert(target_position, keyword_word)

        return " ".join(words)

    def _truncate_title_smartly(self, title: str, max_length: int) -> str:
        """Intelligently truncate title while preserving important keywords."""
        if len(title) <= max_length:
            return title

        words = title.split()

        # Priority words to keep (brand, model, key features)
        priority_words = ["new", "brand", "premium", "professional", "original"]

        # Keep important words and truncate less important ones
        important_words = []
        other_words = []

        for word in words:
            if any(priority in word.lower() for priority in priority_words):
                important_words.append(word)
            else:
                other_words.append(word)

        # Build truncated title
        result = " ".join(important_words)

        # Add other words until we reach the limit
        for word in other_words:
            if len(result + " " + word) <= max_length:
                result += " " + word
            else:
                break

        return result.strip()

    def _optimize_stop_words(self, title: str) -> str:
        """Remove or reposition stop words from critical title positions."""
        words = title.split()

        # Common stop words that should not be in first 3 positions
        stop_words = [
            "the",
            "a",
            "an",
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
        ]

        # Move stop words away from critical positions (0, 1, 2)
        optimized_words = []
        stop_words_found = []

        for i, word in enumerate(words):
            if i < 3 and word.lower() in stop_words:
                stop_words_found.append(word)
            else:
                optimized_words.append(word)

        # Add stop words at the end if needed
        optimized_words.extend(stop_words_found)

        return " ".join(optimized_words)

    def _get_category_specific_fields(self, category: str) -> List[str]:
        """Get category-specific item specifics fields."""
        category_fields = {
            "electronics": [
                "Type",
                "Connectivity",
                "Storage Capacity",
                "Screen Size",
                "Processor",
                "RAM",
                "Operating System",
            ],
            "clothing": [
                "Size Type",
                "Department",
                "Pattern",
                "Sleeve Length",
                "Neckline",
                "Occasion",
                "Fit",
            ],
            "home": [
                "Room",
                "Style",
                "Material",
                "Dimensions",
                "Assembly Required",
                "Care Instructions",
            ],
            "automotive": [
                "Vehicle Type",
                "Year",
                "Make",
                "Model",
                "Engine",
                "Transmission",
                "Mileage",
            ],
            "sports": [
                "Sport",
                "League",
                "Team",
                "Player",
                "Size",
                "Gender",
                "Age Group",
            ],
            "books": [
                "Format",
                "Language",
                "Publication Year",
                "Genre",
                "Author",
                "Publisher",
                "ISBN",
            ],
            "toys": [
                "Age Range",
                "Gender",
                "Character Family",
                "Type",
                "Material",
                "Educational Focus",
            ],
        }

        return category_fields.get(category.lower(), ["Type", "Style", "Features"])

    def _add_keyword_naturally(self, description: str, keyword: str) -> str:
        """Add keywords to descriptions naturally without stuffing."""
        if keyword.lower() in description.lower():
            return description

        # Natural insertion points
        sentences = description.split(". ")

        # Add keyword to a relevant sentence
        keyword_phrases = [
            f"This {keyword} offers",
            f"Features {keyword} technology",
            f"Perfect {keyword} solution",
            f"High-quality {keyword} design",
        ]

        # Choose a phrase and insert it naturally
        if len(sentences) > 1:
            insert_phrase = keyword_phrases[0]  # Use first phrase for simplicity
            sentences.insert(1, insert_phrase)
            return ". ".join(sentences)
        else:
            return f"{description} {keyword_phrases[0]}."

    def _reduce_keyword_density(self, description: str, keyword: str) -> str:
        """Reduce keyword density when it's too high."""
        keyword_lower = keyword.lower()
        words = description.split()

        # Count occurrences
        keyword_count = sum(1 for word in words if keyword_lower in word.lower())

        if keyword_count <= 2:
            return description

        # Remove every other occurrence after the second one
        new_words = []
        occurrences = 0

        for word in words:
            if keyword_lower in word.lower():
                occurrences += 1
                if occurrences <= 2 or occurrences % 2 == 0:
                    new_words.append(word)
                # Skip this occurrence to reduce density
            else:
                new_words.append(word)

        return " ".join(new_words)

    async def _optimize_description_for_cassini(
        self, description: str, keywords: List[str]
    ) -> Dict[str, Any]:
        """Optimize description for Cassini keyword relevance."""
        improvements = []
        optimized_description = description
        keyword_score = 0.2  # Base score

        # Calculate current keyword density
        word_count = len(optimized_description.split())

        for keyword in keywords[:5]:  # Focus on top 5 keywords
            keyword_count = optimized_description.lower().count(keyword.lower())
            current_density = keyword_count / word_count if word_count > 0 else 0

            if current_density < self.description_keyword_density:
                # Add keyword naturally
                optimized_description = self._add_keyword_naturally(
                    optimized_description, keyword
                )
                improvements.append(f"Enhanced keyword density for '{keyword}'")
                keyword_score += 0.1
            elif current_density > self.description_keyword_density * 2:
                # Reduce keyword stuffing
                optimized_description = self._reduce_keyword_density(
                    optimized_description, keyword
                )
                improvements.append(f"Reduced keyword stuffing for '{keyword}'")
                keyword_score += 0.05
            else:
                keyword_score += 0.15  # Good density

        return {
            "optimized_description": optimized_description,
            "keyword_score": min(keyword_score, 1.0),
            "improvements": improvements,
        }

    async def _predict_performance_score(
        self, content: Dict[str, Any], product_data: Dict[str, Any]
    ) -> float:
        """Predict listing performance based on content quality."""
        score = 0.3  # Base score

        # Title quality indicators
        title = content.get("title", "")
        if len(title) >= 50:
            score += 0.1
        if any(
            word in title.lower()
            for word in ["new", "brand", "premium", "professional"]
        ):
            score += 0.1

        # Description quality indicators
        description = content.get("description", "")
        if len(description) >= 200:
            score += 0.1
        if "guarantee" in description.lower() or "warranty" in description.lower():
            score += 0.1

        # Item specifics completeness
        specifics = content.get("item_specifics", {})
        if len(specifics) >= 5:
            score += 0.15

        # Category relevance
        category = product_data.get("category", "")
        if category and category in title.lower():
            score += 0.1

        return min(score, 1.0)
