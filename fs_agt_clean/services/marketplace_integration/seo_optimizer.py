"""
eBay SEO Optimizer for FlipSync.

This module provides SEO optimization capabilities for eBay listings, including:
- Title optimization for eBay search visibility
- Description enhancement for better search ranking
- Item specifics optimization for improved search relevance
- Keyword analysis and recommendation
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class KeywordAnalyzer:
    """Analyzes and recommends keywords for eBay listings."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the keyword analyzer."""
        self.config = config or {}
        self.max_keywords = self.config.get("max_keywords", 20)
        self.min_keyword_length = self.config.get("min_keyword_length", 3)

    async def analyze_category(self, category_id: str) -> List[Dict[str, Any]]:
        """
        Analyze top-performing listings in a category for keyword patterns.

        Args:
            category_id: eBay category ID

        Returns:
            List of keyword data with relevance scores
        """
        # In a real implementation, this would query eBay API for top listings
        # and analyze their keywords

        # Mock implementation for structure
        await asyncio.sleep(0.1)  # Simulate API call

        return [
            {"keyword": "new", "score": 0.95, "search_volume": 10000},
            {"keyword": "authentic", "score": 0.92, "search_volume": 8500},
            {"keyword": "genuine", "score": 0.90, "search_volume": 7800},
            {"keyword": "original", "score": 0.88, "search_volume": 7200},
            {"keyword": "brand new", "score": 0.85, "search_volume": 6500},
            {"keyword": "sealed", "score": 0.82, "search_volume": 5900},
            {"keyword": "warranty", "score": 0.80, "search_volume": 5400},
            {"keyword": "fast shipping", "score": 0.78, "search_volume": 4800},
            {"keyword": "free shipping", "score": 0.75, "search_volume": 4200},
        ]

    async def extract_keywords(self, text: str) -> List[str]:
        """
        Extract potential keywords from text.

        Args:
            text: Text to extract keywords from

        Returns:
            List of extracted keywords
        """
        # Convert to lowercase and remove special characters
        text = re.sub(r"[^\w\s]", " ", text.lower())

        # Split into words
        words = text.split()

        # Filter short words and common stop words
        stop_words = {
            "the",
            "and",
            "a",
            "an",
            "in",
            "on",
            "at",
            "with",
            "for",
            "to",
            "of",
            "is",
            "are",
        }
        keywords = [
            word
            for word in words
            if len(word) >= self.min_keyword_length and word not in stop_words
        ]

        # Get unique keywords
        unique_keywords = list(set(keywords))

        # Limit to max keywords
        return unique_keywords[: self.max_keywords]

    async def recommend_keywords(
        self, product_data: Dict[str, Any], category_id: str
    ) -> List[Dict[str, Any]]:
        """
        Recommend keywords for a product.

        Args:
            product_data: Product data
            category_id: eBay category ID

        Returns:
            List of recommended keywords with scores
        """
        # Extract keywords from product data
        title_keywords = await self.extract_keywords(product_data.get("title", ""))
        description_keywords = await self.extract_keywords(
            product_data.get("description", "")
        )
        feature_keywords = []
        for feature in product_data.get("features", []):
            feature_keywords.extend(await self.extract_keywords(feature))

        # Get category keywords
        category_keywords = await self.analyze_category(category_id)
        category_keyword_dict = {k["keyword"]: k for k in category_keywords}

        # Combine and score keywords
        all_keywords = set(title_keywords + description_keywords + feature_keywords)

        # Score and rank keywords
        scored_keywords = []
        for keyword in all_keywords:
            # Base score
            score = 0.5

            # Boost if in title (most important)
            if keyword in title_keywords:
                score += 0.3

            # Boost if in features
            if keyword in feature_keywords:
                score += 0.1

            # Boost if in description
            if keyword in description_keywords:
                score += 0.05

            # Boost if in category top keywords
            if keyword in category_keyword_dict:
                score += 0.2
                category_data = category_keyword_dict[keyword]
                search_volume = category_data.get("search_volume", 0)
            else:
                search_volume = 0

            scored_keywords.append(
                {
                    "keyword": keyword,
                    "score": min(score, 1.0),  # Cap at 1.0
                    "search_volume": search_volume,
                }
            )

        # Sort by score
        scored_keywords.sort(key=lambda k: k["score"], reverse=True)

        # Return top keywords
        return scored_keywords[: self.max_keywords]


class TitleOptimizer:
    """Optimizes listing titles for eBay search visibility."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the title optimizer."""
        self.config = config or {}
        self.max_title_length = self.config.get("max_title_length", 80)
        self.keyword_analyzer = KeywordAnalyzer(config)

    async def optimize_title(
        self, original_title: str, product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """
        Optimize a product title for eBay search visibility.

        Args:
            original_title: Original product title
            product_data: Product data
            category_id: eBay category ID

        Returns:
            Dictionary with optimized title and metadata
        """
        # Get recommended keywords
        recommended_keywords = await self.keyword_analyzer.recommend_keywords(
            product_data, category_id
        )

        # Start with original title
        title = original_title

        # Add brand if not already in title
        brand = product_data.get("brand")
        if brand and brand.lower() not in title.lower():
            title = f"{brand} {title}"

        # Add condition if new
        condition = product_data.get("condition", "").lower()
        if condition in ["new", "brand new"] and "new" not in title.lower():
            title = f"New {title}"

        # Add top keywords that aren't already in the title
        remaining_length = self.max_title_length - len(title)
        added_keywords = []

        for keyword_data in recommended_keywords:
            keyword = keyword_data["keyword"]

            # Skip if already in title
            if keyword.lower() in title.lower():
                continue

            # Skip if too long
            if len(keyword) + 1 > remaining_length:
                continue

            # Add keyword
            title = f"{title} {keyword}"
            added_keywords.append(keyword)
            remaining_length -= len(keyword) + 1

            # Stop if we've added enough keywords
            if len(added_keywords) >= 3 or remaining_length < 5:
                break

        # Ensure title is not too long
        if len(title) > self.max_title_length:
            title = title[: self.max_title_length]

        # Calculate SEO score
        seo_score = self._calculate_seo_score(title, recommended_keywords)

        return {
            "title": title,
            "seo_score": seo_score,
            "added_keywords": added_keywords,
            "recommended_keywords": recommended_keywords[:5],
            "original_length": len(original_title),
            "optimized_length": len(title),
        }

    def _calculate_seo_score(
        self, title: str, recommended_keywords: List[Dict[str, Any]]
    ) -> int:
        """
        Calculate SEO score for a title.

        Args:
            title: Title to score
            recommended_keywords: Recommended keywords with scores

        Returns:
            SEO score (0-100)
        """
        # Base score
        score = 50

        # Length score (0-20)
        length_ratio = len(title) / self.max_title_length
        if length_ratio > 0.9:
            length_score = 20
        elif length_ratio > 0.7:
            length_score = 15
        elif length_ratio > 0.5:
            length_score = 10
        else:
            length_score = 5

        score += length_score

        # Keyword score (0-30)
        keyword_score = 0
        for keyword_data in recommended_keywords[:10]:  # Check top 10 keywords
            keyword = keyword_data["keyword"]
            keyword_score_value = keyword_data["score"] * 3  # 0-3 points per keyword

            if keyword.lower() in title.lower():
                keyword_score += keyword_score_value

        score += min(keyword_score, 30)  # Cap at 30

        return min(int(score), 100)  # Cap at 100


class DescriptionOptimizer:
    """Optimizes listing descriptions for eBay search relevance."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the description optimizer."""
        self.config = config or {}
        self.keyword_analyzer = KeywordAnalyzer(config)

    async def optimize_description(
        self, original_description: str, product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """
        Optimize a product description for eBay search relevance.

        Args:
            original_description: Original product description
            product_data: Product data
            category_id: eBay category ID

        Returns:
            Dictionary with optimized description and metadata
        """
        # Get recommended keywords
        recommended_keywords = await self.keyword_analyzer.recommend_keywords(
            product_data, category_id
        )

        # Create HTML description
        html_description = self._create_html_description(
            original_description, product_data, recommended_keywords
        )

        # Calculate SEO score
        seo_score = self._calculate_seo_score(html_description, recommended_keywords)

        return {
            "description": html_description,
            "seo_score": seo_score,
            "keyword_density": self._calculate_keyword_density(
                html_description, recommended_keywords
            ),
            "html_length": len(html_description),
            "recommended_keywords": recommended_keywords[:5],
        }

    def _create_html_description(
        self,
        original_description: str,
        product_data: Dict[str, Any],
        recommended_keywords: List[Dict[str, Any]],
    ) -> str:
        """
        Create an HTML description with SEO enhancements.

        Args:
            original_description: Original product description
            product_data: Product data
            recommended_keywords: Recommended keywords

        Returns:
            HTML description
        """
        # Start with header
        html = "<div style='font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;'>\n"

        # Add product title as H1
        title = product_data.get("title", "")
        if title:
            html += f"<h1 style='color: #333; font-size: 24px;'>{title}</h1>\n"

        # Add product image if available
        images = product_data.get("images", [])
        if images:
            html += "<div style='text-align: center; margin: 20px 0;'>\n"
            for image_url in images[:3]:  # Show up to 3 images
                html += f"<img src='{image_url}' style='max-width: 100%; max-height: 400px; margin: 10px;' alt='{title}'>\n"
            html += "</div>\n"

        # Add product highlights
        features = product_data.get("features", [])
        if features:
            html += "<div style='background-color: #f8f8f8; padding: 15px; margin: 15px 0; border-radius: 5px;'>\n"
            html += (
                "<h2 style='color: #333; font-size: 18px;'>Product Highlights</h2>\n"
            )
            html += "<ul style='margin-left: 20px;'>\n"
            for feature in features:
                html += f"<li style='margin: 8px 0;'>{feature}</li>\n"
            html += "</ul>\n"
            html += "</div>\n"

        # Add original description with keyword enhancement
        html += "<div style='margin: 20px 0;'>\n"
        html += "<h2 style='color: #333; font-size: 18px;'>Product Description</h2>\n"

        # Enhance description with keywords
        enhanced_description = original_description
        for keyword_data in recommended_keywords[:5]:  # Use top 5 keywords
            keyword = keyword_data["keyword"]
            if keyword in enhanced_description.lower():
                # Make some instances of the keyword bold
                pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                enhanced_description = pattern.sub(
                    f"<strong>{keyword}</strong>", enhanced_description, count=1
                )

        # Convert newlines to HTML breaks
        enhanced_description = enhanced_description.replace("\n", "<br>\n")
        html += f"<p style='line-height: 1.6;'>{enhanced_description}</p>\n"
        html += "</div>\n"

        # Add shipping and returns section
        html += "<div style='background-color: #f0f7ff; padding: 15px; margin: 15px 0; border-radius: 5px;'>\n"
        html += "<h2 style='color: #0066cc; font-size: 18px;'>Shipping & Returns</h2>\n"
        html += "<p><strong>Fast Shipping:</strong> We ship within 1 business day of payment.</p>\n"
        html += "<p><strong>Returns:</strong> 30-day money-back guarantee for all items.</p>\n"
        html += "</div>\n"

        # Close main div
        html += "</div>"

        return html

    def _calculate_seo_score(
        self, description: str, recommended_keywords: List[Dict[str, Any]]
    ) -> int:
        """
        Calculate SEO score for a description.

        Args:
            description: Description to score
            recommended_keywords: Recommended keywords with scores

        Returns:
            SEO score (0-100)
        """
        # Base score
        score = 50

        # Length score (0-20)
        if len(description) > 1000:
            length_score = 20
        elif len(description) > 500:
            length_score = 15
        elif len(description) > 300:
            length_score = 10
        else:
            length_score = 5

        score += length_score

        # Keyword score (0-30)
        keyword_score = 0
        for keyword_data in recommended_keywords[:10]:  # Check top 10 keywords
            keyword = keyword_data["keyword"]
            keyword_score_value = keyword_data["score"] * 3  # 0-3 points per keyword

            # Count occurrences
            occurrences = description.lower().count(keyword.lower())
            if occurrences > 0:
                # Score based on occurrences (diminishing returns)
                if occurrences >= 3:
                    keyword_score += keyword_score_value
                elif occurrences == 2:
                    keyword_score += keyword_score_value * 0.8
                else:
                    keyword_score += keyword_score_value * 0.5

        score += min(keyword_score, 30)  # Cap at 30

        return min(int(score), 100)  # Cap at 100

    def _calculate_keyword_density(
        self, description: str, recommended_keywords: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        Calculate keyword density in description.

        Args:
            description: Description to analyze
            recommended_keywords: Recommended keywords

        Returns:
            Dictionary mapping keywords to density percentages
        """
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", description)

        # Convert to lowercase
        text = text.lower()

        # Count total words
        words = re.findall(r"\b\w+\b", text)
        total_words = len(words)

        if total_words == 0:
            return {}

        # Calculate density for each keyword
        density = {}
        for keyword_data in recommended_keywords[:10]:  # Check top 10 keywords
            keyword = keyword_data["keyword"]

            # Count occurrences
            keyword_words = keyword.lower().split()
            if len(keyword_words) == 1:
                # Single word
                occurrences = sum(1 for word in words if word == keyword.lower())
            else:
                # Phrase
                occurrences = text.count(keyword.lower())

            # Calculate density
            density[keyword] = (occurrences / total_words) * 100

        return density


class ItemSpecificsOptimizer:
    """Optimizes item specifics for eBay search relevance."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the item specifics optimizer."""
        self.config = config or {}

    async def optimize_item_specifics(
        self, product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """
        Optimize item specifics for eBay search relevance.

        Args:
            product_data: Product data
            category_id: eBay category ID

        Returns:
            Dictionary with optimized item specifics and metadata
        """
        # Get recommended specifics for category
        recommended_specifics = await self._get_recommended_specifics(category_id)

        # Extract specifics from product data
        extracted_specifics = self._extract_specifics_from_product(product_data)

        # Combine and optimize
        optimized_specifics = {}
        missing_required = []
        missing_recommended = []

        for specific_name, specific_data in recommended_specifics.items():
            is_required = specific_data.get("required", False)

            if specific_name in extracted_specifics:
                # Use extracted value
                optimized_specifics[specific_name] = extracted_specifics[specific_name]
            elif is_required:
                # Missing required specific
                missing_required.append(specific_name)
            else:
                # Missing recommended specific
                missing_recommended.append(specific_name)

        # Calculate completeness score
        total_required = sum(
            1 for data in recommended_specifics.values() if data.get("required", False)
        )
        total_recommended = len(recommended_specifics) - total_required

        if total_required > 0:
            required_score = (
                (total_required - len(missing_required)) / total_required * 100
            )
        else:
            required_score = 100

        if total_recommended > 0:
            recommended_score = (
                (total_recommended - len(missing_recommended)) / total_recommended * 100
            )
        else:
            recommended_score = 100

        # Overall score (required counts more)
        overall_score = (required_score * 0.7) + (recommended_score * 0.3)

        return {
            "item_specifics": optimized_specifics,
            "missing_required": missing_required,
            "missing_recommended": missing_recommended,
            "completeness_score": int(overall_score),
            "required_score": int(required_score),
            "recommended_score": int(recommended_score),
        }

    async def _get_recommended_specifics(
        self, category_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get recommended item specifics for a category using real eBay API.

        Args:
            category_id: eBay category ID

        Returns:
            Dictionary mapping specific names to metadata
        """
        try:
            # Import eBay service here to avoid circular imports
            from fs_agt_clean.services.marketplace.ebay.compat import get_ebay_service

            ebay_service = await get_ebay_service()
            if ebay_service:
                # Get real item specifics from eBay API
                api_response = await ebay_service.get_category_item_specifics(
                    category_id
                )

                if api_response and "specifics" in api_response:
                    # Convert API response to our format
                    specifics = {}
                    for name, data in api_response["specifics"].items():
                        specifics[name] = {
                            "required": data.get("required", False),
                            "importance": data.get("importance", 0.7),
                            "values": data.get("values", []),
                            "max_length": data.get("max_length", 65),
                            "usage": data.get("usage", "OPTIONAL"),
                        }
                    return specifics
        except Exception as e:
            # Log the error but continue with fallback
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to get eBay item specifics for category {category_id}: {e}"
            )

        # Fallback to basic specifics if API call fails
        specifics = {
            "Brand": {
                "required": True,
                "importance": 0.9,
                "values": [],
                "max_length": 65,
                "usage": "REQUIRED",
            },
            "MPN": {
                "required": False,
                "importance": 0.8,
                "values": [],
                "max_length": 65,
                "usage": "OPTIONAL",
            },
            "Model": {
                "required": False,
                "importance": 0.8,
                "values": [],
                "max_length": 65,
                "usage": "OPTIONAL",
            },
            "Color": {
                "required": False,
                "importance": 0.7,
                "values": [],
                "max_length": 65,
                "usage": "OPTIONAL",
            },
            "Size": {
                "required": False,
                "importance": 0.7,
                "values": [],
                "max_length": 65,
                "usage": "OPTIONAL",
            },
            "Material": {
                "required": False,
                "importance": 0.6,
                "values": [],
                "max_length": 65,
                "usage": "OPTIONAL",
            },
            "Style": {
                "required": False,
                "importance": 0.6,
                "values": [],
                "max_length": 65,
                "usage": "OPTIONAL",
            },
            "Features": {
                "required": False,
                "importance": 0.7,
                "values": [],
                "max_length": 65,
                "usage": "OPTIONAL",
            },
            "Country/Region of Manufacture": {
                "required": False,
                "importance": 0.5,
                "values": [],
                "max_length": 65,
                "usage": "OPTIONAL",
            },
        }

        # Add category-specific specifics based on category patterns
        if category_id.startswith("1"):  # Electronics
            specifics.update(
                {
                    "Type": {
                        "required": True,
                        "importance": 0.9,
                        "values": [],
                        "max_length": 65,
                        "usage": "REQUIRED",
                    },
                    "Connectivity": {
                        "required": False,
                        "importance": 0.8,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Storage Capacity": {
                        "required": False,
                        "importance": 0.8,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Screen Size": {
                        "required": False,
                        "importance": 0.7,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Processor": {
                        "required": False,
                        "importance": 0.7,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "RAM": {
                        "required": False,
                        "importance": 0.7,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Operating System": {
                        "required": False,
                        "importance": 0.7,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                }
            )
        elif category_id.startswith("2"):  # Clothing
            specifics.update(
                {
                    "Size Type": {
                        "required": True,
                        "importance": 0.9,
                        "values": [],
                        "max_length": 65,
                        "usage": "REQUIRED",
                    },
                    "Department": {
                        "required": True,
                        "importance": 0.9,
                        "values": [],
                        "max_length": 65,
                        "usage": "REQUIRED",
                    },
                    "Pattern": {
                        "required": False,
                        "importance": 0.7,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Sleeve Length": {
                        "required": False,
                        "importance": 0.7,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Neckline": {
                        "required": False,
                        "importance": 0.6,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                    "Occasion": {
                        "required": False,
                        "importance": 0.6,
                        "values": [],
                        "max_length": 65,
                        "usage": "OPTIONAL",
                    },
                }
            )

        return specifics

    def _extract_specifics_from_product(
        self, product_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Extract item specifics from product data.

        Args:
            product_data: Product data

        Returns:
            Dictionary mapping specific names to values
        """
        specifics = {}

        # Extract from attributes
        attributes = product_data.get("attributes", {})
        for key, value in attributes.items():
            if isinstance(value, (str, int, float, bool)):
                specifics[key] = str(value)

        # Extract common fields
        field_mapping = {
            "brand": "Brand",
            "model": "Model",
            "mpn": "MPN",
            "color": "Color",
            "size": "Size",
            "material": "Material",
            "manufacturer": "Manufacturer",
            "country_of_origin": "Country/Region of Manufacture",
        }

        for source_field, target_field in field_mapping.items():
            if source_field in product_data and product_data[source_field]:
                specifics[target_field] = str(product_data[source_field])

        # Extract from features
        features = product_data.get("features", [])
        if features:
            specifics["Features"] = ", ".join(features[:5])  # Limit to 5 features

        return specifics


class EbaySEOOptimizer:
    """
    Optimizes eBay listings for search visibility.

    This class provides comprehensive SEO optimization for eBay listings,
    including title optimization, description enhancement, and item specifics
    optimization.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the eBay SEO optimizer.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.keyword_analyzer = KeywordAnalyzer(config)
        self.title_optimizer = TitleOptimizer(config)
        self.description_optimizer = DescriptionOptimizer(config)
        self.item_specifics_optimizer = ItemSpecificsOptimizer(config)

    async def analyze_market(
        self, category_id: str, search_terms: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze top-performing listings in a category for SEO patterns.

        Args:
            category_id: eBay category ID
            search_terms: Optional search terms to focus analysis

        Returns:
            Dictionary with market analysis data
        """
        # Get category keywords
        category_keywords = await self.keyword_analyzer.analyze_category(category_id)

        # In a real implementation, this would analyze top listings
        # and extract patterns

        # Mock implementation for structure
        await asyncio.sleep(0.2)  # Simulate analysis

        return {
            "category_id": category_id,
            "top_keywords": category_keywords,
            "average_title_length": 65,
            "average_description_length": 1200,
            "common_item_specifics": ["Brand", "MPN", "Model", "Color"],
            "search_terms": search_terms or [],
        }

    async def optimize_title(
        self, original_title: str, product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """
        Optimize the listing title for eBay search visibility.

        Args:
            original_title: Original product title
            product_data: Product data
            category_id: eBay category ID

        Returns:
            Dictionary with optimized title and metadata
        """
        return await self.title_optimizer.optimize_title(
            original_title, product_data, category_id
        )

    async def optimize_description(
        self, original_description: str, product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """
        Optimize the listing description for eBay search visibility.

        Args:
            original_description: Original product description
            product_data: Product data
            category_id: eBay category ID

        Returns:
            Dictionary with optimized description and metadata
        """
        return await self.description_optimizer.optimize_description(
            original_description, product_data, category_id
        )

    async def optimize_item_specifics(
        self, product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """
        Optimize item specifics for eBay search visibility.

        Args:
            product_data: Product data
            category_id: eBay category ID

        Returns:
            Dictionary with optimized item specifics and metadata
        """
        return await self.item_specifics_optimizer.optimize_item_specifics(
            product_data, category_id
        )

    async def optimize_listing(
        self, product_data: Dict[str, Any], category_id: str
    ) -> Dict[str, Any]:
        """
        Optimize a complete listing for eBay search visibility.

        Args:
            product_data: Product data
            category_id: eBay category ID

        Returns:
            Dictionary with optimized listing data and metadata
        """
        # Get original values
        original_title = product_data.get("title", "")
        original_description = product_data.get("description", "")

        # Optimize components in parallel
        title_task = self.optimize_title(original_title, product_data, category_id)
        description_task = self.optimize_description(
            original_description, product_data, category_id
        )
        item_specifics_task = self.optimize_item_specifics(product_data, category_id)

        # Wait for all optimizations to complete
        title_result, description_result, item_specifics_result = await asyncio.gather(
            title_task, description_task, item_specifics_task
        )

        # Calculate overall SEO score
        title_score = title_result.get("seo_score", 0)
        description_score = description_result.get("seo_score", 0)
        item_specifics_score = item_specifics_result.get("completeness_score", 0)

        # Weight the scores (title is most important)
        overall_score = (
            (title_score * 0.5)
            + (description_score * 0.3)
            + (item_specifics_score * 0.2)
        )

        return {
            "title": title_result.get("title"),
            "description": description_result.get("description"),
            "item_specifics": item_specifics_result.get("item_specifics"),
            "seo_score": int(overall_score),
            "title_score": title_score,
            "description_score": description_score,
            "item_specifics_score": item_specifics_score,
            "missing_required_specifics": item_specifics_result.get(
                "missing_required", []
            ),
            "recommended_keywords": title_result.get("recommended_keywords", []),
        }
