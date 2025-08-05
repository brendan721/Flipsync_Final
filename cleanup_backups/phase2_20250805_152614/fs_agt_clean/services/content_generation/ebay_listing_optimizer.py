"""
eBay Listing Optimizer Service for FlipSync.

This service integrates the ItemSpecificsMaximizer with the ContentAgent to provide
comprehensive eBay listing optimization. It coordinates title optimization, item
specifics maximization, and description generation to ensure maximum SEO performance
and keyword consistency across all listing components.

Key Features:
- Integration with ItemSpecificsMaximizer for comprehensive item specifics
- eBay-specific title optimization with keyword positioning
- Factual storytelling description generation
- Keyword consistency validation across title, specifics, and description
- Category-specific optimization rules
- Performance metrics and optimization suggestions
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fs_agt_clean.services.content_generation.item_specifics_maximizer import (
    ItemSpecificsMaximizer,
)
from fs_agt_clean.services.marketplace.ebay.service import EbayService

logger = logging.getLogger(__name__)


class EbayListingOptimizer:
    """
    Comprehensive eBay listing optimizer that coordinates all aspects of listing optimization
    for maximum SEO performance and organic visibility.
    """

    def __init__(self, ebay_service: Optional[EbayService] = None):
        """Initialize the eBay listing optimizer.

        Args:
            ebay_service: eBay service for API integration
        """
        self.ebay_service = (
            ebay_service  # Don't create by default, requires proper config
        )
        self.item_specifics_maximizer = ItemSpecificsMaximizer(self.ebay_service)
        self.title_templates = self._initialize_title_templates()
        self.description_templates = self._initialize_description_templates()

    def _initialize_title_templates(self) -> Dict[str, str]:
        """Initialize eBay-specific title templates by category."""
        return {
            "electronics": "{brand} {model} {key_features} {condition} {connectivity}",
            "clothing": "{brand} {size} {color} {material} {style} {condition}",
            "automotive": "{brand} {model} {year} {part_type} {condition}",
            "home_garden": "{brand} {type} {material} {color} {size} {condition}",
            "collectibles": "{brand} {type} {year} {rarity} {condition}",
            "default": "{brand} {model} {key_features} {condition}",
        }

    def _initialize_description_templates(self) -> Dict[str, str]:
        """Initialize factual storytelling description templates."""
        return {
            "electronics": """
Experience the exceptional quality of this {brand} {model}. This {condition} device features {key_features} 
and delivers {performance_benefits}. 

Key Specifications:
{specifications_list}

What makes this special:
{unique_selling_points}

Perfect for {target_audience}, this {product_type} combines {primary_benefit} with {secondary_benefit}. 
{warranty_info} {shipping_info}
            """,
            "clothing": """
Discover the perfect blend of style and comfort with this {brand} {item_type}. Crafted from {material} 
in a beautiful {color}, this {size} piece is {condition} and ready to elevate your wardrobe.

Product Details:
{specifications_list}

Style Features:
{style_features}

This versatile piece is ideal for {occasions} and pairs perfectly with {styling_suggestions}. 
{care_instructions} {sizing_info}
            """,
            "default": """
Presenting this exceptional {brand} {model} in {condition} condition. This {product_type} offers 
{primary_features} and is perfect for {intended_use}.

Product Specifications:
{specifications_list}

Key Benefits:
{benefits_list}

{additional_details} {shipping_info}
            """,
        }

    async def optimize_complete_listing(
        self,
        product_data: Dict[str, Any],
        category_id: str,
        target_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Optimize complete eBay listing for maximum SEO performance.

        Args:
            product_data: Product information dictionary
            category_id: eBay category ID
            target_keywords: Optional list of target keywords for SEO

        Returns:
            Dictionary with optimized listing components and performance metrics
        """
        try:
            logger.info("Optimizing complete eBay listing for category %s", category_id)

            # Step 1: Maximize item specifics (highest priority for eBay SEO)
            specifics_result = (
                await self.item_specifics_maximizer.maximize_item_specifics(
                    product_data, category_id, target_keywords
                )
            )

            item_specifics = specifics_result["item_specifics"]

            # Step 2: Generate eBay-optimized title using item specifics
            optimized_title = await self._generate_ebay_optimized_title(
                product_data, item_specifics, category_id, target_keywords
            )

            # Step 3: Generate factual storytelling description
            optimized_description = await self._generate_storytelling_description(
                product_data, item_specifics, optimized_title, category_id
            )

            # Step 4: Validate keyword consistency across all components
            consistency_result = (
                await self.item_specifics_maximizer.validate_keyword_consistency(
                    optimized_title, item_specifics, optimized_description
                )
            )

            # Step 5: Generate comprehensive optimization report
            optimization_report = self._generate_optimization_report(
                specifics_result, consistency_result, product_data, category_id
            )

            return {
                "optimized_title": optimized_title,
                "item_specifics": item_specifics,
                "optimized_description": optimized_description,
                "category_id": category_id,
                "seo_metrics": {
                    "specifics_seo_score": specifics_result["seo_score"],
                    "keyword_consistency_score": consistency_result[
                        "overall_consistency_score"
                    ],
                    "total_specifics": specifics_result["total_specifics"],
                    "required_specifics": specifics_result["required_count"],
                    "recommended_specifics": specifics_result["recommended_count"],
                },
                "optimization_suggestions": optimization_report["suggestions"],
                "performance_predictions": optimization_report["predictions"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error("Error optimizing eBay listing: %s", str(e))
            return await self._generate_fallback_optimization(product_data, category_id)

    async def _generate_ebay_optimized_title(
        self,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
        category_id: str,
        target_keywords: Optional[List[str]] = None,
    ) -> str:
        """Generate eBay-optimized title following best practices."""
        # eBay title best practices:
        # - 80 character limit, 65 character sweet spot
        # - First 4 words: Brand → Model → Key Features
        # - Include most important item specifics
        # - Position keywords optimally

        title_parts = []

        # 1. Brand (highest priority - position 0)
        brand = item_specifics.get("Brand") or product_data.get("brand", "")
        if brand:
            title_parts.append(brand)

        # 2. Model (high priority - position 1)
        model = item_specifics.get("Model") or product_data.get("model", "")
        if model and model.lower() not in brand.lower():
            title_parts.append(model)

        # 3. Key features from item specifics (positions 2-3)
        key_features = []
        priority_aspects = [
            "Storage Capacity",
            "Screen Size",
            "Color",
            "Size",
            "Material",
        ]

        for aspect in priority_aspects:
            if aspect in item_specifics:
                value = item_specifics[aspect]
                if len(value) <= 15:  # Keep features concise
                    key_features.append(value)
                if len(key_features) >= 2:  # Limit to 2 key features
                    break

        title_parts.extend(key_features)

        # 4. Condition (important for buyer confidence)
        condition = item_specifics.get("Condition") or product_data.get("condition", "")
        if condition and condition.upper() != "NEW":
            title_parts.append(condition)

        # 5. Add target keywords if space allows
        if target_keywords:
            current_length = len(" ".join(title_parts))
            for keyword in target_keywords[:2]:  # Max 2 additional keywords
                if keyword.lower() not in " ".join(title_parts).lower():
                    if current_length + len(keyword) + 1 <= 65:  # Sweet spot limit
                        title_parts.append(keyword.title())
                        current_length += len(keyword) + 1

        # 6. Add category-specific terms for SEO
        category_terms = self._get_category_seo_terms(category_id)
        current_length = len(" ".join(title_parts))

        for term in category_terms:
            if term.lower() not in " ".join(title_parts).lower():
                if (
                    current_length + len(term) + 1 <= 75
                ):  # Leave room for final adjustments
                    title_parts.append(term)
                    current_length += len(term) + 1
                    break

        # Join and optimize final title
        title = " ".join(title_parts)

        # Ensure title is within eBay limits
        if len(title) > 80:
            title = title[:77] + "..."

        return title

    def _get_category_seo_terms(self, category_id: str) -> List[str]:
        """Get category-specific SEO terms for title optimization."""
        category_terms = {
            "9355": [
                "Smartphone",
                "Unlocked",
                "Cell Phone",
            ],  # Cell Phones & Smartphones
            "58058": ["Mobile", "Device", "Wireless"],
            "11450": ["Fashion", "Apparel", "Style"],  # Clothing
            "6000": ["Auto", "Vehicle", "Car"],  # eBay Motors
            "11700": ["Home", "Decor", "Garden"],  # Home & Garden
            "1": ["Collectible", "Vintage", "Rare"],  # Collectibles
        }

        return category_terms.get(category_id, ["Quality", "Premium"])

    async def _generate_storytelling_description(
        self,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
        title: str,
        category_id: str,
    ) -> str:
        """Generate factual storytelling description."""
        # Determine category for template selection
        category_type = self._determine_category_type(category_id)
        template = self.description_templates.get(
            category_type, self.description_templates["default"]
        )

        # Extract key information for template
        brand = item_specifics.get("Brand", product_data.get("brand", ""))
        model = item_specifics.get("Model", product_data.get("model", ""))
        condition = item_specifics.get(
            "Condition", product_data.get("condition", "New")
        )

        # Build specifications list from item specifics
        specifications_list = self._format_specifications_list(item_specifics)

        # Generate category-specific content
        category_content = self._generate_category_specific_content(
            product_data, item_specifics, category_type
        )

        # Format description using template
        # Extract all needed values from category_content to avoid duplicate keyword arguments
        template_vars = {
            "brand": brand,
            "model": model,
            "condition": condition.lower(),
            "product_type": category_content.get("product_type", "item"),
            "key_features": category_content.get("key_features", "premium features"),
            "specifications_list": specifications_list,
            "primary_benefit": category_content.get(
                "primary_benefit", "exceptional quality"
            ),
            "secondary_benefit": category_content.get(
                "secondary_benefit", "reliable performance"
            ),
        }

        # Add additional category-specific variables without duplicating existing ones
        for key, value in category_content.items():
            if key not in template_vars:
                template_vars[key] = value

        description = template.format(**template_vars)

        # Clean up and optimize description
        description = self._clean_description(description)

        # Ensure keyword consistency with title and specifics
        description = self._enhance_description_keywords(
            description, title, item_specifics
        )

        return description

    def _determine_category_type(self, category_id: str) -> str:
        """Determine category type for template selection."""
        category_mapping = {
            "9355": "electronics",  # Cell Phones & Smartphones
            "58058": "electronics",
            "11450": "clothing",  # Clothing, Shoes & Accessories
            "6000": "automotive",  # eBay Motors
            "11700": "home_garden",  # Home & Garden
            "1": "collectibles",  # Collectibles
        }

        return category_mapping.get(category_id, "default")

    def _format_specifications_list(self, item_specifics: Dict[str, str]) -> str:
        """Format item specifics as a clean specifications list."""
        specs = []

        # Prioritize important specifications
        priority_specs = ["Brand", "Model", "Color", "Size", "Material", "Condition"]

        for spec_name in priority_specs:
            if spec_name in item_specifics:
                specs.append(f"• {spec_name}: {item_specifics[spec_name]}")

        # Add remaining specifications
        for name, value in item_specifics.items():
            if name not in priority_specs:
                specs.append(f"• {name}: {value}")

        return "\n".join(specs[:8])  # Limit to 8 specifications for readability

    def _generate_category_specific_content(
        self,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
        category_type: str,
    ) -> Dict[str, str]:
        """Generate category-specific content for descriptions."""
        if category_type == "electronics":
            return {
                "product_type": "device",
                "key_features": self._extract_tech_features(item_specifics),
                "primary_benefit": "cutting-edge technology",
                "secondary_benefit": "user-friendly design",
                "performance_benefits": "reliable performance and connectivity",
                "target_audience": "tech enthusiasts and professionals",
                "unique_selling_points": "Advanced features and premium build quality",
                "warranty_info": "Manufacturer warranty included where applicable.",
                "shipping_info": "Fast and secure shipping with tracking.",
            }
        elif category_type == "clothing":
            return {
                "product_type": "garment",
                "item_type": product_data.get("type", "clothing item"),
                "material": item_specifics.get("Material", "quality fabric"),
                "color": item_specifics.get("Color", "attractive color"),
                "size": item_specifics.get("Size", "standard size"),
                "style_features": self._extract_style_features(item_specifics),
                "unique_selling_points": "Premium materials and timeless style",
                "occasions": "casual and formal occasions",
                "styling_suggestions": "your favorite accessories",
                "care_instructions": "Follow care label instructions for best results.",
                "sizing_info": "Please refer to size chart for accurate fit.",
            }
        else:
            return {
                "product_type": "item",
                "primary_features": "exceptional quality and design",
                "intended_use": "various applications",
                "benefits_list": self._extract_general_benefits(item_specifics),
                "unique_selling_points": "Outstanding quality and value",
                "additional_details": "Carefully inspected and ready for use.",
                "shipping_info": "Prompt shipping with secure packaging.",
            }

    def _extract_tech_features(self, item_specifics: Dict[str, str]) -> str:
        """Extract technology features from item specifics."""
        tech_features = []

        tech_aspects = [
            "Storage Capacity",
            "Screen Size",
            "Operating System",
            "Connectivity",
            "Camera Resolution",
        ]
        for aspect in tech_aspects:
            if aspect in item_specifics:
                tech_features.append(item_specifics[aspect])

        return ", ".join(tech_features[:3]) if tech_features else "advanced features"

    def _extract_style_features(self, item_specifics: Dict[str, str]) -> str:
        """Extract style features from item specifics."""
        style_features = []

        style_aspects = ["Style", "Pattern", "Sleeve Length", "Neckline", "Fit"]
        for aspect in style_aspects:
            if aspect in item_specifics:
                style_features.append(f"{aspect}: {item_specifics[aspect]}")

        return "\n".join([f"• {feature}" for feature in style_features[:4]])

    def _extract_general_benefits(self, item_specifics: Dict[str, str]) -> str:
        """Extract general benefits from item specifics."""
        benefits = []

        for name, value in list(item_specifics.items())[:5]:
            if name not in ["Brand", "Model", "Condition"]:
                benefits.append(f"• {name}: {value}")

        return (
            "\n".join(benefits)
            if benefits
            else "• Premium quality construction\n• Reliable performance"
        )

    def _clean_description(self, description: str) -> str:
        """Clean and optimize description text."""
        # Remove extra whitespace and empty lines
        lines = [line.strip() for line in description.split("\n") if line.strip()]

        # Join lines with proper spacing
        cleaned = "\n".join(lines)

        # Remove any template placeholders that weren't filled
        cleaned = cleaned.replace("{", "").replace("}", "")

        return cleaned

    def _enhance_description_keywords(
        self, description: str, title: str, item_specifics: Dict[str, str]
    ) -> str:
        """Enhance description with keywords from title and specifics for SEO consistency."""
        # Extract important keywords from title
        title_words = [word for word in title.split() if len(word) > 3]

        # Extract important values from item specifics
        important_values = []
        for name, value in item_specifics.items():
            if name in ["Brand", "Model", "Color", "Material", "Features"]:
                important_values.extend(value.split())

        # Add a keyword-rich closing paragraph if description is short
        if len(description) < 500:
            keyword_phrase = f"This {' '.join(title_words[:3]).lower()} combines {' and '.join(important_values[:2]).lower()} for exceptional value."
            description += f"\n\n{keyword_phrase}"

        return description

    def _generate_optimization_report(
        self,
        specifics_result: Dict[str, Any],
        consistency_result: Dict[str, Any],
        product_data: Dict[str, Any],
        category_id: str,
    ) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        suggestions = []
        predictions = {}

        # Analyze item specifics performance
        seo_score = specifics_result["seo_score"]
        if seo_score < 70:
            suggestions.append(
                "Consider adding more item specifics to improve SEO score"
            )
        if specifics_result["required_count"] < 3:
            suggestions.append("Ensure all required item specifics are completed")

        # Analyze keyword consistency
        consistency_score = consistency_result["overall_consistency_score"]
        if consistency_score < 60:
            suggestions.extend(consistency_result["suggestions"])

        # Add specifics-based suggestions
        suggestions.extend(specifics_result["optimization_suggestions"])

        # Generate performance predictions
        predictions = {
            "seo_visibility": (
                "High" if seo_score > 80 else "Medium" if seo_score > 60 else "Low"
            ),
            "search_ranking_potential": self._predict_search_ranking(
                seo_score, consistency_score
            ),
            "organic_traffic_estimate": self._estimate_organic_traffic(
                specifics_result, consistency_result
            ),
            "conversion_potential": self._predict_conversion_potential(
                product_data, specifics_result
            ),
        }

        return {
            "suggestions": suggestions[:5],  # Top 5 suggestions
            "predictions": predictions,
        }

    def _predict_search_ranking(
        self, seo_score: float, consistency_score: float
    ) -> str:
        """Predict search ranking potential based on optimization scores."""
        combined_score = (seo_score + consistency_score) / 2

        if combined_score > 85:
            return "Excellent - Top 10% potential"
        elif combined_score > 70:
            return "Good - Top 25% potential"
        elif combined_score > 55:
            return "Fair - Top 50% potential"
        else:
            return "Needs improvement"

    def _estimate_organic_traffic(
        self, specifics_result: Dict[str, Any], consistency_result: Dict[str, Any]
    ) -> str:
        """Estimate organic traffic potential."""
        total_specifics = specifics_result["total_specifics"]
        consistency_score = consistency_result["overall_consistency_score"]

        if total_specifics > 12 and consistency_score > 75:
            return "High - 15-25% increase expected"
        elif total_specifics > 8 and consistency_score > 60:
            return "Medium - 8-15% increase expected"
        else:
            return "Low - 3-8% increase expected"

    def _predict_conversion_potential(
        self, product_data: Dict[str, Any], specifics_result: Dict[str, Any]
    ) -> str:
        """Predict conversion potential based on listing completeness."""
        completeness_factors = 0

        # Check for key conversion factors
        if product_data.get("images") and len(product_data["images"]) > 3:
            completeness_factors += 1
        if specifics_result["total_specifics"] > 10:
            completeness_factors += 1
        if specifics_result["required_count"] >= 3:
            completeness_factors += 1
        if product_data.get("condition") == "New":
            completeness_factors += 1

        if completeness_factors >= 3:
            return "High - Complete listing with strong buyer confidence"
        elif completeness_factors >= 2:
            return "Medium - Good listing with room for improvement"
        else:
            return "Low - Missing key elements for buyer confidence"

    async def _generate_fallback_optimization(
        self, product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """Generate fallback optimization when main process fails."""
        logger.warning("Using fallback optimization for category %s", category_id)

        # Basic title
        brand = product_data.get("brand", "")
        model = product_data.get("model", "")
        condition = product_data.get("condition", "New")

        fallback_title = f"{brand} {model} {condition}".strip()
        if len(fallback_title) < 20:
            fallback_title += " - Premium Quality"

        # Basic item specifics
        fallback_specifics = {}
        if brand:
            fallback_specifics["Brand"] = brand
        if model:
            fallback_specifics["Model"] = model
        if condition:
            fallback_specifics["Condition"] = condition

        # Basic description
        fallback_description = (
            f"Quality {brand} {model} in {condition.lower()} condition. "
            f"This item offers reliable performance and value. "
            f"Fast shipping with secure packaging."
        )

        return {
            "optimized_title": fallback_title[:80],
            "item_specifics": fallback_specifics,
            "optimized_description": fallback_description,
            "category_id": category_id,
            "seo_metrics": {
                "specifics_seo_score": 30,
                "keyword_consistency_score": 40,
                "total_specifics": len(fallback_specifics),
                "required_specifics": len(fallback_specifics),
                "recommended_specifics": 0,
            },
            "optimization_suggestions": ["API unavailable - using basic optimization"],
            "performance_predictions": {
                "seo_visibility": "Low",
                "search_ranking_potential": "Needs improvement",
                "organic_traffic_estimate": "Low - 1-3% increase expected",
                "conversion_potential": "Low - Basic listing",
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fallback": True,
        }
