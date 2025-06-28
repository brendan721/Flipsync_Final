"""
Recommendation service for FlipSync chatbot.

This module provides recommendation capabilities for suggesting
relevant actions, products, or responses to users.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.models.recommendation import ChatRecommendationContext

logger = logging.getLogger(__name__)


class ChatbotRecommendationService:
    """
    Legacy recommendation service for backward compatibility.

    This class provides basic recommendation capabilities
    that are used by the chatbot service for legacy support.
    """

    def __init__(self):
        """Initialize the recommendation service."""
        self.recommendation_templates = self._load_recommendation_templates()
        self.initialized = True
        logger.info("ChatbotRecommendationService initialized for legacy support")

    def _load_recommendation_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load recommendation templates for different intents."""
        return {
            "listing": [
                {
                    "type": "action",
                    "title": "Optimize Your Listing",
                    "description": "Use AI to improve your product title and description",
                    "action": "optimize_listing",
                },
                {
                    "type": "tip",
                    "title": "Add High-Quality Photos",
                    "description": "Listings with multiple photos sell 40% faster",
                    "action": "add_photos",
                },
            ],
            "pricing": [
                {
                    "type": "action",
                    "title": "Market Price Analysis",
                    "description": "Get competitive pricing insights for your product",
                    "action": "analyze_pricing",
                },
                {
                    "type": "tip",
                    "title": "Dynamic Pricing",
                    "description": "Enable automatic price adjustments based on market conditions",
                    "action": "enable_dynamic_pricing",
                },
            ],
            "inventory": [
                {
                    "type": "action",
                    "title": "Inventory Sync",
                    "description": "Sync your inventory across all marketplaces",
                    "action": "sync_inventory",
                },
                {
                    "type": "tip",
                    "title": "Low Stock Alert",
                    "description": "Set up alerts when inventory runs low",
                    "action": "setup_alerts",
                },
            ],
            "general": [
                {
                    "type": "tip",
                    "title": "Getting Started",
                    "description": "Connect your marketplace accounts to begin",
                    "action": "connect_accounts",
                },
                {
                    "type": "action",
                    "title": "View Dashboard",
                    "description": "Check your sales performance and metrics",
                    "action": "view_dashboard",
                },
            ],
        }

    async def get_recommendations(
        self, context: ChatRecommendationContext
    ) -> List[Dict[str, Any]]:
        """
        Get recommendations based on context.

        Args:
            context: Recommendation context with user info and intent

        Returns:
            List of recommendation dictionaries
        """
        try:
            intent_type = context.intent.intent_type if context.intent else "general"

            # Get base recommendations for the intent
            base_recommendations = self.recommendation_templates.get(
                intent_type, self.recommendation_templates["general"]
            )

            # Personalize recommendations based on context
            personalized_recommendations = []

            for rec in base_recommendations:
                personalized_rec = rec.copy()
                personalized_rec["timestamp"] = datetime.now().isoformat()
                personalized_rec["relevance_score"] = self._calculate_relevance(
                    rec, context
                )
                personalized_recommendations.append(personalized_rec)

            # Sort by relevance score
            personalized_recommendations.sort(
                key=lambda x: x.get("relevance_score", 0.0), reverse=True
            )

            # Return top 3 recommendations
            return personalized_recommendations[:3]

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []

    def _calculate_relevance(
        self, recommendation: Dict[str, Any], context: ChatRecommendationContext
    ) -> float:
        """
        Calculate relevance score for a recommendation.

        Args:
            recommendation: Recommendation dictionary
            context: Recommendation context

        Returns:
            Relevance score between 0.0 and 1.0
        """
        try:
            base_score = 0.5  # Base relevance

            # Boost score based on intent confidence
            if context.intent and context.intent.confidence:
                base_score += context.intent.confidence * 0.3

            # Boost score for action-type recommendations
            if recommendation.get("type") == "action":
                base_score += 0.2

            # Boost score based on message content relevance
            if context.message:
                message_lower = context.message.lower()
                rec_title_lower = recommendation.get("title", "").lower()
                rec_desc_lower = recommendation.get("description", "").lower()

                # Simple keyword matching
                title_words = set(rec_title_lower.split())
                desc_words = set(rec_desc_lower.split())
                message_words = set(message_lower.split())

                title_overlap = len(title_words.intersection(message_words))
                desc_overlap = len(desc_words.intersection(message_words))

                if title_overlap > 0:
                    base_score += 0.1 * title_overlap
                if desc_overlap > 0:
                    base_score += 0.05 * desc_overlap

            # Ensure score is within bounds
            return min(max(base_score, 0.0), 1.0)

        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            return 0.5
