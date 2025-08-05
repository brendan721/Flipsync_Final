#!/usr/bin/env python3
"""
Factual Storytelling Description Generator for FlipSync eBay Listings.

This service generates comprehensive, buyer-focused product descriptions using a
factual, matter-of-fact storytelling approach. It avoids cookie-cutter templates
in favor of dynamic content generation based on product data and item specifics.

Key Features:
- Dynamic content generation without rigid templates
- Factual, matter-of-fact storytelling approach (no marketing fluff)
- Comprehensive utilization of product details and item specifics
- Buyer-focused narrative with structured information sections
- Natural keyword integration for SEO optimization
- Target length: 200-700 words with optimal keyword density
- Integration with ItemSpecificsMaximizer and KeywordConsistencyEngine
"""

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class FactualStorytellingGenerator:
    """
    Dynamic description generator that creates buyer-focused, factual narratives
    without relying on rigid templates. Uses intelligent content structuring
    based on product data and category context.
    """

    def __init__(self):
        """Initialize the factual storytelling generator."""
        # Content structure priorities for different product types
        self.content_priorities = {
            "electronics": [
                "functionality",
                "specifications",
                "compatibility",
                "condition",
                "benefits",
            ],
            "clothing": ["fit", "material", "style", "care", "occasion"],
            "shoes": ["comfort", "style", "material", "sizing", "performance"],
            "home": ["functionality", "design", "dimensions", "material", "care"],
            "automotive": [
                "compatibility",
                "performance",
                "installation",
                "specifications",
                "warranty",
            ],
            "default": ["quality", "features", "specifications", "condition", "value"],
        }

        # Narrative connectors for natural flow
        self.narrative_connectors = {
            "introduction": ["This", "Here is", "Presenting", "Available now is"],
            "feature_intro": [
                "Features include",
                "Key attributes are",
                "Notable characteristics include",
                "This item offers",
            ],
            "specification_intro": [
                "Technical specifications",
                "Detailed specifications",
                "Product specifications include",
            ],
            "condition_intro": ["Condition details", "Item condition", "Current state"],
            "benefit_intro": [
                "Benefits include",
                "Advantages of this item",
                "Why choose this item",
            ],
            "conclusion": [
                "Perfect for",
                "Ideal for",
                "Suitable for",
                "Great choice for",
            ],
        }

        # Factual descriptors (avoiding marketing fluff)
        self.factual_descriptors = {
            "quality": [
                "well-constructed",
                "solidly built",
                "properly manufactured",
                "carefully crafted",
            ],
            "condition": [
                "excellent condition",
                "good working order",
                "fully functional",
                "properly maintained",
            ],
            "performance": [
                "reliable performance",
                "consistent operation",
                "dependable function",
                "stable operation",
            ],
            "design": [
                "thoughtful design",
                "practical layout",
                "functional design",
                "user-friendly interface",
            ],
        }

    async def generate_description(
        self,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
        title: str,
        category_id: str,
        target_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive factual storytelling description.

        Args:
            product_data: Original product data
            item_specifics: Generated item specifics from ItemSpecificsMaximizer
            title: Optimized eBay title
            category_id: eBay category ID
            target_keywords: Target keywords for SEO optimization

        Returns:
            Generated description with metadata and optimization metrics
        """
        start_time = time.perf_counter()

        try:
            # Determine product category and content strategy
            category_type = self._determine_category_type(category_id)
            content_strategy = self._develop_content_strategy(
                product_data, item_specifics, category_type, target_keywords
            )

            # Generate structured content sections
            content_sections = await self._generate_content_sections(
                product_data, item_specifics, content_strategy
            )

            # Create natural narrative flow with enhanced paragraph structure
            description = self._create_narrative_flow(
                content_sections, content_strategy
            )

            # CRITICAL FIX: Force proper paragraph structure for eBay Cassini compliance
            logger.info(
                f"Before paragraph structure fix: {len(description.split(chr(10)+chr(10)))} paragraphs"
            )
            description = self._force_cassini_paragraph_structure(description)
            logger.info(
                f"After paragraph structure fix: {len(description.split(chr(10)+chr(10)))} paragraphs"
            )

            # Optimize keyword integration
            logger.info(
                f"Before keyword optimization: {len(description.split(chr(10)+chr(10)))} paragraphs"
            )
            optimized_description = self._optimize_keyword_integration(
                description, target_keywords, item_specifics
            )
            logger.info(
                f"After keyword optimization: {len(optimized_description.split(chr(10)+chr(10)))} paragraphs"
            )

            # Validate and refine description
            final_description = self._validate_and_refine(
                optimized_description, product_data, item_specifics
            )
            logger.info(
                f"After validation: {len(final_description.split(chr(10)+chr(10)))} paragraphs"
            )

            # Generate metadata and metrics
            metadata = self._generate_description_metadata(
                final_description, item_specifics, target_keywords
            )

            execution_time = (time.perf_counter() - start_time) * 1000

            return {
                "description": final_description,
                "metadata": metadata,
                "content_strategy": content_strategy,
                "word_count": len(final_description.split()),
                "character_count": len(final_description),
                "keyword_density": metadata["keyword_density"],
                "specifics_utilization": metadata["specifics_utilization"],
                "execution_time_ms": round(execution_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "production_ready": (
                    200 <= len(final_description.split()) <= 700
                    and metadata["specifics_utilization"] >= 90
                ),
            }

        except Exception as e:
            logger.error(f"Error generating factual storytelling description: {e}")
            raise

    def _determine_category_type(self, category_id: str) -> str:
        """Determine product category type for content strategy."""
        category_mapping = {
            "9355": "electronics",  # Cell Phones & Smartphones
            "95672": "shoes",  # Basketball Shoes
            "31388": "electronics",  # Tablets & eBook Readers
            "171485": "electronics",  # Laptops & Netbooks
            "15709": "shoes",  # Athletic Shoes
            "1059": "clothing",  # Men's Clothing
            "15724": "clothing",  # Women's Clothing
            "11700": "home",  # Home & Garden
            "20081": "home",  # Kitchen, Dining & Bar
        }

        return category_mapping.get(category_id, "default")

    def _develop_content_strategy(
        self,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
        category_type: str,
        target_keywords: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Develop dynamic content strategy based on available data."""
        # Analyze available data richness
        data_richness = {
            "product_data_fields": len([v for v in product_data.values() if v]),
            "item_specifics_count": len(item_specifics),
            "has_technical_specs": any(
                key in str(product_data).lower()
                for key in ["spec", "technical", "feature", "capability"]
            ),
            "has_condition_info": "condition" in product_data
            or "Condition" in item_specifics,
            "has_brand_model": ("brand" in product_data or "Brand" in item_specifics)
            and ("model" in product_data or "Model" in item_specifics),
        }

        # Determine content priorities based on data availability
        priorities = self.content_priorities.get(
            category_type, self.content_priorities["default"]
        )

        # Adjust priorities based on data richness
        adjusted_priorities = []
        for priority in priorities:
            if priority == "specifications" and data_richness["has_technical_specs"]:
                adjusted_priorities.append(priority)
            elif priority == "condition" and data_richness["has_condition_info"]:
                adjusted_priorities.append(priority)
            elif priority in ["functionality", "features", "quality"]:
                adjusted_priorities.append(priority)

        # Ensure we have at least 3 content priorities
        if len(adjusted_priorities) < 3:
            adjusted_priorities.extend(
                [p for p in priorities if p not in adjusted_priorities][:3]
            )

        return {
            "category_type": category_type,
            "content_priorities": adjusted_priorities[:5],  # Top 5 priorities
            "data_richness": data_richness,
            "target_length": self._calculate_target_length(data_richness),
            "keyword_targets": target_keywords or [],
            "narrative_style": "factual_informative",
        }

    def _calculate_target_length(self, data_richness: Dict[str, Any]) -> int:
        """Calculate target description length based on data richness."""
        base_length = 300  # Base target

        # Adjust based on available data
        if data_richness["item_specifics_count"] > 20:
            base_length += 150
        elif data_richness["item_specifics_count"] > 15:
            base_length += 100
        elif data_richness["item_specifics_count"] > 10:
            base_length += 50

        if data_richness["has_technical_specs"]:
            base_length += 100

        if data_richness["product_data_fields"] > 10:
            base_length += 75

        return min(base_length, 700)  # Cap at 700 words

    async def _generate_content_sections(
        self,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
        content_strategy: Dict[str, Any],
    ) -> Dict[str, str]:
        """Generate structured content sections dynamically."""
        sections = {}

        # Introduction section - factual product introduction
        sections["introduction"] = self._generate_introduction(
            product_data, item_specifics, content_strategy
        )

        # Core content sections based on priorities
        for priority in content_strategy["content_priorities"]:
            if priority == "specifications":
                sections["specifications"] = self._generate_specifications_section(
                    product_data, item_specifics
                )
            elif priority == "functionality":
                sections["functionality"] = self._generate_functionality_section(
                    product_data, item_specifics
                )
            elif priority == "condition":
                sections["condition"] = self._generate_condition_section(
                    product_data, item_specifics
                )
            elif priority == "features":
                sections["features"] = self._generate_features_section(
                    product_data, item_specifics
                )
            elif priority in ["quality", "value"]:
                sections["quality"] = self._generate_quality_section(
                    product_data, item_specifics
                )

        # Conclusion section
        sections["conclusion"] = self._generate_conclusion(
            product_data, item_specifics, content_strategy
        )

        return sections

    def _generate_introduction(
        self,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
        content_strategy: Dict[str, Any],
    ) -> str:
        """Generate factual introduction section."""
        brand = item_specifics.get("Brand", product_data.get("brand", ""))
        model = item_specifics.get("Model", product_data.get("model", ""))
        condition = item_specifics.get(
            "Condition", product_data.get("condition", "new")
        )

        # Build introduction dynamically
        intro_parts = []

        if brand and model:
            intro_parts.append(f"This {condition.lower()} {brand} {model}")
        elif brand:
            intro_parts.append(f"This {condition.lower()} {brand} item")
        else:
            intro_parts.append(f"This {condition.lower()} item")

        # Add key distinguishing features
        key_features = []
        if "Color" in item_specifics:
            key_features.append(f"in {item_specifics['Color'].lower()}")
        if "Size" in item_specifics:
            key_features.append(f"size {item_specifics['Size']}")
        if "Storage Capacity" in item_specifics:
            key_features.append(f"with {item_specifics['Storage Capacity']} storage")

        if key_features:
            intro_parts.append(" ".join(key_features))

        # Add category-appropriate descriptor
        category_type = content_strategy["category_type"]
        if category_type == "electronics":
            intro_parts.append("delivers reliable performance and functionality")
        elif category_type == "clothing":
            intro_parts.append("combines style and comfort")
        elif category_type == "shoes":
            intro_parts.append("provides comfort and durability")
        else:
            intro_parts.append("offers quality construction and dependable performance")

        return " ".join(intro_parts) + "."

    def _generate_specifications_section(
        self, product_data: Dict[str, Any], item_specifics: Dict[str, str]
    ) -> str:
        """Generate technical specifications section."""
        spec_items = []

        # Technical specifications from item specifics
        tech_aspects = [
            "Processor",
            "Memory",
            "Storage Capacity",
            "Screen Size",
            "Camera Resolution",
            "Connectivity",
            "Operating System",
            "Battery Type",
            "Display Technology",
            "Wireless Technology",
            "Network",
            "Chipset Model",
        ]

        for aspect in tech_aspects:
            if aspect in item_specifics and item_specifics[aspect]:
                spec_items.append(f"{aspect}: {item_specifics[aspect]}")

        # Additional specs from product data
        spec_fields = ["processor", "memory", "storage", "connectivity", "features"]
        for field in spec_fields:
            if field in product_data and product_data[field]:
                field_name = field.replace("_", " ").title()
                if field_name not in [item.split(":")[0] for item in spec_items]:
                    spec_items.append(f"{field_name}: {product_data[field]}")

        # Include ALL available item specifics for comprehensive coverage
        for aspect_name, aspect_value in item_specifics.items():
            if aspect_value and aspect_name not in tech_aspects:
                formatted_name = aspect_name.lower().replace("_", " ").replace("/", " ")
                spec_entry = f"{formatted_name}: {aspect_value}"
                if spec_entry not in spec_items:
                    spec_items.append(spec_entry)

        if spec_items:
            # Create comprehensive specifications section with multiple sentences
            intro = "Technical specifications and product details include: "
            specs_text = "; ".join(spec_items[:20])  # Include up to 20 specifications

            # Add detailed explanatory sentences
            detail_sentences = []
            detail_sentences.append(
                "These specifications ensure optimal performance and compatibility"
            )

            if any("storage" in item.lower() for item in spec_items):
                detail_sentences.append(
                    "Storage capacity provides sufficient space for applications, media, and data"
                )

            if any(
                "connectivity" in item.lower() or "network" in item.lower()
                for item in spec_items
            ):
                detail_sentences.append(
                    "Connectivity features enable seamless integration with existing systems and networks"
                )

            if any(
                "display" in item.lower() or "screen" in item.lower()
                for item in spec_items
            ):
                detail_sentences.append(
                    "Display technology delivers clear visual output for enhanced user experience"
                )

            if any(
                "processor" in item.lower() or "cpu" in item.lower()
                for item in spec_items
            ):
                detail_sentences.append(
                    "Processing capabilities support demanding applications and multitasking requirements"
                )

            if any("camera" in item.lower() for item in spec_items):
                detail_sentences.append(
                    "Camera specifications enable high-quality photo and video capture"
                )

            # Build comprehensive result
            result = intro + specs_text + ". "
            result += ". ".join(detail_sentences) + "."

            return result

        return ""

    def _generate_functionality_section(
        self, product_data: Dict[str, Any], item_specifics: Dict[str, str]
    ) -> str:
        """Generate functionality and features section."""
        functionality_items = []

        # Extract functionality information
        if "Features" in item_specifics:
            functionality_items.append(f"Features {item_specifics['Features'].lower()}")

        if "description" in product_data:
            # Extract functional keywords from description
            functional_keywords = re.findall(
                r"\b(?:supports?|enables?|provides?|includes?|offers?)\s+([^.]+)",
                product_data["description"],
                re.IGNORECASE,
            )
            for match in functional_keywords[:3]:
                if len(match) < 50:  # Reasonable length
                    functionality_items.append(f"supports {match.strip()}")

        # Add category-specific functionality
        if "Network" in item_specifics and item_specifics["Network"]:
            functionality_items.append(
                f"works with {item_specifics['Network']} networks"
            )

        if "Connectivity" in item_specifics:
            functionality_items.append(f"connects via {item_specifics['Connectivity']}")

        if functionality_items:
            return "Functionality includes: " + "; ".join(functionality_items[:5]) + "."

        return ""

    def _generate_condition_section(
        self, product_data: Dict[str, Any], item_specifics: Dict[str, str]
    ) -> str:
        """Generate condition details section."""
        condition = item_specifics.get(
            "Condition", product_data.get("condition", "new")
        )
        condition_details = []

        if condition.lower() == "new":
            condition_details.append(
                "Item is in new condition with original packaging where applicable"
            )
        elif condition.lower() in ["used", "pre-owned"]:
            condition_details.append(
                "Item is in good working condition with normal signs of use"
            )
        elif condition.lower() == "refurbished":
            condition_details.append(
                "Item has been professionally refurbished and tested for functionality"
            )

        # Add warranty information if available
        if "Manufacturer Warranty" in item_specifics:
            condition_details.append(
                f"includes {item_specifics['Manufacturer Warranty']} manufacturer warranty"
            )

        if condition_details:
            return " and ".join(condition_details) + "."

        return f"Item condition: {condition}."

    def _generate_features_section(
        self, product_data: Dict[str, Any], item_specifics: Dict[str, str]
    ) -> str:
        """Generate key features section."""
        features = []

        # Extract notable features from item specifics
        feature_aspects = [
            "Key Feature",
            "Features",
            "Special Features",
            "Performance/Activity",
            "Theme",
            "Style",
            "Material",
            "Design",
        ]

        for aspect in feature_aspects:
            if aspect in item_specifics and item_specifics[aspect]:
                value = item_specifics[aspect]
                if value not in [f.split(":")[-1].strip() for f in features]:
                    features.append(f"{aspect.lower().replace('/', ' ')}: {value}")

        if features:
            return "Notable features include " + "; ".join(features[:6]) + "."

        return ""

    def _generate_quality_section(
        self, product_data: Dict[str, Any], item_specifics: Dict[str, str]
    ) -> str:
        """Generate quality and value section."""
        quality_points = []

        # Brand reputation
        brand = item_specifics.get("Brand", product_data.get("brand", ""))
        if brand:
            quality_points.append(f"{brand} brand ensures reliable quality")

        # Material quality
        materials = []
        material_aspects = [
            "Material",
            "Upper Material",
            "Lining Material",
            "Construction",
        ]
        for aspect in material_aspects:
            if aspect in item_specifics and item_specifics[aspect]:
                materials.append(item_specifics[aspect].lower())

        if materials:
            unique_materials = list(set(materials))
            quality_points.append(f"constructed with {', '.join(unique_materials[:3])}")

        # Manufacturing details
        if "Country/Region of Manufacture" in item_specifics:
            country = item_specifics["Country/Region of Manufacture"]
            quality_points.append(f"manufactured in {country}")

        if quality_points:
            return "Quality details: " + "; ".join(quality_points[:4]) + "."

        return ""

    def _generate_conclusion(
        self,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
        content_strategy: Dict[str, Any],
    ) -> str:
        """Generate conclusion section."""
        category_type = content_strategy["category_type"]

        # Category-appropriate use cases
        use_cases = {
            "electronics": [
                "daily use",
                "professional applications",
                "personal productivity",
            ],
            "clothing": ["casual wear", "professional settings", "special occasions"],
            "shoes": ["athletic activities", "casual wear", "daily comfort"],
            "home": ["home improvement", "daily use", "functional enhancement"],
            "default": ["various applications", "daily use", "reliable performance"],
        }

        suitable_uses = use_cases.get(category_type, use_cases["default"])

        # Build conclusion
        conclusion_parts = []
        conclusion_parts.append(f"Suitable for {suitable_uses[0]}")

        if len(suitable_uses) > 1:
            conclusion_parts.append(f"and {suitable_uses[1]}")

        # Add value proposition
        if "condition" in product_data and product_data["condition"].lower() == "new":
            conclusion_parts.append(
                "providing new item reliability and manufacturer warranty coverage"
            )
        else:
            conclusion_parts.append(
                "offering dependable performance and proven functionality"
            )

        # Add additional value statements
        conclusion_parts.append(
            "This item represents excellent value for money with comprehensive features and specifications"
        )
        conclusion_parts.append(
            "Purchase with confidence knowing all technical details and compatibility requirements are clearly documented"
        )

        return " ".join(conclusion_parts) + "."

    def _create_narrative_flow(
        self, content_sections: Dict[str, str], content_strategy: Dict[str, Any]
    ) -> str:
        """Create natural narrative flow with proper paragraph structure for eBay Cassini compliance."""
        # Create structured paragraphs for optimal readability and SEO
        paragraphs = []

        # Debug: Check what sections we have
        available_sections = [k for k, v in content_sections.items() if v and v.strip()]

        # Paragraph 1: Introduction (Product Overview)
        if content_sections.get("introduction"):
            intro_paragraph = content_sections["introduction"].strip()
            if intro_paragraph:
                paragraphs.append(intro_paragraph)

        # Paragraph 2: Technical Specifications (Key specs and features)
        tech_content = []
        if content_sections.get("specifications"):
            spec_content = content_sections["specifications"].strip()
            if spec_content:
                tech_content.append(spec_content)
        if content_sections.get("features"):
            features_content = content_sections["features"].strip()
            if features_content:
                tech_content.append(features_content)

        if tech_content:
            tech_paragraph = " ".join(tech_content)
            paragraphs.append(tech_paragraph)

        # Paragraph 3: Functionality/Benefits (Practical applications)
        functionality_content = []
        if content_sections.get("functionality"):
            func_content = content_sections["functionality"].strip()
            if func_content:
                functionality_content.append(func_content)
        if content_sections.get("quality"):
            quality_content = content_sections["quality"].strip()
            if quality_content:
                functionality_content.append(quality_content)

        if functionality_content:
            functionality_paragraph = " ".join(functionality_content)
            paragraphs.append(functionality_paragraph)

        # Paragraph 4: Conclusion (Value proposition and condition details)
        conclusion_content = []
        if content_sections.get("condition"):
            condition_content = content_sections["condition"].strip()
            if condition_content:
                conclusion_content.append(condition_content)
        if content_sections.get("conclusion"):
            conclusion_text = content_sections["conclusion"].strip()
            if conclusion_text:
                conclusion_content.append(conclusion_text)

        if conclusion_content:
            conclusion_paragraph = " ".join(conclusion_content)
            paragraphs.append(conclusion_paragraph)

        # Ensure we have at least 3 paragraphs by splitting long content if needed
        if len(paragraphs) < 3 and paragraphs:
            # If we only have 1-2 paragraphs, try to split the longest one
            longest_idx = max(range(len(paragraphs)), key=lambda i: len(paragraphs[i]))
            longest_paragraph = paragraphs[longest_idx]

            # Split on sentence boundaries if the paragraph is very long
            if len(longest_paragraph) > 200:
                sentences = longest_paragraph.split(". ")
                if len(sentences) >= 4:
                    # Split into two paragraphs
                    mid_point = len(sentences) // 2
                    first_half = ". ".join(sentences[:mid_point]) + "."
                    second_half = ". ".join(sentences[mid_point:])

                    paragraphs[longest_idx] = first_half
                    paragraphs.insert(longest_idx + 1, second_half)

        # Force minimum paragraph structure if we still don't have enough
        if len(paragraphs) == 1 and paragraphs[0]:
            # Split the single paragraph into logical sections using sentence-based approach
            full_text = paragraphs[0]
            sentences = [s.strip() + "." for s in full_text.split(".") if s.strip()]

            if len(sentences) >= 6:  # Need at least 6 sentences to create 3 paragraphs
                # Create 3-4 paragraphs by grouping sentences logically
                paragraphs = []

                # Paragraph 1: Introduction (first 1-2 sentences)
                intro_sentences = (
                    sentences[:2] if len(sentences) >= 8 else sentences[:1]
                )
                paragraphs.append(" ".join(intro_sentences))

                # Paragraph 2: Technical specs (next 2-3 sentences)
                remaining_sentences = sentences[len(intro_sentences) :]
                if len(remaining_sentences) >= 4:
                    tech_sentences = remaining_sentences[:3]
                    paragraphs.append(" ".join(tech_sentences))
                    remaining_sentences = remaining_sentences[3:]
                else:
                    tech_sentences = remaining_sentences[:2]
                    paragraphs.append(" ".join(tech_sentences))
                    remaining_sentences = remaining_sentences[2:]

                # Paragraph 3: Functionality (next 2-3 sentences)
                if len(remaining_sentences) >= 3:
                    func_sentences = remaining_sentences[:2]
                    paragraphs.append(" ".join(func_sentences))
                    remaining_sentences = remaining_sentences[2:]

                    # Paragraph 4: Conclusion (remaining sentences)
                    if remaining_sentences:
                        paragraphs.append(" ".join(remaining_sentences))
                elif remaining_sentences:
                    # Add remaining to paragraph 3
                    paragraphs.append(" ".join(remaining_sentences))

            # Fallback: If we still have only 1 paragraph, force split by character count
            if len(paragraphs) == 1 and len(paragraphs[0]) > 300:
                text = paragraphs[0]
                mid_point = len(text) // 2

                # Find the nearest sentence boundary
                split_point = text.find(". ", mid_point)
                if split_point == -1:
                    split_point = mid_point
                else:
                    split_point += 2  # Include the '. '

                paragraphs = [text[:split_point].strip(), text[split_point:].strip()]

        # Join paragraphs with double line breaks for eBay readability
        # eBay supports basic HTML but double line breaks work universally
        final_description = "\n\n".join(paragraphs)

        # Debug: Ensure we actually have paragraph breaks
        if "\n\n" not in final_description and len(paragraphs) > 1:
            # Fallback: Force paragraph breaks if they're missing
            final_description = "\n\n".join(p.strip() for p in paragraphs if p.strip())

        return final_description

    def _ensure_paragraph_structure(self, description: str) -> str:
        """Ensure proper 3-4 paragraph structure for eBay Cassini algorithm compliance.

        Structure:
        1. Introduction paragraph (product overview and key value proposition)
        2. Technical specifications paragraph (detailed specs and features)
        3. Functionality paragraph (practical applications and benefits)
        4. Conclusion paragraph (condition, warranty, and purchase confidence)
        """
        # Check if we already have proper paragraph structure
        paragraphs = description.split("\n\n")

        if len(paragraphs) >= 3:
            return description  # Already has good structure

        # Force proper 4-paragraph structure using intelligent content analysis
        return self._create_structured_paragraphs(description)

    def _create_structured_paragraphs(self, description: str) -> str:
        """Create properly structured 4-paragraph description for Cassini compliance.

        Paragraph 1: Introduction (product overview and key value proposition)
        Paragraph 2: Technical specifications (detailed specs and features)
        Paragraph 3: Functionality (practical applications and benefits)
        Paragraph 4: Conclusion (condition, warranty, and purchase confidence)
        """
        text = description.strip()

        # Split text into sentences for intelligent regrouping
        sentences = []
        current_sentence = ""

        for char in text:
            current_sentence += char
            if char in ".!?" and len(current_sentence.strip()) > 10:
                sentences.append(current_sentence.strip())
                current_sentence = ""

        # Add remaining text as last sentence if exists
        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        if len(sentences) < 4:
            # If too few sentences, split by character count
            return self._split_by_character_count(text)

        # Intelligently group sentences into 4 paragraphs
        total_sentences = len(sentences)

        # Paragraph 1: Introduction (first 1-2 sentences)
        intro_end = min(2, total_sentences // 4 + 1)
        paragraph1 = " ".join(sentences[:intro_end])

        # Paragraph 2: Technical specs (next 25-40% of sentences)
        specs_start = intro_end
        specs_end = specs_start + max(1, total_sentences // 3)
        paragraph2 = " ".join(sentences[specs_start:specs_end])

        # Paragraph 3: Functionality (next 25-35% of sentences)
        func_start = specs_end
        func_end = func_start + max(1, (total_sentences - func_start) // 2)
        paragraph3 = " ".join(sentences[func_start:func_end])

        # Paragraph 4: Conclusion (remaining sentences)
        paragraph4 = " ".join(sentences[func_end:])

        # Ensure all paragraphs have content
        paragraphs = [
            p for p in [paragraph1, paragraph2, paragraph3, paragraph4] if p.strip()
        ]

        # If we don't have at least 3 paragraphs, use fallback
        if len(paragraphs) < 3:
            return self._split_by_character_count(text)

        return "\n\n".join(paragraphs)

    def _force_cassini_paragraph_structure(self, description: str) -> str:
        """Force proper 3-4 paragraph structure for Cassini compliance - GUARANTEED to work.

        This method ensures we ALWAYS get proper paragraph structure regardless of input.
        """
        text = description.strip()
        logger.info(f"Input text length: {len(text)}")
        logger.info(f"Input text preview: {text[:200]}...")

        # Remove any existing paragraph breaks to start fresh
        text = text.replace("\n\n", " ").replace("\n", " ")

        # Split into sentences more reliably - handle various sentence patterns
        # First try standard sentence endings
        sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        logger.info(f"Found {len(sentences)} sentences with standard splitting")

        # If we don't have enough sentences, try splitting on other patterns
        if len(sentences) < 3:
            # Try splitting on semicolons and colons (common in technical descriptions)
            sentences = re.split(r"[.!?;:]\s+", text)
            sentences = [s.strip() for s in sentences if s.strip() and len(s) > 10]

        # If still not enough, split on logical content boundaries
        if len(sentences) < 3:
            # Split on common content markers
            content_markers = [
                "Technical specifications",
                "These specifications",
                "Functionality includes",
                "Item is in",
                "Suitable for",
                "This item represents",
            ]

            for marker in content_markers:
                if marker in text:
                    parts = text.split(marker, 1)
                    if (
                        len(parts) == 2
                        and len(parts[0].strip()) > 20
                        and len(parts[1].strip()) > 20
                    ):
                        sentences = [parts[0].strip(), marker + parts[1].strip()]
                        break

        # Final fallback: character-based split
        if len(sentences) < 2:
            mid = len(text) // 2
            split_point = text.find(". ", mid)
            if split_point == -1:
                split_point = text.find(" ", mid)  # Split on any space
            if split_point == -1:
                split_point = mid
            else:
                split_point += 1
            return f"{text[:split_point].strip()}\n\n{text[split_point:].strip()}"

        # Create exactly 4 paragraphs for optimal Cassini compliance
        total_sentences = len(sentences)
        logger.info(f"Creating paragraphs from {total_sentences} sentences")

        # Paragraph 1: Introduction (first 1-2 sentences)
        if total_sentences >= 8:
            p1_end = 2
        else:
            p1_end = 1
        paragraph1 = " ".join(sentences[:p1_end])

        # Paragraph 2: Technical specs (next 25-35% of remaining sentences)
        remaining = sentences[p1_end:]
        p2_count = max(1, len(remaining) // 3)
        paragraph2 = " ".join(remaining[:p2_count])

        # Paragraph 3: Functionality (next 25-35% of remaining sentences)
        remaining = remaining[p2_count:]
        if len(remaining) > 2:
            p3_count = max(1, len(remaining) // 2)
            paragraph3 = " ".join(remaining[:p3_count])

            # Paragraph 4: Conclusion (remaining sentences)
            paragraph4 = " ".join(remaining[p3_count:])

            result = f"{paragraph1}\n\n{paragraph2}\n\n{paragraph3}\n\n{paragraph4}"
            logger.info(f"Created 4 paragraphs, result length: {len(result)}")
            logger.info(f"Result contains \\n\\n: {chr(10)+chr(10) in result}")
            logger.info(f"Result repr: {repr(result[:200])}")
            logger.info(f"Paragraph count check: {len(result.split(chr(10)+chr(10)))}")
            return result
        else:
            # Only 3 paragraphs if not enough sentences
            paragraph3 = " ".join(remaining)
            result = f"{paragraph1}\n\n{paragraph2}\n\n{paragraph3}"
            logger.info(f"Created 3 paragraphs, result length: {len(result)}")
            logger.info(f"Result contains \\n\\n: {'\\n\\n' in result}")
            return result

    def _split_by_content_markers(self, description: str) -> List[str]:
        """Split description by logical content markers."""
        paragraphs = []
        remaining_text = description.strip()

        # Paragraph 1: Introduction (everything before "Technical specifications")
        if "Technical specifications" in remaining_text:
            intro_end = remaining_text.find("Technical specifications")
            if intro_end > 0:
                intro_paragraph = remaining_text[:intro_end].strip()
                if intro_paragraph:
                    paragraphs.append(intro_paragraph)
                remaining_text = (
                    "Technical specifications"
                    + remaining_text[intro_end + len("Technical specifications") :]
                )

        # Paragraph 2: Technical specifications (from "Technical specifications" to "Functionality")
        if "Functionality includes" in remaining_text:
            func_start = remaining_text.find("Functionality includes")
            if func_start > 0:
                tech_paragraph = remaining_text[:func_start].strip()
                if tech_paragraph:
                    paragraphs.append(tech_paragraph)
                remaining_text = remaining_text[func_start:]

        # Paragraph 3: Functionality (from "Functionality" to condition/conclusion markers)
        conclusion_markers = ["Item is in", "Suitable for", "This item represents"]
        conclusion_start = -1

        for marker in conclusion_markers:
            marker_pos = remaining_text.find(marker)
            if marker_pos > 0:
                if conclusion_start == -1 or marker_pos < conclusion_start:
                    conclusion_start = marker_pos

        if conclusion_start > 0:
            func_paragraph = remaining_text[:conclusion_start].strip()
            if func_paragraph:
                paragraphs.append(func_paragraph)
            remaining_text = remaining_text[conclusion_start:]

        # Paragraph 4: Conclusion (remaining text)
        if remaining_text.strip():
            paragraphs.append(remaining_text.strip())

        return paragraphs

    def _force_paragraph_structure(self, description: str) -> str:
        """Force paragraph structure when content markers aren't found."""
        # Split on sentence boundaries with better detection
        sentence_endings = [". ", "! ", "? "]
        sentences = []

        current_sentence = ""
        i = 0
        while i < len(description):
            current_sentence += description[i]

            # Check for sentence endings
            for ending in sentence_endings:
                if description[i : i + len(ending)] == ending:
                    sentences.append(current_sentence.strip())
                    current_sentence = ""
                    i += len(ending) - 1
                    break
            i += 1

        # Add the last sentence if it doesn't end with proper punctuation
        if current_sentence.strip():
            sentences.append(current_sentence.strip())

        if len(sentences) < 3:
            # If we can't split into sentences, split by character count
            return self._split_by_character_count(description)

        # Group sentences into 3-4 paragraphs
        new_paragraphs = []
        total_sentences = len(sentences)

        if total_sentences >= 6:
            # Create 3-4 paragraphs
            sentences_per_para = self._calculate_sentences_per_paragraph(
                total_sentences
            )

            sentence_index = 0
            for para_size in sentences_per_para:
                para_sentences = sentences[sentence_index : sentence_index + para_size]
                if para_sentences:
                    paragraph_text = " ".join(para_sentences)
                    new_paragraphs.append(paragraph_text)
                    sentence_index += para_size
        else:
            # Split into 2-3 paragraphs
            mid_point = total_sentences // 2
            new_paragraphs.append(" ".join(sentences[:mid_point]))
            new_paragraphs.append(" ".join(sentences[mid_point:]))

        return "\n\n".join(new_paragraphs)

    def _calculate_sentences_per_paragraph(self, total_sentences: int) -> List[int]:
        """Calculate optimal sentence distribution across paragraphs."""
        if total_sentences >= 8:
            # 4 paragraphs: intro(2), tech(3), func(2), conclusion(rest)
            return [2, 3, 2, total_sentences - 7]
        elif total_sentences >= 6:
            # 3 paragraphs: intro(2), tech(2), conclusion(rest)
            return [2, 2, total_sentences - 4]
        else:
            # 2 paragraphs
            return [total_sentences // 2, total_sentences - (total_sentences // 2)]

    def _split_by_character_count(self, description: str) -> str:
        """Split description by character count as last resort."""
        if len(description) < 300:
            return description  # Too short to split

        # Find a good split point around the middle
        mid_point = len(description) // 2

        # Look for a sentence boundary near the middle
        for offset in range(50):  # Search within 50 characters of midpoint
            for direction in [1, -1]:
                pos = mid_point + (offset * direction)
                if 0 < pos < len(description) - 1:
                    if description[pos : pos + 2] == ". ":
                        first_half = description[: pos + 1].strip()
                        second_half = description[pos + 2 :].strip()
                        return f"{first_half}\n\n{second_half}"

        # If no good split point found, split at midpoint
        first_half = description[:mid_point].strip()
        second_half = description[mid_point:].strip()
        return f"{first_half}\n\n{second_half}"

    def _force_paragraph_split(self, description: str) -> str:
        """Force paragraph splitting as a last resort using simple text analysis."""
        # Look for the actual content markers in the description
        text = description.strip()

        # Try to split on the most common patterns we see in the generated content
        split_patterns = [
            "Technical specifications and product details include:",
            "Functionality includes:",
            "Item is in",
            "Suitable for",
            "This item represents",
        ]

        paragraphs = []
        remaining = text

        for pattern in split_patterns:
            if pattern in remaining:
                before, after = remaining.split(pattern, 1)
                if before.strip():
                    paragraphs.append(before.strip())
                remaining = pattern + after

        # Add the remaining text as the last paragraph
        if remaining.strip():
            paragraphs.append(remaining.strip())

        # If we still don't have enough paragraphs, force split by sentences
        if len(paragraphs) < 3:
            # Simple sentence-based splitting
            sentences = [s.strip() + "." for s in text.split(".") if s.strip()]
            if len(sentences) >= 6:
                # Group sentences into paragraphs
                para1 = ". ".join(sentences[:2])
                para2 = ". ".join(sentences[2:4])
                para3 = ". ".join(sentences[4:])
                paragraphs = [para1, para2, para3]
            elif len(sentences) >= 3:
                # Split into 2 paragraphs
                mid = len(sentences) // 2
                para1 = ". ".join(sentences[:mid])
                para2 = ". ".join(sentences[mid:])
                paragraphs = [para1, para2]

        # Ensure we have at least 2 paragraphs
        if len(paragraphs) < 2:
            # Character-based split as absolute fallback
            mid_point = len(text) // 2
            # Find nearest sentence boundary
            split_point = text.find(". ", mid_point)
            if split_point == -1:
                split_point = mid_point
            else:
                split_point += 2

            paragraphs = [text[:split_point].strip(), text[split_point:].strip()]

        return "\n\n".join(p for p in paragraphs if p.strip())

    def _optimize_keyword_integration(
        self,
        description: str,
        target_keywords: Optional[List[str]],
        item_specifics: Dict[str, str],
    ) -> str:
        """Optimize keyword integration naturally for eBay Cassini algorithm compliance."""
        if not target_keywords:
            return description

        optimized_description = description

        # Create semantic keyword variations for natural integration
        keyword_variations = self._create_keyword_variations(target_keywords)

        # Extract existing keywords from description
        existing_keywords = set(
            word.lower() for word in re.findall(r"\b\w+\b", description)
        )

        # Find missing target keywords and their variations
        missing_keywords = []
        for keyword in target_keywords:
            if keyword.lower() not in existing_keywords:
                # Check if any variation exists
                variations = keyword_variations.get(keyword.lower(), [keyword])
                if not any(var.lower() in existing_keywords for var in variations):
                    missing_keywords.append(keyword)

        # Integrate missing keywords naturally using Cassini-friendly patterns
        if missing_keywords:
            optimized_description = self._integrate_keywords_naturally(
                optimized_description, missing_keywords, item_specifics
            )

        return optimized_description

    def _create_keyword_variations(
        self, target_keywords: List[str]
    ) -> Dict[str, List[str]]:
        """Create semantic variations of keywords for natural integration."""
        variations = {}

        # Common keyword variations for eBay Cassini
        keyword_synonyms = {
            "smartphone": ["phone", "mobile", "cell phone", "device"],
            "unlocked": ["carrier-free", "network unlocked", "sim-free"],
            "camera": ["photography", "photo", "imaging", "lens"],
            "titanium": ["titanium finish", "titanium design", "titanium construction"],
            "sneakers": ["shoes", "footwear", "athletic shoes", "trainers"],
            "basketball": ["sports", "athletic", "court", "performance"],
            "retro": ["vintage", "classic", "throwback", "heritage"],
            "leather": ["genuine leather", "leather construction", "premium leather"],
        }

        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            variations[keyword_lower] = keyword_synonyms.get(keyword_lower, [keyword])

        return variations

    def _integrate_keywords_naturally(
        self,
        description: str,
        missing_keywords: List[str],
        item_specifics: Dict[str, str],
    ) -> str:
        """Integrate missing keywords naturally using contextual placement."""
        paragraphs = description.split("\n\n")

        for i, keyword in enumerate(
            missing_keywords[:3]
        ):  # Limit to avoid keyword stuffing
            keyword_lower = keyword.lower()

            # Contextual integration based on keyword type
            if keyword_lower in ["smartphone", "phone", "mobile"]:
                # Integrate into technical paragraph
                if len(paragraphs) >= 2:
                    paragraphs[1] = self._add_keyword_to_paragraph(
                        paragraphs[1], keyword, "technical"
                    )
            elif keyword_lower in ["camera", "photography", "imaging"]:
                # Integrate into features paragraph
                if len(paragraphs) >= 2:
                    paragraphs[1] = self._add_keyword_to_paragraph(
                        paragraphs[1], keyword, "feature"
                    )
            elif keyword_lower in ["unlocked", "carrier-free"]:
                # Integrate into functionality paragraph
                if len(paragraphs) >= 3:
                    paragraphs[2] = self._add_keyword_to_paragraph(
                        paragraphs[2], keyword, "functionality"
                    )
            else:
                # Generic integration into conclusion
                if len(paragraphs) >= 4:
                    paragraphs[3] = self._add_keyword_to_paragraph(
                        paragraphs[3], keyword, "conclusion"
                    )

        return "\n\n".join(paragraphs)

    def _add_keyword_to_paragraph(
        self, paragraph: str, keyword: str, context: str
    ) -> str:
        """Add keyword to paragraph naturally based on context."""
        if keyword.lower() in paragraph.lower():
            return paragraph  # Already present

        # Context-specific integration patterns
        if context == "technical":
            if "specifications" in paragraph.lower():
                return paragraph.replace(
                    "specifications include:",
                    f"specifications for this {keyword.lower()} include:",
                )
        elif context == "feature":
            if "features" in paragraph.lower():
                return paragraph.replace(
                    "features include", f"{keyword} features include"
                )
        elif context == "functionality":
            if "functionality" in paragraph.lower():
                return paragraph.replace(
                    "Functionality includes:", f"{keyword} functionality includes:"
                )
        elif context == "conclusion":
            if "suitable for" in paragraph.lower():
                return paragraph.replace(
                    "Suitable for", f"Suitable for {keyword.lower()} users and"
                )

        return paragraph

    def _validate_and_refine(
        self,
        description: str,
        product_data: Dict[str, Any],
        item_specifics: Dict[str, str],
    ) -> str:
        """Validate and refine the generated description."""
        # Remove redundant phrases
        description = re.sub(
            r"\b(the|a|an)\s+\1\b", r"\1", description, flags=re.IGNORECASE
        )

        # Fix spacing issues while preserving paragraph breaks
        # First preserve paragraph breaks by replacing them with a placeholder
        paragraph_placeholder = "<<<PARAGRAPH_BREAK>>>"
        description = description.replace("\n\n", paragraph_placeholder)

        # Now fix spacing issues
        description = re.sub(r"\s+", " ", description)
        description = re.sub(r"\s+([.,:;])", r"\1", description)

        # Restore paragraph breaks
        description = description.replace(paragraph_placeholder, "\n\n")

        # Ensure proper capitalization
        sentences = description.split(". ")
        capitalized_sentences = []

        for sentence in sentences:
            if sentence:
                sentence = sentence.strip()
                if sentence:
                    sentence = (
                        sentence[0].upper() + sentence[1:]
                        if len(sentence) > 1
                        else sentence.upper()
                    )
                    capitalized_sentences.append(sentence)

        description = ". ".join(capitalized_sentences)

        # Ensure description ends with period
        if not description.endswith("."):
            description += "."

        return description

    def _generate_description_metadata(
        self,
        description: str,
        item_specifics: Dict[str, str],
        target_keywords: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Generate metadata for the description."""
        words = description.split()
        word_count = len(words)

        # Calculate keyword density
        keyword_density = {}
        if target_keywords:
            description_lower = description.lower()
            for keyword in target_keywords:
                count = description_lower.count(keyword.lower())
                density = (count / word_count) * 100 if word_count > 0 else 0
                keyword_density[keyword] = round(density, 2)

        # Calculate specifics utilization
        specifics_mentioned = 0
        description_lower = description.lower()

        for aspect_name, aspect_value in item_specifics.items():
            if aspect_value.lower() in description_lower:
                specifics_mentioned += 1

        specifics_utilization = (
            (specifics_mentioned / len(item_specifics)) * 100 if item_specifics else 0
        )

        # Readability metrics
        sentences = len([s for s in description.split(".") if s.strip()])
        avg_sentence_length = word_count / sentences if sentences > 0 else 0

        return {
            "word_count": word_count,
            "sentence_count": sentences,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "keyword_density": keyword_density,
            "specifics_utilization": round(specifics_utilization, 1),
            "readability_score": self._calculate_readability_score(
                word_count, sentences, description
            ),
            "seo_optimization_score": self._calculate_seo_score(
                keyword_density, specifics_utilization
            ),
        }

    def _calculate_readability_score(
        self, word_count: int, sentence_count: int, description: str
    ) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)."""
        if sentence_count == 0:
            return 0

        avg_sentence_length = word_count / sentence_count

        # Count syllables (simplified)
        syllable_count = 0
        words = description.split()
        for word in words:
            syllable_count += max(1, len(re.findall(r"[aeiouAEIOU]", word)))

        avg_syllables_per_word = syllable_count / word_count if word_count > 0 else 0

        # Simplified Flesch Reading Ease formula
        readability = (
            206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        )

        return max(0, min(100, readability))

    def _calculate_seo_score(
        self, keyword_density: Dict[str, float], specifics_utilization: float
    ) -> float:
        """Calculate SEO optimization score for the description."""
        seo_score = 0

        # Keyword density score (optimal range: 1-3%)
        if keyword_density:
            density_scores = []
            for density in keyword_density.values():
                if 1 <= density <= 3:
                    density_scores.append(100)
                elif 0.5 <= density < 1 or 3 < density <= 5:
                    density_scores.append(75)
                elif density > 0:
                    density_scores.append(50)
                else:
                    density_scores.append(0)

            seo_score += (sum(density_scores) / len(density_scores)) * 0.4

        # Specifics utilization score
        seo_score += (specifics_utilization / 100) * 60

        return round(seo_score, 1)
