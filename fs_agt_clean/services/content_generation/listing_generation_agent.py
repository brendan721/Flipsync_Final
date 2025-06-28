"""Listing generation agent."""

import logging
from typing import Dict, List, Optional

from fs_agt_clean.agents.data import AIService
from fs_agt_clean.core.monitoring.alerts.collectors import MetricCollector

logger = logging.getLogger(__name__)


class ListingGenerationUnifiedAgent:
    """UnifiedAgent for generating product listings."""

    def __init__(
        self,
        ai_service: AIService,
        metric_collector: Optional[MetricCollector] = None,
    ):
        self.ai_service = ai_service
        self.metric_collector = metric_collector

    async def generate_listing(
        self,
        product_data: Dict[str, str],
        target_marketplace: str,
        style_guide: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Generate a product listing."""
        try:
            # Collect metrics if available
            if self.metric_collector:
                await self.metric_collector.record_start("listing_generation")

            # Generate title
            title = await self._generate_title(product_data)

            # Generate description
            description = await self._generate_description(product_data, style_guide)

            # Generate keywords
            keywords = await self._generate_keywords(product_data)

            listing = {
                "title": title,
                "description": description,
                "keywords": keywords,
            }

            # Record success metric
            if self.metric_collector:
                await self.metric_collector.record_success("listing_generation")

            return listing

        except Exception as e:
            # Record failure metric
            if self.metric_collector:
                await self.metric_collector.record_failure("listing_generation")
            logger.error("Failed to generate listing: %s", str(e))
            raise

    async def _generate_title(self, product_data: Dict[str, str]) -> str:
        """Generate a product title."""
        prompt = self._create_title_prompt(product_data)
        title = await self.ai_service.generate_text(prompt, max_tokens=100)
        return title.strip()

    async def _generate_description(
        self,
        product_data: Dict[str, str],
        style_guide: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate a product description."""
        prompt = self._create_description_prompt(product_data, style_guide)
        description = await self.ai_service.generate_text(prompt, max_tokens=500)
        return description.strip()

    async def _generate_keywords(self, product_data: Dict[str, str]) -> List[str]:
        """Generate keywords for the product."""
        combined_text = (
            f"{product_data.get('title', '')} {product_data.get('description', '')}"
        )
        keywords = await self.ai_service.extract_keywords(
            combined_text, max_keywords=10
        )
        return keywords

    def _create_title_prompt(self, product_data: Dict[str, str]) -> str:
        """Create a prompt for generating a product title."""
        return (
            f"Generate a clear and compelling product title for the following product:\n"
            f"Brand: {product_data.get('brand', 'Unknown')}\n"
            f"Category: {product_data.get('category', 'Unknown')}\n"
            f"Features: {product_data.get('features', 'None')}\n"
        )

    def _create_description_prompt(
        self,
        product_data: Dict[str, str],
        style_guide: Optional[Dict[str, str]] = None,
    ) -> str:
        """Create a prompt for generating a product description."""
        style_instructions = ""
        if style_guide:
            style_instructions = (
                f"\nStyle requirements:\n"
                f"Tone: {style_guide.get('tone', 'Professional')}\n"
                f"Length: {style_guide.get('length', 'Medium')}\n"
                f"Format: {style_guide.get('format', 'Paragraphs with bullet points')}\n"
            )

        return (
            f"Generate a detailed product description for the following product:\n"
            f"Title: {product_data.get('title', 'Unknown')}\n"
            f"Brand: {product_data.get('brand', 'Unknown')}\n"
            f"Category: {product_data.get('category', 'Unknown')}\n"
            f"Features: {product_data.get('features', 'None')}\n"
            f"{style_instructions}"
        )
