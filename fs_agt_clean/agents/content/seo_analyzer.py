"""SEO analysis and optimization agent for marketplace content."""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fs_agt_clean.agents.content.base_content_agent import BaseContentUnifiedAgent
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer

logger = logging.getLogger(__name__)


class SEOAnalyzer(BaseContentUnifiedAgent):
    """
    UnifiedAgent for SEO analysis and optimization of marketplace content.

    Capabilities:
    - Keyword density analysis
    - Content structure analysis
    - Marketplace-specific SEO scoring
    - Competitor keyword analysis
    - Search ranking optimization
    - Content gap analysis
    """

    def __init__(
        self,
        marketplace: str = "ebay",
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the SEO analyzer agent.

        Args:
            marketplace: Target marketplace for SEO optimization
            config_manager: Configuration manager
            alert_manager: Alert manager for monitoring
            battery_optimizer: Battery optimizer for mobile efficiency
            config: Optional configuration overrides
        """
        agent_id = f"seo_analyzer_{marketplace}_{uuid4()}"
        super().__init__(
            agent_id=agent_id,
            content_type="seo_analysis",
            config_manager=config_manager,
            alert_manager=alert_manager,
            battery_optimizer=battery_optimizer,
            config=config,
        )

        self.marketplace = marketplace
        self.keyword_database = {}
        self.competitor_data = {}

        # SEO scoring weights for different factors
        self.seo_weights = {
            "keyword_density": 0.25,
            "title_optimization": 0.20,
            "content_structure": 0.15,
            "meta_description": 0.15,
            "content_length": 0.10,
            "readability": 0.10,
            "keyword_placement": 0.05,
        }

        # Marketplace-specific SEO rules
        self.marketplace_seo_rules = {
            "ebay": {
                "title_keyword_positions": [
                    0,
                    1,
                    2,
                ],  # First 3 words are most important
                "optimal_title_length": (60, 80),
                "optimal_description_length": (200, 500),
                "keyword_density_range": (0.01, 0.03),
                "important_sections": [
                    "title",
                    "subtitle",
                    "description",
                    "item_specifics",
                ],
            },
            "amazon": {
                "title_keyword_positions": [0, 1],  # First 2 words are most important
                "optimal_title_length": (150, 200),
                "optimal_description_length": (300, 600),
                "keyword_density_range": (0.005, 0.02),
                "important_sections": [
                    "title",
                    "bullet_points",
                    "description",
                    "backend_keywords",
                ],
            },
        }

    def _get_required_config_fields(self) -> List[str]:
        """Get required configuration fields."""
        fields = super()._get_required_config_fields()
        fields.extend(
            [
                "keyword_research_service",
                "competitor_analysis_enabled",
                "search_volume_api",
                "ranking_tracker_enabled",
            ]
        )
        return fields

    async def _setup_content_resources(self) -> None:
        """Set up SEO analysis resources."""
        await self._load_keyword_database()
        await self._initialize_seo_tools()
        logger.info(f"SEO analysis resources initialized for {self.marketplace}")

    async def _cleanup_content_resources(self) -> None:
        """Clean up SEO analysis resources."""
        self.keyword_database.clear()
        self.competitor_data.clear()

    async def _load_keyword_database(self) -> None:
        """Load keyword database for SEO analysis."""
        # Simulate loading keyword data
        self.keyword_database = {
            "electronics": {
                "primary": ["smartphone", "laptop", "tablet", "headphones", "camera"],
                "secondary": ["wireless", "bluetooth", "HD", "portable", "premium"],
                "long_tail": [
                    "best smartphone 2024",
                    "wireless bluetooth headphones",
                    "4K camera",
                ],
            },
            "clothing": {
                "primary": ["shirt", "dress", "jeans", "jacket", "shoes"],
                "secondary": ["cotton", "comfortable", "stylish", "trendy", "casual"],
                "long_tail": [
                    "comfortable cotton shirt",
                    "stylish casual dress",
                    "trendy denim jeans",
                ],
            },
            "home": {
                "primary": ["furniture", "decor", "kitchen", "bedroom", "living room"],
                "secondary": ["modern", "wooden", "metal", "glass", "comfortable"],
                "long_tail": [
                    "modern wooden furniture",
                    "kitchen decor items",
                    "bedroom furniture set",
                ],
            },
        }

    async def _initialize_seo_tools(self) -> None:
        """Initialize SEO analysis tools."""
        self.seo_tools = {
            "keyword_analyzer": self._analyze_keyword_usage,
            "content_structure_analyzer": self._analyze_content_structure,
            "readability_analyzer": self._analyze_readability,
            "competitor_analyzer": self._analyze_competitor_content,
            "ranking_predictor": self._predict_search_ranking,
        }

    async def _handle_generation_event(self, event: Dict[str, Any]) -> None:
        """Handle SEO analysis generation events."""
        try:
            content = event.get("content", {})
            keywords = event.get("target_keywords", [])
            analysis_type = event.get("analysis_type", "comprehensive")

            if analysis_type == "keyword_analysis":
                result = await self.analyze_keyword_optimization(content, keywords)
            elif analysis_type == "competitor_analysis":
                result = await self.analyze_competitor_seo(content, keywords)
            elif analysis_type == "ranking_prediction":
                result = await self.predict_search_performance(content, keywords)
            else:
                result = await self.comprehensive_seo_analysis(content, keywords)

            self.metrics["content_generated"] += 1
            logger.info(f"Completed {analysis_type} SEO analysis")

        except Exception as e:
            logger.error(f"Error handling SEO analysis event: {e}")

    async def _handle_optimization_event(self, event: Dict[str, Any]) -> None:
        """Handle SEO optimization events."""
        try:
            content = event.get("content", {})
            target_keywords = event.get("target_keywords", [])
            optimization_goals = event.get("goals", ["ranking", "visibility"])

            result = await self.optimize_content_for_seo(
                content, target_keywords, optimization_goals
            )
            self.metrics["content_optimized"] += 1
            logger.info(f"Optimized content for SEO goals: {optimization_goals}")

        except Exception as e:
            logger.error(f"Error handling SEO optimization event: {e}")

    async def _generate_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SEO analysis."""
        try:
            content = task.get("content", {})
            keywords = task.get("keywords", [])
            analysis_type = task.get("analysis_type", "comprehensive")

            start_time = datetime.now(timezone.utc)

            if analysis_type == "keyword":
                result = await self.analyze_keyword_optimization(content, keywords)
            elif analysis_type == "competitor":
                result = await self.analyze_competitor_seo(content, keywords)
            elif analysis_type == "structure":
                result = await self.analyze_content_structure(content)
            else:
                result = await self.comprehensive_seo_analysis(content, keywords)

            end_time = datetime.now(timezone.utc)
            self.metrics["generation_latency"] = (end_time - start_time).total_seconds()

            return {
                "analysis": result,
                "success": True,
                "analysis_time": self.metrics["generation_latency"],
            }

        except Exception as e:
            logger.error(f"Error generating SEO analysis: {e}")
            return {"error": str(e), "success": False}

    async def _optimize_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content for SEO."""
        try:
            content = task.get("content", {})
            keywords = task.get("keywords", [])
            goals = task.get("optimization_goals", ["ranking"])

            start_time = datetime.now(timezone.utc)
            optimized_content = await self.optimize_content_for_seo(
                content, keywords, goals
            )
            end_time = datetime.now(timezone.utc)

            self.metrics["optimization_latency"] = (
                end_time - start_time
            ).total_seconds()

            return {
                "original_content": content,
                "optimized_content": optimized_content,
                "target_keywords": keywords,
                "optimization_goals": goals,
                "success": True,
                "optimization_time": self.metrics["optimization_latency"],
            }

        except Exception as e:
            logger.error(f"Error optimizing content for SEO: {e}")
            return {"error": str(e), "success": False}

    async def comprehensive_seo_analysis(
        self, content: Dict[str, Any], keywords: List[str]
    ) -> Dict[str, Any]:
        """Perform comprehensive SEO analysis."""
        try:
            analysis_results = {}

            # Keyword analysis
            analysis_results["keyword_analysis"] = (
                await self.analyze_keyword_optimization(content, keywords)
            )

            # Content structure analysis
            analysis_results["structure_analysis"] = (
                await self.analyze_content_structure(content)
            )

            # Readability analysis
            analysis_results["readability_analysis"] = await self._analyze_readability(
                content
            )

            # Marketplace-specific analysis
            analysis_results["marketplace_analysis"] = (
                await self._analyze_marketplace_compliance(content)
            )

            # Overall SEO score calculation
            overall_score = self._calculate_overall_seo_score(analysis_results)

            # Generate recommendations
            recommendations = self._generate_seo_recommendations(analysis_results)

            return {
                "overall_seo_score": overall_score,
                "detailed_analysis": analysis_results,
                "recommendations": recommendations,
                "target_keywords": keywords,
                "marketplace": self.marketplace,
                "analyzed_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error in comprehensive SEO analysis: {e}")
            return {"error": str(e)}

    async def analyze_keyword_optimization(
        self, content: Dict[str, Any], keywords: List[str]
    ) -> Dict[str, Any]:
        """Analyze keyword optimization in content."""
        try:
            if not keywords:
                return {"error": "No keywords provided for analysis"}

            # Combine all text content
            all_text = self._extract_all_text(content)

            keyword_analysis = {}

            for keyword in keywords:
                analysis = await self._analyze_single_keyword(
                    all_text, keyword, content
                )
                keyword_analysis[keyword] = analysis

            # Calculate overall keyword optimization score
            keyword_scores = [
                analysis["optimization_score"] for analysis in keyword_analysis.values()
            ]
            overall_keyword_score = (
                sum(keyword_scores) / len(keyword_scores) if keyword_scores else 0
            )

            return {
                "overall_keyword_score": overall_keyword_score,
                "keyword_details": keyword_analysis,
                "keyword_density_overall": self._calculate_overall_keyword_density(
                    all_text, keywords
                ),
                "recommendations": self._generate_keyword_recommendations(
                    keyword_analysis
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing keyword optimization: {e}")
            return {"error": str(e)}

    async def analyze_content_structure(
        self, content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze content structure for SEO."""
        try:
            structure_analysis = {
                "title_analysis": self._analyze_title_structure(
                    content.get("title", "")
                ),
                "description_analysis": self._analyze_description_structure(
                    content.get("description", "")
                ),
                "bullet_points_analysis": self._analyze_bullet_points(
                    content.get("bullet_points", [])
                ),
                "content_hierarchy": self._analyze_content_hierarchy(content),
                "meta_elements": self._analyze_meta_elements(content),
            }

            # Calculate structure score
            structure_score = self._calculate_structure_score(structure_analysis)

            return {
                "structure_score": structure_score,
                "structure_details": structure_analysis,
                "recommendations": self._generate_structure_recommendations(
                    structure_analysis
                ),
            }

        except Exception as e:
            logger.error(f"Error analyzing content structure: {e}")
            return {"error": str(e)}

    async def optimize_content_for_seo(
        self, content: Dict[str, Any], keywords: List[str], goals: List[str]
    ) -> Dict[str, Any]:
        """Optimize content for SEO goals."""
        try:
            optimized_content = content.copy()
            optimizations_applied = []

            if "ranking" in goals:
                optimized_content, ranking_opts = await self._optimize_for_ranking(
                    optimized_content, keywords
                )
                optimizations_applied.extend(ranking_opts)

            if "visibility" in goals:
                optimized_content, visibility_opts = (
                    await self._optimize_for_visibility(optimized_content, keywords)
                )
                optimizations_applied.extend(visibility_opts)

            if "conversion" in goals:
                optimized_content, conversion_opts = (
                    await self._optimize_for_conversion(optimized_content)
                )
                optimizations_applied.extend(conversion_opts)

            # Calculate improvement scores
            original_score = await self._calculate_content_seo_score(content, keywords)
            optimized_score = await self._calculate_content_seo_score(
                optimized_content, keywords
            )

            return {
                "optimized_content": optimized_content,
                "optimizations_applied": optimizations_applied,
                "seo_score_before": original_score,
                "seo_score_after": optimized_score,
                "improvement_percentage": (
                    ((optimized_score - original_score) / original_score * 100)
                    if original_score > 0
                    else 0
                ),
                "optimization_goals": goals,
            }

        except Exception as e:
            logger.error(f"Error optimizing content for SEO: {e}")
            return {"error": str(e)}

    # Helper methods for SEO analysis
    def _extract_all_text(self, content: Dict[str, Any]) -> str:
        """Extract all text content for analysis."""
        text_parts = []

        if "title" in content:
            text_parts.append(content["title"])
        if "description" in content:
            text_parts.append(content["description"])
        if "bullet_points" in content:
            text_parts.extend(content["bullet_points"])
        if "meta_description" in content:
            text_parts.append(content["meta_description"])

        return " ".join(text_parts).lower()

    async def _analyze_single_keyword(
        self, text: str, keyword: str, content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze a single keyword in the content."""
        keyword_lower = keyword.lower()

        # Count occurrences
        total_words = len(text.split())
        keyword_count = text.count(keyword_lower)
        keyword_density = keyword_count / total_words if total_words > 0 else 0

        # Check keyword placement
        title_has_keyword = keyword_lower in content.get("title", "").lower()
        description_has_keyword = (
            keyword_lower in content.get("description", "").lower()
        )

        # Calculate optimization score
        optimization_score = 0
        if title_has_keyword:
            optimization_score += 40
        if description_has_keyword:
            optimization_score += 30
        if 0.01 <= keyword_density <= 0.03:  # Optimal density range
            optimization_score += 30
        elif keyword_density > 0:
            optimization_score += 15

        return {
            "keyword": keyword,
            "count": keyword_count,
            "density": keyword_density,
            "in_title": title_has_keyword,
            "in_description": description_has_keyword,
            "optimization_score": optimization_score,
            "recommendations": self._generate_keyword_specific_recommendations(
                keyword,
                keyword_count,
                keyword_density,
                title_has_keyword,
                description_has_keyword,
            ),
        }

    def _calculate_overall_keyword_density(
        self, text: str, keywords: List[str]
    ) -> float:
        """Calculate overall keyword density."""
        total_words = len(text.split())
        total_keyword_occurrences = sum(
            text.count(keyword.lower()) for keyword in keywords
        )
        return total_keyword_occurrences / total_words if total_words > 0 else 0

    def _analyze_title_structure(self, title: str) -> Dict[str, Any]:
        """Analyze title structure for SEO."""
        rules = self.marketplace_seo_rules.get(
            self.marketplace, self.marketplace_seo_rules["ebay"]
        )

        title_length = len(title)
        optimal_length = rules["optimal_title_length"]

        analysis = {
            "length": title_length,
            "optimal_length_range": optimal_length,
            "length_score": (
                100 if optimal_length[0] <= title_length <= optimal_length[1] else 50
            ),
            "word_count": len(title.split()),
            "has_brand": self._detect_brand_in_title(title),
            "has_model": self._detect_model_in_title(title),
            "capitalization_score": self._analyze_title_capitalization(title),
        }

        return analysis

    def _analyze_description_structure(self, description: str) -> Dict[str, Any]:
        """Analyze description structure for SEO."""
        rules = self.marketplace_seo_rules.get(
            self.marketplace, self.marketplace_seo_rules["ebay"]
        )

        desc_length = len(description)
        optimal_length = rules["optimal_description_length"]

        analysis = {
            "length": desc_length,
            "optimal_length_range": optimal_length,
            "length_score": (
                100 if optimal_length[0] <= desc_length <= optimal_length[1] else 50
            ),
            "paragraph_count": len([p for p in description.split("\n\n") if p.strip()]),
            "sentence_count": len([s for s in description.split(".") if s.strip()]),
            "has_call_to_action": self._detect_call_to_action(description),
            "readability_score": self._calculate_readability_score(description),
        }

        return analysis

    def _analyze_bullet_points(self, bullet_points: List[str]) -> Dict[str, Any]:
        """Analyze bullet points for SEO."""
        if not bullet_points:
            return {
                "count": 0,
                "score": 0,
                "recommendations": ["Add bullet points for better structure"],
            }

        analysis = {
            "count": len(bullet_points),
            "average_length": sum(len(bp) for bp in bullet_points) / len(bullet_points),
            "keyword_coverage": self._analyze_bullet_point_keywords(bullet_points),
            "structure_score": self._score_bullet_point_structure(bullet_points),
        }

        return analysis

    def _analyze_content_hierarchy(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content hierarchy for SEO."""
        hierarchy_score = 0

        if "title" in content and content["title"]:
            hierarchy_score += 30
        if "description" in content and content["description"]:
            hierarchy_score += 25
        if "bullet_points" in content and content["bullet_points"]:
            hierarchy_score += 20
        if "meta_description" in content and content["meta_description"]:
            hierarchy_score += 25

        return {
            "hierarchy_score": hierarchy_score,
            "has_title": "title" in content and bool(content["title"]),
            "has_description": "description" in content
            and bool(content["description"]),
            "has_bullet_points": "bullet_points" in content
            and bool(content["bullet_points"]),
            "has_meta_description": "meta_description" in content
            and bool(content["meta_description"]),
        }

    def _analyze_meta_elements(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze meta elements for SEO."""
        meta_analysis = {
            "meta_description_present": "meta_description" in content,
            "meta_keywords_present": "meta_keywords" in content,
            "og_tags_present": any(key.startswith("og_") for key in content.keys()),
        }

        if "meta_description" in content:
            meta_desc = content["meta_description"]
            meta_analysis["meta_description_length"] = len(meta_desc)
            meta_analysis["meta_description_optimal"] = 150 <= len(meta_desc) <= 160

        return meta_analysis

    # Additional helper methods
    def _detect_brand_in_title(self, title: str) -> bool:
        """Detect if title contains a brand name."""
        # Simplified brand detection
        common_brands = ["apple", "samsung", "sony", "nike", "adidas", "microsoft"]
        return any(brand in title.lower() for brand in common_brands)

    def _detect_model_in_title(self, title: str) -> bool:
        """Detect if title contains a model identifier."""
        # Look for model patterns (numbers, alphanumeric codes)
        import re

        model_patterns = [r"\b\d+\b", r"\b[A-Z]\d+\b", r"\b\d+[A-Z]\b"]
        return any(re.search(pattern, title) for pattern in model_patterns)

    def _analyze_title_capitalization(self, title: str) -> int:
        """Analyze title capitalization for SEO."""
        words = title.split()
        if not words:
            return 0

        capitalized_words = sum(1 for word in words if word[0].isupper())
        return int((capitalized_words / len(words)) * 100)

    def _detect_call_to_action(self, description: str) -> bool:
        """Detect call-to-action phrases in description."""
        cta_phrases = [
            "buy now",
            "order today",
            "shop now",
            "get yours",
            "limited time",
            "act fast",
        ]
        return any(phrase in description.lower() for phrase in cta_phrases)

    def _analyze_bullet_point_keywords(
        self, bullet_points: List[str]
    ) -> Dict[str, Any]:
        """Analyze keyword usage in bullet points."""
        all_text = " ".join(bullet_points).lower()
        word_count = len(all_text.split())

        # Count action words
        action_words = [
            "premium",
            "professional",
            "high-quality",
            "durable",
            "reliable",
        ]
        action_word_count = sum(all_text.count(word) for word in action_words)

        return {
            "total_words": word_count,
            "action_words_count": action_word_count,
            "action_word_density": (
                action_word_count / word_count if word_count > 0 else 0
            ),
        }

    def _score_bullet_point_structure(self, bullet_points: List[str]) -> int:
        """Score bullet point structure."""
        if not bullet_points:
            return 0

        score = 0

        # Check count (3-5 is optimal)
        if 3 <= len(bullet_points) <= 5:
            score += 40
        elif len(bullet_points) > 0:
            score += 20

        # Check length consistency
        lengths = [len(bp) for bp in bullet_points]
        avg_length = sum(lengths) / len(lengths)
        if 20 <= avg_length <= 100:  # Optimal length range
            score += 30

        # Check for variety in starting words
        starting_words = [
            bp.split()[0].lower() if bp.split() else "" for bp in bullet_points
        ]
        unique_starts = len(set(starting_words))
        if unique_starts > len(bullet_points) * 0.7:  # 70% unique starts
            score += 30

        return score

    async def _analyze_readability(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze content readability."""
        all_text = self._extract_all_text(content)

        if not all_text:
            return {"readability_score": 0, "grade_level": "N/A"}

        # Simple readability calculation
        sentences = [s for s in all_text.split(".") if s.strip()]
        words = all_text.split()

        if not sentences or not words:
            return {"readability_score": 0, "grade_level": "N/A"}

        avg_sentence_length = len(words) / len(sentences)

        # Simplified Flesch Reading Ease
        readability_score = 206.835 - (1.015 * avg_sentence_length)
        readability_score = max(0, min(100, readability_score))

        # Determine grade level
        if readability_score >= 90:
            grade_level = "5th grade"
        elif readability_score >= 80:
            grade_level = "6th grade"
        elif readability_score >= 70:
            grade_level = "7th grade"
        elif readability_score >= 60:
            grade_level = "8th-9th grade"
        elif readability_score >= 50:
            grade_level = "10th-12th grade"
        else:
            grade_level = "College level"

        return {
            "readability_score": readability_score,
            "grade_level": grade_level,
            "avg_sentence_length": avg_sentence_length,
            "total_sentences": len(sentences),
            "total_words": len(words),
        }

    async def _analyze_marketplace_compliance(
        self, content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze marketplace-specific compliance."""
        rules = self.marketplace_seo_rules.get(
            self.marketplace, self.marketplace_seo_rules["ebay"]
        )
        compliance_score = 0
        issues = []

        # Check title compliance
        title = content.get("title", "")
        if title:
            title_length = len(title)
            optimal_title = rules["optimal_title_length"]
            if optimal_title[0] <= title_length <= optimal_title[1]:
                compliance_score += 25
            else:
                issues.append(
                    f"Title length ({title_length}) not optimal ({optimal_title[0]}-{optimal_title[1]})"
                )

        # Check description compliance
        description = content.get("description", "")
        if description:
            desc_length = len(description)
            optimal_desc = rules["optimal_description_length"]
            if optimal_desc[0] <= desc_length <= optimal_desc[1]:
                compliance_score += 25
            else:
                issues.append(
                    f"Description length ({desc_length}) not optimal ({optimal_desc[0]}-{optimal_desc[1]})"
                )

        # Check keyword density
        keywords = content.get("keywords", [])
        if keywords:
            all_text = self._extract_all_text(content)
            keyword_density = self._calculate_overall_keyword_density(
                all_text, keywords
            )
            optimal_density = rules["keyword_density_range"]
            if optimal_density[0] <= keyword_density <= optimal_density[1]:
                compliance_score += 25
            else:
                issues.append(
                    f"Keyword density ({keyword_density:.3f}) not optimal ({optimal_density[0]}-{optimal_density[1]})"
                )

        # Check required sections
        required_sections = rules["important_sections"]
        present_sections = [
            section
            for section in required_sections
            if section in content and content[section]
        ]
        if len(present_sections) == len(required_sections):
            compliance_score += 25
        else:
            missing = set(required_sections) - set(present_sections)
            issues.append(f"Missing required sections: {', '.join(missing)}")

        return {
            "compliance_score": compliance_score,
            "marketplace": self.marketplace,
            "issues": issues,
            "required_sections": required_sections,
            "present_sections": present_sections,
        }

    def _calculate_overall_seo_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate overall SEO score from analysis results."""
        scores = {}

        # Extract scores from different analyses
        if "keyword_analysis" in analysis_results:
            scores["keyword"] = analysis_results["keyword_analysis"].get(
                "overall_keyword_score", 0
            )

        if "structure_analysis" in analysis_results:
            scores["structure"] = analysis_results["structure_analysis"].get(
                "structure_score", 0
            )

        if "readability_analysis" in analysis_results:
            scores["readability"] = analysis_results["readability_analysis"].get(
                "readability_score", 0
            )

        if "marketplace_analysis" in analysis_results:
            scores["marketplace"] = analysis_results["marketplace_analysis"].get(
                "compliance_score", 0
            )

        # Calculate weighted average
        total_score = 0
        total_weight = 0

        for category, score in scores.items():
            weight = self.seo_weights.get(f"{category}_optimization", 0.25)
            total_score += score * weight
            total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0

    def _generate_seo_recommendations(
        self, analysis_results: Dict[str, Any]
    ) -> List[str]:
        """Generate SEO recommendations based on analysis."""
        recommendations = []

        # Keyword recommendations
        if "keyword_analysis" in analysis_results:
            keyword_score = analysis_results["keyword_analysis"].get(
                "overall_keyword_score", 0
            )
            if keyword_score < 70:
                recommendations.append(
                    "Improve keyword optimization in title and description"
                )

        # Structure recommendations
        if "structure_analysis" in analysis_results:
            structure_score = analysis_results["structure_analysis"].get(
                "structure_score", 0
            )
            if structure_score < 70:
                recommendations.append(
                    "Improve content structure with better hierarchy"
                )

        # Readability recommendations
        if "readability_analysis" in analysis_results:
            readability_score = analysis_results["readability_analysis"].get(
                "readability_score", 0
            )
            if readability_score < 60:
                recommendations.append(
                    "Improve readability with shorter sentences and simpler words"
                )

        # Marketplace compliance recommendations
        if "marketplace_analysis" in analysis_results:
            compliance_score = analysis_results["marketplace_analysis"].get(
                "compliance_score", 0
            )
            if compliance_score < 80:
                recommendations.append("Address marketplace compliance issues")
                issues = analysis_results["marketplace_analysis"].get("issues", [])
                recommendations.extend(issues[:3])  # Add top 3 specific issues

        return recommendations[:10]  # Limit to top 10 recommendations

    # Missing helper methods
    def _generate_keyword_specific_recommendations(
        self,
        keyword: str,
        count: int,
        density: float,
        in_title: bool,
        in_description: bool,
    ) -> List[str]:
        """Generate keyword-specific recommendations."""
        recommendations = []

        if not in_title:
            recommendations.append(f"Add '{keyword}' to title for better SEO")
        if not in_description:
            recommendations.append(f"Include '{keyword}' in description")
        if density < 0.01:
            recommendations.append(
                f"Increase '{keyword}' density (currently {density:.3f})"
            )
        elif density > 0.03:
            recommendations.append(
                f"Reduce '{keyword}' density (currently {density:.3f})"
            )

        return recommendations

    def _calculate_structure_score(self, structure_analysis: Dict[str, Any]) -> float:
        """Calculate structure score from analysis."""
        score = 0.0

        # Title analysis score
        title_analysis = structure_analysis.get("title_analysis", {})
        score += title_analysis.get("length_score", 0) * 0.3

        # Description analysis score
        desc_analysis = structure_analysis.get("description_analysis", {})
        score += desc_analysis.get("length_score", 0) * 0.3

        # Bullet points score
        bullet_analysis = structure_analysis.get("bullet_points_analysis", {})
        score += bullet_analysis.get("structure_score", 0) * 0.2

        # Hierarchy score
        hierarchy_analysis = structure_analysis.get("content_hierarchy", {})
        score += hierarchy_analysis.get("hierarchy_score", 0) * 0.2

        return min(100.0, score)

    def _generate_structure_recommendations(
        self, structure_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate structure recommendations."""
        recommendations = []

        title_analysis = structure_analysis.get("title_analysis", {})
        if title_analysis.get("length_score", 0) < 80:
            recommendations.append("Optimize title length for better SEO")

        desc_analysis = structure_analysis.get("description_analysis", {})
        if desc_analysis.get("length_score", 0) < 80:
            recommendations.append("Optimize description length")

        bullet_analysis = structure_analysis.get("bullet_points_analysis", {})
        if bullet_analysis.get("count", 0) == 0:
            recommendations.append("Add bullet points for better structure")

        return recommendations

    async def _calculate_content_seo_score(
        self, content: Dict[str, Any], keywords: List[str]
    ) -> float:
        """Calculate content SEO score."""
        try:
            # Simple SEO score calculation
            score = 0.0

            # Title score
            if "title" in content and content["title"]:
                title_length = len(content["title"])
                if 50 <= title_length <= 80:
                    score += 25
                elif title_length > 0:
                    score += 15

            # Description score
            if "description" in content and content["description"]:
                desc_length = len(content["description"])
                if 200 <= desc_length <= 500:
                    score += 25
                elif desc_length > 0:
                    score += 15

            # Keyword score
            if keywords:
                all_text = self._extract_all_text(content)
                keyword_density = self._calculate_overall_keyword_density(
                    all_text, keywords
                )
                if 0.01 <= keyword_density <= 0.03:
                    score += 25
                elif keyword_density > 0:
                    score += 15

            # Structure score
            if "bullet_points" in content and content["bullet_points"]:
                score += 25

            return score

        except Exception:
            return 50.0

    async def _optimize_for_ranking(
        self, content: Dict[str, Any], keywords: List[str]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Optimize content for ranking."""
        optimized_content = content.copy()
        improvements = []

        # Add keywords to title if missing
        if "title" in content and keywords:
            title = content["title"]
            for keyword in keywords[:2]:  # Add top 2 keywords
                if keyword.lower() not in title.lower():
                    optimized_content["title"] = f"{keyword} {title}"
                    improvements.append(f"Added '{keyword}' to title")
                    break

        return optimized_content, improvements

    async def _optimize_for_visibility(
        self, content: Dict[str, Any], keywords: List[str]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Optimize content for visibility."""
        optimized_content = content.copy()
        improvements = []

        # Enhance description with keywords
        if "description" in content and keywords:
            description = content["description"]
            for keyword in keywords[:1]:  # Add top keyword
                if keyword.lower() not in description.lower():
                    optimized_content["description"] = (
                        f"{description} Features {keyword} technology."
                    )
                    improvements.append(f"Enhanced description with '{keyword}'")
                    break

        return optimized_content, improvements

    async def _optimize_for_conversion(
        self, content: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[str]]:
        """Optimize content for conversion."""
        optimized_content = content.copy()
        improvements = []

        # Add call-to-action if missing
        if "description" in content:
            description = content["description"]
            cta_phrases = ["buy now", "order today", "shop now"]
            has_cta = any(phrase in description.lower() for phrase in cta_phrases)

            if not has_cta:
                optimized_content["description"] = (
                    description + " Order now for fast shipping!"
                )
                improvements.append("Added call-to-action")

        return optimized_content, improvements

    def _generate_keyword_recommendations(
        self, keyword_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate keyword recommendations based on analysis."""
        recommendations = []

        for keyword, analysis in keyword_analysis.items():
            score = analysis.get("optimization_score", 0)
            if score < 70:
                if not analysis.get("in_title", False):
                    recommendations.append(f"Add '{keyword}' to title")
                if not analysis.get("in_description", False):
                    recommendations.append(f"Include '{keyword}' in description")
                if analysis.get("density", 0) < 0.01:
                    recommendations.append(f"Increase '{keyword}' usage")

        return recommendations[:5]  # Limit to top 5 recommendations
