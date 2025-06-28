"""
Recommendation service for the FlipSync chatbot.

This module provides integration between the chatbot and recommendation algorithms,
"""

import logging
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.models.recommendation import ChatRecommendationContext
from fs_agt_clean.core.recommendations.algorithms.collaborative import (
    CollaborativeFiltering,
)
from fs_agt_clean.core.recommendations.algorithms.content_based import (
    ContentBasedFiltering,
)
from fs_agt_clean.core.recommendations.algorithms.hybrid import (
    HybridRecommender,
    Recommendation,
)

# Configure logging
logger = logging.getLogger(__name__)


class ChatbotRecommendationService:
    """
    Service for integrating recommendation algorithms with the chatbot.

    Connects recommendation algorithms with the chatbot service, implementing
    proactive recommendation triggers based on conversation context.
    """

    def __init__(self):
        """Initialize the service with recommendation algorithms."""
        self.collaborative_recommender = CollaborativeFiltering()
        self.content_based_recommender = ContentBasedFiltering()
        self.hybrid_recommender = HybridRecommender()

        # Configure recommendation triggers
        self._configure_recommendation_triggers()

    def _configure_recommendation_triggers(self):
        """Configure triggers based on conversation context."""
        # Define triggers for different recommendation types
        self.product_triggers = [
            "similar products",
            "alternatives",
            "related items",
            "other products",
            "recommendations",
            "suggest",
        ]

        self.marketplace_triggers = [
            "marketplace",
            "platform",
            "sell on",
            "listing on",
            "amazon",
            "ebay",
            "etsy",
            "walmart",
        ]

        self.pricing_triggers = [
            "price",
            "pricing",
            "cost",
            "value",
            "discount",
            "competitive",
            "profit margin",
            "fee",
        ]

        self.content_triggers = [
            "description",
            "title",
            "image",
            "photo",
            "picture",
            "keyword",
            "seo",
            "search ranking",
        ]

        # Define entity types that should trigger recommendations
        self.recommendation_entity_types = [
            "product_category",
            "marketplace",
            "price_range",
            "product_attribute",
            "competitor",
        ]

    async def get_recommendations(
        self, context: ChatRecommendationContext
    ) -> Dict[str, Any]:
        """
        Get recommendations based on conversation context.

        Args:
            context: The recommendation context including conversation history,
                     user profile, and extracted entities

        Returns:
            Dictionary containing recommendations and metadata
        """
        try:
            # Determine recommendation type based on context
            recommendation_type = self._determine_recommendation_type(context)

            if not recommendation_type:
                # No relevant recommendation type found
                return {"has_recommendations": False}

            # Get recommendations based on type
            if recommendation_type == "product":
                # Note: Assuming _get_product_recommendations returns List[Recommendation]
                product_recs: List[Recommendation] = (
                    await self._get_product_recommendations(context)
                )
                # Convert Recommendation objects to Dict[str, Any]
                recommendations = [rec.__dict__ for rec in product_recs]
            elif recommendation_type == "marketplace":
                recommendations = await self._get_marketplace_recommendations(context)
            elif recommendation_type == "pricing":
                recommendations = await self._get_pricing_recommendations(context)
            elif recommendation_type == "content":
                recommendations = await self._get_content_recommendations(context)
            else:
                # Fallback to general recommendations
                general_recs: List[Recommendation] = (
                    await self._get_general_recommendations(context)
                )
                # Convert Recommendation objects to Dict[str, Any]
                recommendations = [rec.__dict__ for rec in general_recs]

            # Format recommendations for display
            formatted_recommendations = self._format_recommendations(
                recommendations, recommendation_type
            )

            return {
                "has_recommendations": bool(formatted_recommendations),
                "recommendation_type": recommendation_type,
                "recommendations": formatted_recommendations,
                "confidence": self._calculate_recommendation_confidence(context),
                "context_factors": self._extract_context_factors(context),
            }

        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return {"has_recommendations": False, "error": str(e)}

    def _determine_recommendation_type(
        self, context: ChatRecommendationContext
    ) -> Optional[str]:
        """
        Determine the type of recommendation to provide based on context.

        Args:
            context: The recommendation context

        Returns:
            Recommendation type or None if no relevant type found
        """
        # Extract text from recent messages
        recent_text = " ".join(
            [msg.get("text", "").lower() for msg in context.recent_messages]
        )

        # Check for triggers in recent messages
        if any(trigger in recent_text for trigger in self.product_triggers):
            return "product"

        if any(trigger in recent_text for trigger in self.marketplace_triggers):
            return "marketplace"

        if any(trigger in recent_text for trigger in self.pricing_triggers):
            return "pricing"

        if any(trigger in recent_text for trigger in self.content_triggers):
            return "content"

        # Check for relevant entities
        for entity in context.extracted_entities:
            entity_type = entity.get("entity")
            if entity_type in self.recommendation_entity_types:
                if entity_type == "product_category":
                    return "product"
                elif entity_type == "marketplace":
                    return "marketplace"
                elif entity_type == "price_range":
                    return "pricing"
                elif entity_type == "product_attribute":
                    return "content"

        # Check current intent
        agent_type = context.current_intent.get("agent_type")
        if agent_type == "market":
            return "product"
        elif agent_type == "content":
            return "content"

        # No relevant recommendation type found
        return None

    async def _get_product_recommendations(
        self, context: ChatRecommendationContext
    ) -> List[Recommendation]:
        """
        Get product recommendations based on conversation context.

        Args:
            context: The recommendation context

        Returns:
            List of product recommendations
        """
        # Extract product-related entities
        product_category = None
        product_attributes = []

        for entity in context.extracted_entities:
            if entity.get("entity") == "product_category":
                product_category = entity.get("value")
            elif entity.get("entity") == "product_attribute":
                product_attributes.append(entity.get("value"))

        # Use hybrid recommender for best results
        recommendations = self.hybrid_recommender.recommend(user_id=context.user_id)

        return recommendations

    async def _get_marketplace_recommendations(
        self, context: ChatRecommendationContext
    ) -> List[Dict[str, Any]]:
        """
        Get marketplace recommendations based on conversation context.

        Args:
            context: The recommendation context

        Returns:
            List of marketplace recommendations
        """
        # Extract marketplace-related entities
        current_marketplace = None
        product_category = None

        for entity in context.extracted_entities:
            if entity.get("entity") == "marketplace":
                current_marketplace = entity.get("value")
            elif entity.get("entity") == "product_category":
                product_category = entity.get("value")

        # TODO: Implement or find correct method for marketplace recommendations
        recommendations = []  # Placeholder

        return recommendations

    async def _get_pricing_recommendations(
        self, context: ChatRecommendationContext
    ) -> List[Dict[str, Any]]:
        """
        Get pricing recommendations based on conversation context.

        Args:
            context: The recommendation context

        Returns:
            List of pricing recommendations
        """
        # Extract pricing-related entities
        product_category = None
        marketplace = None
        competitor = None

        for entity in context.extracted_entities:
            if entity.get("entity") == "product_category":
                product_category = entity.get("value")
            elif entity.get("entity") == "marketplace":
                marketplace = entity.get("value")
            elif entity.get("entity") == "competitor":
                competitor = entity.get("value")

        # TODO: Implement or find correct method for pricing recommendations
        recommendations = []  # Placeholder

        return recommendations

    async def _get_content_recommendations(
        self, context: ChatRecommendationContext
    ) -> List[Dict[str, Any]]:
        """
        Get content optimization recommendations based on conversation context.

        Args:
            context: The recommendation context

        Returns:
            List of content recommendations
        """
        # Extract content-related entities
        product_category = None
        marketplace = None
        content_type = "description"  # Default

        for entity in context.extracted_entities:
            if entity.get("entity") == "product_category":
                product_category = entity.get("value")
            elif entity.get("entity") == "marketplace":
                marketplace = entity.get("value")
            elif entity.get("entity") == "content_type":
                content_type = entity.get("value")

        # TODO: Implement or find correct method for content recommendations
        recommendations = []  # Placeholder

        return recommendations

    async def _get_general_recommendations(
        self, context: ChatRecommendationContext
    ) -> List[Recommendation]:
        """
        Get general recommendations when no specific type is determined.

        Args:
            context: The recommendation context

        Returns:
            List of general recommendations
        """
        # Use hybrid recommender for general recommendations
        recommendations = self.hybrid_recommender.recommend(user_id=context.user_id)

        return recommendations

    def _format_recommendations(
        self, recommendations: List[Dict[str, Any]], recommendation_type: str
    ) -> List[Dict[str, Any]]:
        """
        Format recommendations for display in chat.

        Args:
            recommendations: Raw recommendations from recommenders
            recommendation_type: Type of recommendations

        Returns:
            Formatted recommendations for display
        """
        formatted = []

        for rec in recommendations:
            formatted_rec = {
                "id": rec.get("id"),
                "title": rec.get("title"),
                "description": rec.get("description"),
                "type": recommendation_type,
                "confidence": rec.get("confidence", 0.7),
                "action": self._get_recommendation_action(rec, recommendation_type),
            }

            # Add type-specific fields
            if recommendation_type == "product":
                formatted_rec.update(
                    {
                        "image_url": rec.get("image_url"),
                        "price": rec.get("price"),
                        "marketplace": rec.get("marketplace"),
                    }
                )
            elif recommendation_type == "marketplace":
                formatted_rec.update(
                    {
                        "logo_url": rec.get("logo_url"),
                        "benefits": rec.get("benefits", []),
                        "fees": rec.get("fees"),
                    }
                )
            elif recommendation_type == "pricing":
                formatted_rec.update(
                    {
                        "suggested_price": rec.get("suggested_price"),
                        "price_range": rec.get("price_range"),
                        "competitor_prices": rec.get("competitor_prices", []),
                    }
                )
            elif recommendation_type == "content":
                formatted_rec.update(
                    {
                        "before": rec.get("before"),
                        "after": rec.get("after"),
                        "improvement_points": rec.get("improvement_points", []),
                    }
                )

            formatted.append(formatted_rec)

        return formatted

    def _get_recommendation_action(
        self, recommendation: Dict[str, Any], recommendation_type: str
    ) -> Dict[str, Any]:
        """
        Get the action for a recommendation.

        Args:
            recommendation: The recommendation
            recommendation_type: Type of recommendation

        Returns:
            Action for the recommendation
        """
        if recommendation_type == "product":
            return {
                "type": "view_product",
                "label": "View Product",
                "url": recommendation.get("url"),
            }
        elif recommendation_type == "marketplace":
            return {
                "type": "explore_marketplace",
                "label": "Explore Marketplace",
                "url": recommendation.get("url"),
            }
        elif recommendation_type == "pricing":
            return {
                "type": "apply_pricing",
                "label": "Apply Pricing",
                "data": {"price": recommendation.get("suggested_price")},
            }
        elif recommendation_type == "content":
            return {
                "type": "apply_content",
                "label": "Apply Changes",
                "data": {"content": recommendation.get("after")},
            }
        else:
            return {
                "type": "view_details",
                "label": "View Details",
                "url": recommendation.get("url"),
            }

    def _calculate_recommendation_confidence(
        self, context: ChatRecommendationContext
    ) -> float:
        """
        Calculate the confidence score for recommendations.

        Args:
            context: The recommendation context

        Returns:
            Confidence score for recommendations
        """
        # This method needs to be implemented to calculate the confidence score
        # based on the recommendation context.
        # For now, we'll return a default value
        return 0.7

    def _extract_context_factors(
        self, context: ChatRecommendationContext
    ) -> Dict[str, Any]:
        """
        Extract context factors from the recommendation context.

        Args:
            context: The recommendation context

        Returns:
            Dictionary containing context factors
        """
        # This method needs to be implemented to extract relevant context factors
        # from the recommendation context.
        # For now, we'll return an empty dictionary
        return {}
