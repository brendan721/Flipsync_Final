from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.service.asin_finder.models import ASINData
from fs_agt_clean.services.llm.ollama_service import OllamaLLMService
from fs_agt_clean.services.metrics.service import MetricsService


class ContentStyle(BaseModel):
    tone: str = "professional"
    formality_level: int = 3
    language_complexity: int = 3
    storytelling_mode: str = "feature_focused"
    emotional_appeal: str = "moderate"


class ContentTemplate(BaseModel):
    template_id: str
    name: str
    structure: List[str]
    style_guide: ContentStyle
    keywords: List[str]
    success_rate: float = 0.0
    usage_count: int = 0
    last_updated: datetime = datetime.utcnow()


class StorytellingEngine:
    """Engine for generating compelling product descriptions and stories."""

    def __init__(
        self,
        config_manager: ConfigManager,
        metrics_service: Optional[MetricsService] = None,
        max_retries: int = 3,
    ):
        """Initialize storytelling engine.

        Args:
            config_manager: Configuration manager instance
            metrics_service: Optional metrics service
            max_retries: Maximum number of retries for API calls
        """
        self.config = config_manager
        self.metrics = metrics_service
        self.max_retries = max_retries
        self.llm_service = OllamaLLMService(config_manager)
        self.templates = {
            "premium": ContentTemplate(
                template_id="premium",
                name="Premium Product Narrative",
                structure=[
                    "attention_grabbing_hook",
                    "unique_value_proposition",
                    "feature_benefits",
                    "social_proof",
                    "scarcity_urgency",
                    "call_to_action",
                ],
                style_guide=ContentStyle(
                    tone="professional",
                    formality_level=4,
                    language_complexity=3,
                    storytelling_mode="feature_focused",
                    emotional_appeal="moderate",
                ),
                keywords=["premium", "quality", "exclusive", "luxury"],
            ),
            "value": ContentTemplate(
                template_id="value",
                name="Value-Focused Narrative",
                structure=[
                    "price_value_hook",
                    "cost_benefit_analysis",
                    "practical_features",
                    "comparison_points",
                    "satisfaction_guarantee",
                    "action_prompt",
                ],
                style_guide=ContentStyle(
                    tone="casual",
                    formality_level=2,
                    language_complexity=2,
                    storytelling_mode="benefit_driven",
                    emotional_appeal="moderate",
                ),
                keywords=["value", "affordable", "practical", "efficient"],
            ),
            "innovative": ContentTemplate(
                template_id="innovative",
                name="Innovation Spotlight",
                structure=[
                    "innovation_hook",
                    "technology_showcase",
                    "unique_features",
                    "future_benefits",
                    "early_adopter_appeal",
                    "innovation_cta",
                ],
                style_guide=ContentStyle(
                    tone="enthusiastic",
                    formality_level=3,
                    language_complexity=4,
                    storytelling_mode="story_based",
                    emotional_appeal="strong",
                ),
                keywords=["innovative", "cutting-edge", "advanced", "smart"],
            ),
        }

    async def generate_content(
        self,
        asin_data: ASINData,
        template_id: str = None,
        custom_style: Optional[ContentStyle] = None,
    ) -> Dict[str, str]:
        """
        Generate dynamic content for a product listing.
        """
        try:
            template = self._select_template(asin_data, template_id)
            style = custom_style or template.style_guide
            self.metrics.track_content_generation(template.template_id)
            content = {}
            for section in template.structure:
                content[section] = await self._generate_section(
                    section, asin_data, template, style
                )
            self._update_template_metrics(template.template_id, success=True)
            return content
        except Exception as e:
            if self.metrics:
                self.metrics.track_error("content_generation_error", str(e))
            self._update_template_metrics(template_id or "default", success=False)
            raise

    async def _generate_section(
        self,
        section: str,
        asin_data: ASINData,
        template: ContentTemplate,
        style: ContentStyle,
    ) -> str:
        """
        Generate content for a specific section using OpenAI.
        """
        prompt = self._create_section_prompt(section, asin_data, template, style)
        for attempt in range(self.max_retries):
            try:
                response = await self.llm_service.chat.completions.create(
                    model=self.config.get("llm.model", "llama2"),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.7,
                )
                return response.choices[0].message.content.strip()
            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                continue

    def _create_section_prompt(
        self,
        section: str,
        asin_data: ASINData,
        template: ContentTemplate,
        style: ContentStyle,
    ) -> str:
        """
        Create a specific prompt for each section.
        """
        base_prompt = f"Create a {style.tone} {section} for {asin_data.product_name}. "
        section_prompts = {
            "attention_grabbing_hook": f"{base_prompt}Focus on unique selling points and emotional appeal. Use {style.emotional_appeal} emotional language.",
            "unique_value_proposition": f"{base_prompt}Highlight what makes this product special. Focus on key differentiators and main benefits.",
            "feature_benefits": f"{base_prompt}Transform features into benefits. Show how each feature improves the user's life.",
            "social_proof": f"{base_prompt}Include trust-building elements. Focus on reliability and customer satisfaction.",
            "scarcity_urgency": f"{base_prompt}Create a sense of urgency without being pushy. Focus on value and timeliness.",
            "call_to_action": f"{base_prompt}Create a compelling but natural call to action. Focus on value and confidence.",
        }
        return section_prompts.get(
            section, f"{base_prompt}Create engaging and informative content."
        )

    def _get_system_prompt(self, style: ContentStyle) -> str:
        """
        Create system prompt based on style settings.
        """
        return f"You are an expert e-commerce copywriter specializing in {style.storytelling_mode} content. Write in a {style.tone} tone with formality level {style.formality_level}/5 and complexity level {style.language_complexity}/5. Use {style.emotional_appeal} emotional appeal."

    def _select_template(
        self, asin_data: ASINData, template_id: Optional[str]
    ) -> ContentTemplate:
        """
        Select the best template based on product data or specified template.
        """
        if template_id and template_id in self.templates:
            return self.templates[template_id]
        if asin_data.price >= 100:
            return self.templates["premium"]
        elif "innovative" in asin_data.product_name.lower():
            return self.templates["innovative"]
        else:
            return self.templates["value"]

    def _update_template_metrics(self, template_id: str, success: bool):
        """
        Update template usage metrics.
        """
        if template_id in self.templates:
            template = self.templates[template_id]
            template.usage_count += 1
            current_success_count = template.success_rate * (template.usage_count - 1)
            new_success_count = current_success_count + (1 if success else 0)
            template.success_rate = new_success_count / template.usage_count
            template.last_updated = datetime.utcnow()

    async def create_template(self, template: ContentTemplate) -> bool:
        """
        Add a new content template.
        """
        if template.template_id in self.templates:
            return False
        self.templates[template.template_id] = template
        return True

    async def update_template(self, template: ContentTemplate) -> bool:
        """
        Update an existing template.
        """
        if template.template_id not in self.templates:
            return False
        self.templates[template.template_id] = template
        return True

    async def get_template_metrics(self) -> Dict[str, Dict]:
        """
        Get performance metrics for all templates.
        """
        return {
            template_id: {
                "success_rate": template.success_rate,
                "usage_count": template.usage_count,
                "last_updated": template.last_updated,
            }
            for template_id, template in self.templates.items()
        }

    async def generate_story(
        self,
        product_data: Dict,
        style: str = "engaging",
        max_length: int = 1000,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """Generate a compelling product story.

        Args:
            product_data: Product information
            style: Desired writing style
            max_length: Maximum length in characters
            keywords: Optional keywords to include

        Returns:
            Generated product story
        """
        prompt = self._build_story_prompt(product_data, style, max_length, keywords)
        try:
            response = await self.llm_service.chat.completions.create(
                model=self.config.get("llm.model", "llama2"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_length,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            if self.metrics:
                self.metrics.track_error("story_generation", str(e))
            raise

    def _build_story_prompt(
        self,
        product_data: Dict,
        style: str,
        max_length: int,
        keywords: Optional[List[str]] = None,
    ) -> str:
        """Build prompt for story generation.

        Args:
            product_data: Product information
            style: Desired writing style
            max_length: Maximum length
            keywords: Optional keywords

        Returns:
            Formatted prompt string
        """
        prompt = f"""Create a {style} product description for:

Title: {product_data.get('title', '')}
Features: {', '.join(product_data.get('features', []))}
Category: {product_data.get('category', '')}

Style guidelines:
- Be {style} and persuasive
- Maximum length: {max_length} characters
- Focus on benefits and value proposition
"""

        if keywords:
            prompt += f"\nInclude these keywords naturally: {', '.join(keywords)}"

        return prompt
