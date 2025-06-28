"""
Intent Recognition System for FlipSync AI Routing
================================================

This module provides intelligent intent recognition to route user messages
to the appropriate specialized agents based on content analysis and context.
"""

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Enhanced intent patterns with weighted keywords and phrases
INTENT_PATTERNS = {
    "ebay_inventory_query": {
        "high_weight": [
            "ebay inventory",
            "my ebay listings",
            "ebay items",
            "how many ebay items",
            "see my ebay inventory",
            "ebay stock levels",
            "ebay products",
            "my ebay store",
            "ebay listing count",
            "total ebay listings",
            "active ebay listings",
            "ebay item count",
            "can you see my ebay inventory",
            "show me my ebay inventory",
            "what's in my ebay inventory",
            "ebay inventory status",
        ],
        "medium_weight": [
            "ebay",
            "inventory",
            "listings",
            "items",
            "stock",
            "products",
            "store",
            "marketplace",
            "how many",
            "count",
            "total",
            "active",
            "see",
            "show",
            "view",
        ],
        "low_weight": ["my", "the", "all", "current", "available"],
    },
    "marketplace_inventory_query": {
        "high_weight": [
            "marketplace inventory",
            "my listings",
            "how many items do I have",
            "inventory count",
            "total items",
            "item count",
            "listing count",
            "my products",
            "my inventory",
            "inventory status",
            "stock count",
            "how many products",
            "total listings",
            "active items",
        ],
        "medium_weight": [
            "inventory",
            "listings",
            "items",
            "products",
            "stock",
            "count",
            "total",
            "how many",
            "my",
            "active",
            "available",
        ],
        "low_weight": ["current", "all", "existing", "present"],
    },
    "market_query": {
        "high_weight": [
            "pricing analysis",
            "price comparison",
            "competitor pricing",
            "market price",
            "amazon price",
            "ebay price",
            "pricing strategy",
            "inventory management",
            "stock levels",
            "asin",
            "sku",
            "marketplace optimization",
            "profit margin",
            "pricing for",
            "cost analysis",
            "revenue optimization",
        ],
        "medium_weight": [
            "price",
            "pricing",
            "inventory",
            "stock",
            "amazon",
            "ebay",
            "marketplace",
            "competitor",
            "market",
            "sell",
            "buy",
            "product",
            "cost",
            "profit",
            "margin",
            "revenue",
            "sales",
            "competition",
            "demand",
            "supply",
        ],
        "low_weight": ["listing", "trend", "forecast", "optimization"],
    },
    "analytics_query": {
        "high_weight": [
            "sales report",
            "performance report",
            "analytics dashboard",
            "conversion rate",
            "performance metrics",
            "data analysis",
            "kpi tracking",
            "roi analysis",
            "traffic analysis",
            "sales data",
            "performance data",
            "business intelligence",
        ],
        "medium_weight": [
            "report",
            "analytics",
            "performance",
            "metrics",
            "data",
            "dashboard",
            "chart",
            "graph",
            "statistics",
            "analysis",
            "kpi",
            "roi",
            "conversion",
            "traffic",
            "views",
            "clicks",
            "impressions",
            "ctr",
        ],
        "low_weight": [
            "growth",
            "decline",
            "trend",
            "benchmark",
            "revenue",
            "profit",
            "loss",
        ],
    },
    "logistics_query": {
        "high_weight": [
            "track shipment",
            "shipping status",
            "delivery tracking",
            "fba shipment",
            "warehouse management",
            "fulfillment center",
            "shipping cost",
            "delivery time",
            "package tracking",
            "shipment arrival",
            "logistics optimization",
        ],
        "medium_weight": [
            "shipping",
            "delivery",
            "warehouse",
            "fulfillment",
            "logistics",
            "tracking",
            "carrier",
            "transport",
            "freight",
            "ups",
            "fedex",
            "usps",
            "dhl",
            "package",
            "shipment",
            "dispatch",
            "arrival",
        ],
        "low_weight": ["transit", "customs", "duty", "tax", "import", "export"],
    },
    "content_query": {
        "high_weight": [
            "product description",
            "listing optimization",
            "seo optimization",
            "content creation",
            "product title",
            "keyword optimization",
            "listing content",
            "product copy",
            "optimize listing",
            "improve description",
            "content strategy",
        ],
        "medium_weight": [
            "description",
            "title",
            "content",
            "copy",
            "write",
            "create",
            "optimize",
            "seo",
            "keyword",
            "tag",
            "category",
            "brand",
            "feature",
            "benefit",
            "specification",
            "review",
            "rating",
            "feedback",
        ],
        "low_weight": [
            "image",
            "photo",
            "testimonial",
            "bullet",
            "headline",
            "caption",
            "alt text",
            "meta",
        ],
    },
    "executive_query": {
        "high_weight": [
            "business strategy",
            "growth strategy",
            "strategic planning",
            "business plan",
            "investment strategy",
            "business growth",
            "strategic decision",
            "business advice",
            "growth planning",
            "business direction",
            "strategic guidance",
        ],
        "medium_weight": [
            "strategy",
            "decision",
            "plan",
            "planning",
            "business",
            "growth",
            "recommendation",
            "advice",
            "guidance",
            "direction",
            "goal",
            "objective",
            "target",
            "milestone",
            "roadmap",
            "vision",
            "mission",
            "expansion",
        ],
        "low_weight": [
            "budget",
            "roi",
            "investment",
            "risk",
            "opportunity",
            "threat",
            "swot",
            "competitive",
        ],
    },
    "general_query": {
        "high_weight": [
            "hello",
            "hi",
            "help me",
            "can you help",
            "how do i",
            "what is",
            "thank you",
            "thanks",
            "goodbye",
            "bye",
        ],
        "medium_weight": [
            "help",
            "how",
            "what",
            "when",
            "where",
            "why",
            "who",
            "can",
            "could",
            "would",
            "should",
            "please",
            "explain",
            "show",
            "tell",
        ],
        "low_weight": [],
    },
}

# Context keywords that modify intent confidence
CONTEXT_MODIFIERS = {
    "urgency": ["urgent", "asap", "immediately", "quickly", "fast", "rush"],
    "uncertainty": ["maybe", "perhaps", "possibly", "might", "could be", "not sure"],
    "comparison": ["vs", "versus", "compare", "better", "worse", "best", "worst"],
    "temporal": [
        "today",
        "tomorrow",
        "yesterday",
        "this week",
        "next month",
        "quarterly",
    ],
    "quantitative": ["how much", "how many", "percentage", "rate", "ratio", "number"],
}


@dataclass
class IntentResult:
    """Result of intent recognition analysis."""

    primary_intent: str
    confidence: float
    secondary_intents: List[Tuple[str, float]]
    context_modifiers: List[str]
    extracted_entities: Dict[str, Any]
    reasoning: str
    requires_handoff: bool = False
    suggested_agent: Optional[str] = None


class IntentRecognizer:
    """Advanced intent recognition system with rule-based and contextual analysis."""

    def __init__(self):
        """Initialize the intent recognizer."""
        self.intent_patterns = INTENT_PATTERNS
        self.context_modifiers = CONTEXT_MODIFIERS

        # Compile regex patterns for efficiency with weights
        self.compiled_patterns = {}
        for intent, weight_groups in self.intent_patterns.items():
            self.compiled_patterns[intent] = {}
            for weight, keywords in weight_groups.items():
                if keywords:  # Only compile if keywords exist
                    pattern = (
                        r"\b(?:" + "|".join(re.escape(kw) for kw in keywords) + r")\b"
                    )
                    self.compiled_patterns[intent][weight] = re.compile(
                        pattern, re.IGNORECASE
                    )

        # Track conversation context for better intent detection
        self.conversation_context = defaultdict(list)

        # Intent confidence thresholds
        self.confidence_thresholds = {"high": 0.8, "medium": 0.5, "low": 0.3}

    def recognize_intent(
        self,
        message: str,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
    ) -> IntentResult:
        """
        Recognize intent from user message with contextual analysis.

        Args:
            message: UnifiedUser message text
            user_id: Optional user identifier
            conversation_id: Optional conversation identifier
            conversation_history: Optional conversation history for context

        Returns:
            IntentResult with primary intent and analysis
        """
        try:
            # Preprocess message
            processed_message = self._preprocess_message(message)

            # Calculate intent scores using multiple methods
            rule_based_scores = self._calculate_rule_based_scores(processed_message)
            context_scores = self._calculate_context_scores(
                processed_message, conversation_history
            )

            # Combine scores with weights
            combined_scores = self._combine_scores(rule_based_scores, context_scores)

            # Determine primary intent
            primary_intent, primary_confidence = self._get_primary_intent(
                combined_scores
            )

            # Get secondary intents
            secondary_intents = self._get_secondary_intents(
                combined_scores, primary_intent
            )

            # Extract context modifiers
            context_modifiers = self._extract_context_modifiers(processed_message)

            # Extract entities
            entities = self._extract_entities(processed_message, primary_intent)

            # Generate reasoning
            reasoning = self._generate_reasoning(
                primary_intent, primary_confidence, rule_based_scores, context_modifiers
            )

            # Determine if handoff is needed
            requires_handoff = self._requires_agent_handoff(
                primary_intent, primary_confidence, conversation_history
            )

            # Suggest appropriate agent
            suggested_agent = self._suggest_agent(primary_intent, entities)

            # Update conversation context
            if conversation_id:
                self._update_conversation_context(
                    conversation_id, message, primary_intent, entities
                )

            return IntentResult(
                primary_intent=primary_intent,
                confidence=primary_confidence,
                secondary_intents=secondary_intents,
                context_modifiers=context_modifiers,
                extracted_entities=entities,
                reasoning=reasoning,
                requires_handoff=requires_handoff,
                suggested_agent=suggested_agent,
            )

        except Exception as e:
            logger.error(f"Error in intent recognition: {e}")
            return IntentResult(
                primary_intent="general_query",
                confidence=0.1,
                secondary_intents=[],
                context_modifiers=[],
                extracted_entities={},
                reasoning=f"Error in intent recognition: {e}",
                requires_handoff=False,
                suggested_agent="assistant",
            )

    def _preprocess_message(self, message: str) -> str:
        """Preprocess message for better pattern matching."""
        # Convert to lowercase for pattern matching
        processed = message.lower().strip()

        # Remove extra whitespace
        processed = re.sub(r"\s+", " ", processed)

        # Handle common abbreviations
        abbreviations = {
            "roi": "return on investment",
            "seo": "search engine optimization",
            "ctr": "click through rate",
            "kpi": "key performance indicator",
            "asin": "amazon standard identification number",
            "sku": "stock keeping unit",
        }

        for abbr, full in abbreviations.items():
            processed = re.sub(r"\b" + abbr + r"\b", full, processed)

        return processed

    def _calculate_rule_based_scores(self, message: str) -> Dict[str, float]:
        """Calculate intent scores based on weighted keyword pattern matching."""
        scores = {}

        # Weight multipliers for different keyword categories
        weight_multipliers = {
            "high_weight": 3.0,
            "medium_weight": 1.5,
            "low_weight": 1.0,
        }

        for intent, weight_patterns in self.compiled_patterns.items():
            total_score = 0.0
            total_matches = 0

            for weight, pattern in weight_patterns.items():
                matches = pattern.findall(message)
                if matches:
                    match_count = len(matches)
                    unique_matches = len(set(matches))
                    multiplier = weight_multipliers.get(weight, 1.0)

                    # Score based on unique matches with weight multiplier
                    weight_score = unique_matches * multiplier * 0.1
                    total_score += weight_score
                    total_matches += match_count

            if total_score > 0:
                # Normalize by message length but cap the penalty
                message_length = len(message.split())
                length_factor = min(
                    message_length / 10.0, 1.0
                )  # Don't over-penalize long messages

                # Apply length normalization
                normalized_score = total_score / max(length_factor, 0.5)

                # Boost for multiple matches across different weight categories
                if total_matches > 1:
                    normalized_score *= 1.2

                scores[intent] = min(normalized_score, 1.0)
            else:
                scores[intent] = 0.0

        return scores

    def _calculate_context_scores(
        self, message: str, conversation_history: Optional[List[Dict]]
    ) -> Dict[str, float]:
        """Calculate intent scores based on conversation context."""
        context_scores = defaultdict(float)

        if not conversation_history:
            return dict(context_scores)

        # Analyze recent messages for context
        recent_messages = (
            conversation_history[-5:]
            if len(conversation_history) > 5
            else conversation_history
        )

        for msg in recent_messages:
            msg_content = msg.get("content", "").lower()

            # Look for intent patterns in recent context
            for intent, weight_patterns in self.compiled_patterns.items():
                for weight, pattern in weight_patterns.items():
                    if pattern.search(msg_content):
                        # Give more weight to high-weight pattern matches in context
                        weight_boost = 0.15 if weight == "high_weight" else 0.1
                        context_scores[intent] += weight_boost
                        break  # Don't double-count for same intent

        # Normalize context scores
        max_context_score = max(context_scores.values()) if context_scores else 1.0
        if max_context_score > 0:
            for intent in context_scores:
                context_scores[intent] = min(
                    context_scores[intent] / max_context_score, 0.3
                )

        return dict(context_scores)

    def _combine_scores(
        self, rule_scores: Dict[str, float], context_scores: Dict[str, float]
    ) -> Dict[str, float]:
        """Combine rule-based and context scores with appropriate weights."""
        combined = {}

        # Weight: 70% rule-based, 30% context
        rule_weight = 0.7
        context_weight = 0.3

        all_intents = set(rule_scores.keys()) | set(context_scores.keys())

        for intent in all_intents:
            rule_score = rule_scores.get(intent, 0.0)
            context_score = context_scores.get(intent, 0.0)

            combined[intent] = (rule_score * rule_weight) + (
                context_score * context_weight
            )

        return combined

    def _get_primary_intent(self, scores: Dict[str, float]) -> Tuple[str, float]:
        """Determine the primary intent from combined scores."""
        if not scores:
            return "general_query", 0.1

        # Get intent with highest score
        primary_intent = max(scores, key=scores.get)
        primary_confidence = scores[primary_intent]

        # If confidence is too low, default to general query
        if primary_confidence < self.confidence_thresholds["low"]:
            return "general_query", primary_confidence

        return primary_intent, primary_confidence

    def _get_secondary_intents(
        self, scores: Dict[str, float], primary_intent: str
    ) -> List[Tuple[str, float]]:
        """Get secondary intents ranked by confidence."""
        secondary = []

        for intent, score in scores.items():
            if intent != primary_intent and score > self.confidence_thresholds["low"]:
                secondary.append((intent, score))

        # Sort by confidence and return top 3
        secondary.sort(key=lambda x: x[1], reverse=True)
        return secondary[:3]

    def _extract_context_modifiers(self, message: str) -> List[str]:
        """Extract context modifiers from the message."""
        modifiers = []

        for modifier_type, keywords in self.context_modifiers.items():
            for keyword in keywords:
                if keyword in message:
                    modifiers.append(modifier_type)
                    break

        return modifiers

    def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """Extract relevant entities based on intent."""
        entities = {}

        # Extract numbers and currencies
        numbers = re.findall(r"\b\d+(?:\.\d+)?\b", message)
        if numbers:
            entities["numbers"] = [float(n) for n in numbers]

        currencies = re.findall(r"\$\d+(?:\.\d+)?", message)
        if currencies:
            entities["currencies"] = currencies

        # Extract dates and time references
        time_patterns = [
            r"\b(?:today|tomorrow|yesterday)\b",
            r"\b(?:this|next|last)\s+(?:week|month|quarter|year)\b",
            r"\b\d{1,2}\/\d{1,2}\/\d{2,4}\b",
        ]

        for pattern in time_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            if matches:
                entities.setdefault("time_references", []).extend(matches)

        # Intent-specific entity extraction
        if intent == "market_query":
            # Extract product identifiers
            asin_pattern = r"\b[A-Z0-9]{10}\b"
            asins = re.findall(asin_pattern, message)
            if asins:
                entities["asins"] = asins

        elif intent == "analytics_query":
            # Extract metric names
            metric_patterns = [r"\b(?:revenue|profit|sales|conversion|ctr|roi)\b"]
            for pattern in metric_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                if matches:
                    entities.setdefault("metrics", []).extend(matches)

        return entities

    def _generate_reasoning(
        self,
        intent: str,
        confidence: float,
        scores: Dict[str, float],
        modifiers: List[str],
    ) -> str:
        """Generate human-readable reasoning for the intent classification."""
        reasoning_parts = []

        # Primary intent reasoning
        if confidence >= self.confidence_thresholds["high"]:
            reasoning_parts.append(f"High confidence ({confidence:.2f}) for {intent}")
        elif confidence >= self.confidence_thresholds["medium"]:
            reasoning_parts.append(f"Medium confidence ({confidence:.2f}) for {intent}")
        else:
            reasoning_parts.append(f"Low confidence ({confidence:.2f}) for {intent}")

        # Top scoring intents
        top_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_scores = [
            f"{intent}: {score:.2f}" for intent, score in top_intents if score > 0
        ]
        if top_scores:
            reasoning_parts.append(f"Top scores: {', '.join(top_scores)}")

        # Context modifiers
        if modifiers:
            reasoning_parts.append(f"Context modifiers: {', '.join(modifiers)}")

        return "; ".join(reasoning_parts)

    def _requires_agent_handoff(
        self, intent: str, confidence: float, conversation_history: Optional[List[Dict]]
    ) -> bool:
        """Determine if the query requires handoff to a specialized agent."""
        # High confidence specialized intents require handoff
        specialized_intents = [
            "market_query",
            "analytics_query",
            "logistics_query",
            "content_query",
            "executive_query",
        ]

        if (
            intent in specialized_intents
            and confidence >= self.confidence_thresholds["medium"]
        ):
            return True

        # Check for context switches in conversation
        if conversation_history and len(conversation_history) > 0:
            last_message = conversation_history[-1]
            last_intent = last_message.get("intent")

            if last_intent and last_intent != intent and intent in specialized_intents:
                return True

        return False

    def _suggest_agent(self, intent: str, entities: Dict[str, Any]) -> str:
        """Suggest the most appropriate agent for the intent."""
        agent_mapping = {
            "market_query": "market",
            "analytics_query": "analytics",
            "logistics_query": "logistics",
            "content_query": "content",
            "executive_query": "executive",
            "general_query": "assistant",
            # eBay-specific agent mappings
            "ebay_inventory_query": "ebay",
            "marketplace_inventory_query": "ebay",
        }

        return agent_mapping.get(intent, "assistant")

    def _update_conversation_context(
        self, conversation_id: str, message: str, intent: str, entities: Dict[str, Any]
    ):
        """Update conversation context for future intent recognition."""
        context_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "intent": intent,
            "entities": entities,
        }

        self.conversation_context[conversation_id].append(context_entry)

        # Keep only last 10 entries per conversation
        if len(self.conversation_context[conversation_id]) > 10:
            self.conversation_context[conversation_id] = self.conversation_context[
                conversation_id
            ][-10:]

    def get_intent_statistics(self) -> Dict[str, Any]:
        """Get statistics about intent recognition performance."""
        total_conversations = len(self.conversation_context)

        intent_counts = defaultdict(int)
        for conversation in self.conversation_context.values():
            for entry in conversation:
                intent_counts[entry["intent"]] += 1

        return {
            "total_conversations": total_conversations,
            "intent_distribution": dict(intent_counts),
            "available_intents": list(self.intent_patterns.keys()),
            "confidence_thresholds": self.confidence_thresholds,
        }
