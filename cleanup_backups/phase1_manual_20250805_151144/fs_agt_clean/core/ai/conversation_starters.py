"""
FlipSync Conversation Starters
==============================

This module provides conversation starters and prompts specifically designed
for FlipSync's eBay sales optimization focus.
"""

from enum import Enum
from typing import Any, Dict, List


class ConversationCategory(str, Enum):
    """Categories of conversation starters."""

    PRICING = "pricing"
    LISTINGS = "listings"
    SHIPPING = "shipping"
    INVENTORY = "inventory"
    MARKETING = "marketing"
    ANALYTICS = "analytics"
    GENERAL = "general"


class FlipSyncConversationStarters:
    """Manages FlipSync-specific conversation starters and prompts."""

    def __init__(self):
        """Initialize conversation starters."""
        self.starters = self._initialize_starters()

    def _initialize_starters(self) -> Dict[ConversationCategory, List[str]]:
        """Initialize conversation starters by category."""
        return {
            ConversationCategory.PRICING: [
                "How can I optimize my pricing to sell electronics faster on eBay?",
                "What pricing strategy gets the best ROI for my product category?",
                "Should I use Best Offer or fixed pricing for faster sales?",
                "How do I price competitively while maintaining good profit margins?",
                "What's the optimal price range for my slow-moving inventory?",
            ],
            ConversationCategory.LISTINGS: [
                "How can I improve my eBay listings to get more views and sales?",
                "What keywords should I use in my titles for better search visibility?",
                "How do I optimize my item specifics for eBay's search algorithm?",
                "What listing format converts best: auction or Buy It Now?",
                "How can I improve my listing photos to increase conversion rates?",
            ],
            ConversationCategory.SHIPPING: [
                "How can I optimize shipping costs to improve my profit margins?",
                "What's the best shipping strategy for my product size and weight?",
                "Should I offer free shipping or charge separately for better sales?",
                "How do I calculate shipping costs to stay competitive?",
                "What shipping services give the best balance of cost and speed?",
            ],
            ConversationCategory.INVENTORY: [
                "Which products should I focus on for the highest profit potential?",
                "How do I identify trending products before they become saturated?",
                "What's the optimal inventory level for my sales velocity?",
                "How can I predict demand for seasonal products?",
                "Which slow-moving items should I liquidate vs. optimize?",
            ],
            ConversationCategory.MARKETING: [
                "When should I boost my listings with eBay Promoted Listings?",
                "What's the ROI on eBay advertising for my product categories?",
                "How do I optimize my promoted listings budget for maximum return?",
                "Should I run sales or promotions to increase velocity?",
                "What marketing strategies work best for my business size?",
            ],
            ConversationCategory.ANALYTICS: [
                "What metrics should I track to measure my eBay business performance?",
                "How do I analyze my sales data to identify optimization opportunities?",
                "What's my current sales velocity compared to category averages?",
                "How can I improve my sell-through rate?",
                "What are my most profitable product categories and why?",
            ],
            ConversationCategory.GENERAL: [
                "How can FlipSync help me sell faster and earn more on eBay?",
                "What's the biggest opportunity to improve my eBay business right now?",
                "How do I get started with automated listing optimization?",
                "What FlipSync features will have the most impact on my profits?",
                "How can I scale my eBay business more efficiently?",
            ],
        }

    def get_starters_by_category(self, category: ConversationCategory) -> List[str]:
        """Get conversation starters for a specific category."""
        return self.starters.get(category, [])

    def get_all_starters(self) -> List[str]:
        """Get all conversation starters as a flat list."""
        all_starters = []
        for starters in self.starters.values():
            all_starters.extend(starters)
        return all_starters

    def get_random_starters(self, count: int = 3) -> List[str]:
        """Get random conversation starters for display."""
        import random

        all_starters = self.get_all_starters()
        return random.sample(all_starters, min(count, len(all_starters)))

    def get_contextual_starters(self, user_context: Dict[str, Any]) -> List[str]:
        """Get conversation starters based on user context."""
        # Analyze user context to suggest relevant starters
        suggested_starters = []

        # Check user's business focus
        business_type = user_context.get("business_type", "").lower()
        recent_activity = user_context.get("recent_activity", "").lower()

        # Prioritize based on context
        if "pricing" in recent_activity or "price" in business_type:
            suggested_starters.extend(
                self.get_starters_by_category(ConversationCategory.PRICING)[:2]
            )

        if "listing" in recent_activity or "optimization" in recent_activity:
            suggested_starters.extend(
                self.get_starters_by_category(ConversationCategory.LISTINGS)[:2]
            )

        if "shipping" in recent_activity or "fulfillment" in recent_activity:
            suggested_starters.extend(
                self.get_starters_by_category(ConversationCategory.SHIPPING)[:1]
            )

        # Always include general starters
        suggested_starters.extend(
            self.get_starters_by_category(ConversationCategory.GENERAL)[:1]
        )

        # If no context matches, return general starters
        if not suggested_starters:
            suggested_starters = self.get_starters_by_category(
                ConversationCategory.GENERAL
            )[:3]

        return suggested_starters[:5]  # Limit to 5 suggestions

    def get_onboarding_starters(self) -> List[str]:
        """Get conversation starters for new users during onboarding."""
        return [
            "How can FlipSync help me sell faster and earn more on eBay?",
            "What's the first optimization I should make to my eBay listings?",
            "How do I get started with automated pricing optimization?",
            "What FlipSync features will have the biggest impact on my profits?",
            "How can I analyze my current eBay performance to identify opportunities?",
        ]

    def get_dashboard_starters(self) -> List[str]:
        """Get conversation starters for the main dashboard."""
        return [
            "How can I sell electronics faster on eBay?",
            "What pricing strategy gets the best ROI?",
            "When should I boost my listings with ads?",
            "How can I optimize shipping costs for better margins?",
            "What listing improvements will increase my sales velocity?",
        ]


# Global instance
conversation_starters = FlipSyncConversationStarters()
