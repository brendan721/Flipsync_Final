"""Advanced intent recognition agent for conversational interface."""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """
    Advanced intent recognition agent for conversational interface.

    Capabilities:
    - Multi-layered intent classification
    - Context-aware intent detection
    - Entity extraction and validation
    - Confidence scoring and fallback handling
    - Intent history and pattern analysis
    - Real-time intent adaptation
    """

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the intent recognizer agent.

        Args:
            config_manager: Configuration manager
            alert_manager: Alert manager for monitoring
            battery_optimizer: Battery optimizer for mobile efficiency
            config: Optional configuration overrides
        """
        self.agent_id = f"intent_recognizer_{uuid4()}"
        self.config_manager = config_manager or ConfigManager()
        self.alert_manager = alert_manager or AlertManager()
        self.battery_optimizer = battery_optimizer or BatteryOptimizer()
        self.config = config or {}

        # Intent classification models
        self.intent_patterns = {}
        self.entity_extractors = {}
        self.context_memory = {}
        self.intent_history = []

        # Confidence thresholds
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4,
        }

        # Intent categories
        self.intent_categories = {
            "product_search": ["find", "search", "look for", "show me", "browse"],
            "price_inquiry": ["price", "cost", "how much", "expensive", "cheap"],
            "listing_management": ["list", "sell", "create listing", "update", "edit"],
            "inventory_check": ["inventory", "stock", "available", "quantity", "count"],
            "analytics_request": [
                "analytics",
                "performance",
                "stats",
                "report",
                "metrics",
            ],
            "help_support": ["help", "support", "how to", "tutorial", "guide"],
            "account_management": ["account", "profile", "settings", "preferences"],
            "order_tracking": ["order", "shipment", "tracking", "delivery", "status"],
        }

        # Entity types
        self.entity_types = {
            "product_name": r"\b[A-Z][a-zA-Z0-9\s]+(?:Pro|Max|Plus|Ultra)?\b",
            "brand": r"\b(?:Apple|Samsung|Sony|Nike|Adidas|Microsoft|Amazon)\b",
            "price": r"\$?\d+(?:\.\d{2})?",
            "quantity": r"\b\d+\s*(?:pieces?|items?|units?)?\b",
            "category": r"\b(?:electronics|clothing|home|books|toys|sports)\b",
            "marketplace": r"\b(?:eBay|Amazon|Etsy|Facebook)\b",
            "time_period": r"\b(?:today|yesterday|week|month|year|daily|weekly|monthly)\b",
        }

        logger.info(f"Initialized IntentRecognizer: {self.agent_id}")

    async def initialize(self) -> None:
        """Initialize intent recognition resources."""
        await self._load_intent_models()
        await self._setup_entity_extractors()
        logger.info("Intent recognition resources initialized")

    async def _load_intent_models(self) -> None:
        """Load intent classification models."""
        # Initialize intent patterns for each category
        for category, keywords in self.intent_categories.items():
            self.intent_patterns[category] = {
                "keywords": keywords,
                "patterns": [rf"\b{keyword}\b" for keyword in keywords],
                "weight": 1.0,
            }

    async def _setup_entity_extractors(self) -> None:
        """Set up entity extraction patterns."""
        # Compile regex patterns for entity extraction
        for entity_type, pattern in self.entity_types.items():
            self.entity_extractors[entity_type] = re.compile(pattern, re.IGNORECASE)

    async def recognize_intent(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Recognize intent from user input with context awareness."""
        try:
            # Preprocess input
            processed_input = await self._preprocess_input(user_input)

            # Extract entities
            entities = await self._extract_entities(processed_input)

            # Classify intent
            intent_scores = await self._classify_intent(processed_input, context)

            # Get primary intent
            primary_intent = await self._get_primary_intent(intent_scores)

            # Validate intent with context
            validated_intent = await self._validate_intent_with_context(
                primary_intent, entities, context
            )

            # Update intent history
            await self._update_intent_history(validated_intent, user_input, context)

            return {
                "intent": validated_intent["intent"],
                "confidence": validated_intent["confidence"],
                "entities": entities,
                "intent_scores": intent_scores,
                "context_used": context is not None,
                "processing_time": datetime.now(timezone.utc).isoformat(),
                "agent_id": self.agent_id,
            }

        except Exception as e:
            logger.error(f"Error recognizing intent: {e}")
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "entities": {},
                "error": str(e),
                "agent_id": self.agent_id,
            }

    async def _preprocess_input(self, user_input: str) -> str:
        """Preprocess user input for intent recognition."""
        # Convert to lowercase
        processed = user_input.lower().strip()

        # Remove extra whitespace
        processed = re.sub(r"\s+", " ", processed)

        # Handle common contractions
        contractions = {
            "i'm": "i am",
            "you're": "you are",
            "it's": "it is",
            "don't": "do not",
            "can't": "cannot",
            "won't": "will not",
        }

        for contraction, expansion in contractions.items():
            processed = processed.replace(contraction, expansion)

        return processed

    async def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text."""
        entities = {}

        for entity_type, pattern in self.entity_extractors.items():
            matches = pattern.findall(text)
            if matches:
                entities[entity_type] = matches

        return entities

    async def _classify_intent(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """Classify intent with confidence scores."""
        intent_scores = {}

        for intent_category, pattern_data in self.intent_patterns.items():
            score = 0.0

            # Check keyword matches
            for keyword in pattern_data["keywords"]:
                if keyword in text:
                    score += 1.0

            # Check pattern matches
            for pattern in pattern_data["patterns"]:
                if re.search(pattern, text, re.IGNORECASE):
                    score += 0.5

            # Apply context boost
            if context:
                context_boost = await self._calculate_context_boost(
                    intent_category, context
                )
                score += context_boost

            # Normalize score
            max_possible_score = (
                len(pattern_data["keywords"]) + len(pattern_data["patterns"]) * 0.5
            )
            if max_possible_score > 0:
                normalized_score = min(1.0, score / max_possible_score)
            else:
                normalized_score = 0.0

            intent_scores[intent_category] = normalized_score

        return intent_scores

    async def _calculate_context_boost(
        self, intent_category: str, context: Dict[str, Any]
    ) -> float:
        """Calculate context boost for intent classification."""
        boost = 0.0

        # Previous intent context
        if "previous_intent" in context:
            prev_intent = context["previous_intent"]
            if self._are_related_intents(prev_intent, intent_category):
                boost += 0.2

        # Current page/section context
        if "current_section" in context:
            section = context["current_section"]
            if self._intent_matches_section(intent_category, section):
                boost += 0.3

        # UnifiedUser behavior context
        if "recent_actions" in context:
            actions = context["recent_actions"]
            if self._intent_matches_actions(intent_category, actions):
                boost += 0.1

        return boost

    def _are_related_intents(self, intent1: str, intent2: str) -> bool:
        """Check if two intents are related."""
        related_groups = [
            ["product_search", "price_inquiry", "listing_management"],
            ["inventory_check", "analytics_request"],
            ["help_support", "account_management"],
        ]

        for group in related_groups:
            if intent1 in group and intent2 in group:
                return True

        return False

    def _intent_matches_section(self, intent: str, section: str) -> bool:
        """Check if intent matches current section."""
        section_intent_map = {
            "search": "product_search",
            "listings": "listing_management",
            "inventory": "inventory_check",
            "analytics": "analytics_request",
            "account": "account_management",
            "orders": "order_tracking",
        }

        return section_intent_map.get(section) == intent

    def _intent_matches_actions(self, intent: str, actions: List[str]) -> bool:
        """Check if intent matches recent actions."""
        action_intent_map = {
            "search": "product_search",
            "view_listing": "listing_management",
            "check_inventory": "inventory_check",
            "view_analytics": "analytics_request",
        }

        for action in actions[-3:]:  # Check last 3 actions
            if action_intent_map.get(action) == intent:
                return True

        return False

    async def _get_primary_intent(
        self, intent_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Get primary intent from scores."""
        if not intent_scores:
            return {"intent": "unknown", "confidence": 0.0}

        # Get highest scoring intent
        primary_intent = max(intent_scores.items(), key=lambda x: x[1])
        intent_name, confidence = primary_intent

        # Determine confidence level
        if confidence >= self.confidence_thresholds["high"]:
            confidence_level = "high"
        elif confidence >= self.confidence_thresholds["medium"]:
            confidence_level = "medium"
        elif confidence >= self.confidence_thresholds["low"]:
            confidence_level = "low"
        else:
            confidence_level = "very_low"
            intent_name = "unknown"

        return {
            "intent": intent_name,
            "confidence": confidence,
            "confidence_level": confidence_level,
        }

    async def _validate_intent_with_context(
        self,
        primary_intent: Dict[str, Any],
        entities: Dict[str, List[str]],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Validate intent using entities and context."""
        intent = primary_intent["intent"]
        confidence = primary_intent["confidence"]

        # Entity validation
        required_entities = self._get_required_entities(intent)
        entity_validation = await self._validate_entities(entities, required_entities)

        # Adjust confidence based on entity validation
        if entity_validation["valid"]:
            confidence = min(1.0, confidence + 0.1)
        else:
            confidence = max(0.0, confidence - 0.2)

        # Context validation
        if context:
            context_validation = await self._validate_context(intent, context)
            if context_validation["valid"]:
                confidence = min(1.0, confidence + 0.05)

        return {
            "intent": intent,
            "confidence": confidence,
            "entity_validation": entity_validation,
            "context_validation": context_validation if context else None,
        }

    def _get_required_entities(self, intent: str) -> List[str]:
        """Get required entities for an intent."""
        entity_requirements = {
            "product_search": ["product_name", "category"],
            "price_inquiry": ["product_name"],
            "listing_management": ["product_name"],
            "inventory_check": ["product_name"],
            "analytics_request": ["time_period"],
            "order_tracking": [],
        }

        return entity_requirements.get(intent, [])

    async def _validate_entities(
        self, entities: Dict[str, List[str]], required: List[str]
    ) -> Dict[str, Any]:
        """Validate extracted entities."""
        missing_entities = []

        for required_entity in required:
            if required_entity not in entities or not entities[required_entity]:
                missing_entities.append(required_entity)

        return {
            "valid": len(missing_entities) == 0,
            "missing_entities": missing_entities,
            "extracted_entities": list(entities.keys()),
        }

    async def _validate_context(
        self, intent: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate intent against context."""
        # Simple context validation
        valid = True
        issues = []

        # Check if intent makes sense in current context
        current_section = context.get("current_section")
        if current_section and not self._intent_matches_section(
            intent, current_section
        ):
            # Don't mark as invalid, just note the mismatch
            issues.append(
                f"Intent '{intent}' doesn't match current section '{current_section}'"
            )

        return {
            "valid": valid,
            "issues": issues,
            "context_factors": list(context.keys()),
        }

    async def _update_intent_history(
        self,
        intent_result: Dict[str, Any],
        user_input: str,
        context: Optional[Dict[str, Any]],
    ) -> None:
        """Update intent history for pattern analysis."""
        history_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_input": user_input,
            "intent": intent_result["intent"],
            "confidence": intent_result["confidence"],
            "context": context,
        }

        self.intent_history.append(history_entry)

        # Keep only last 100 entries
        if len(self.intent_history) > 100:
            self.intent_history = self.intent_history[-100:]

    async def get_intent_suggestions(
        self, partial_input: str, context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Get intent suggestions for partial input."""
        try:
            suggestions = []

            # Get potential intents based on partial input
            potential_intents = await self._get_potential_intents(partial_input)

            # Rank suggestions based on context and history
            ranked_suggestions = await self._rank_intent_suggestions(
                potential_intents, context
            )

            return ranked_suggestions[:5]  # Return top 5 suggestions

        except Exception as e:
            logger.error(f"Error getting intent suggestions: {e}")
            return []

    async def _get_potential_intents(self, partial_input: str) -> List[str]:
        """Get potential intents from partial input."""
        potential_intents = []

        for intent_category, pattern_data in self.intent_patterns.items():
            for keyword in pattern_data["keywords"]:
                if (
                    keyword.startswith(partial_input.lower())
                    or partial_input.lower() in keyword
                ):
                    potential_intents.append(intent_category)
                    break

        return list(set(potential_intents))

    async def _rank_intent_suggestions(
        self, potential_intents: List[str], context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Rank intent suggestions based on context and history."""
        ranked = []

        for intent in potential_intents:
            score = 1.0

            # Context boost
            if context:
                context_boost = await self._calculate_context_boost(intent, context)
                score += context_boost

            # History boost (recent intents get higher score)
            history_boost = self._calculate_history_boost(intent)
            score += history_boost

            ranked.append(
                {
                    "intent": intent,
                    "score": score,
                    "description": self._get_intent_description(intent),
                }
            )

        return sorted(ranked, key=lambda x: x["score"], reverse=True)

    def _calculate_history_boost(self, intent: str) -> float:
        """Calculate boost based on intent history."""
        if not self.intent_history:
            return 0.0

        recent_intents = [entry["intent"] for entry in self.intent_history[-10:]]
        intent_count = recent_intents.count(intent)

        return min(0.3, intent_count * 0.1)

    def _get_intent_description(self, intent: str) -> str:
        """Get human-readable description of intent."""
        descriptions = {
            "product_search": "Search for products",
            "price_inquiry": "Check product prices",
            "listing_management": "Manage product listings",
            "inventory_check": "Check inventory status",
            "analytics_request": "View analytics and reports",
            "help_support": "Get help and support",
            "account_management": "Manage account settings",
            "order_tracking": "Track orders and shipments",
        }

        return descriptions.get(intent, "Unknown intent")

    def get_metrics(self) -> Dict[str, Any]:
        """Get intent recognition metrics."""
        total_recognitions = len(self.intent_history)

        if total_recognitions == 0:
            return {"total_recognitions": 0}

        # Calculate confidence distribution
        confidences = [entry["confidence"] for entry in self.intent_history]
        avg_confidence = sum(confidences) / len(confidences)

        # Calculate intent distribution
        intents = [entry["intent"] for entry in self.intent_history]
        intent_counts = {}
        for intent in intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        return {
            "total_recognitions": total_recognitions,
            "average_confidence": avg_confidence,
            "intent_distribution": intent_counts,
            "agent_id": self.agent_id,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }

    async def shutdown(self) -> None:
        """Clean up intent recognition resources."""
        self.intent_patterns.clear()
        self.entity_extractors.clear()
        self.context_memory.clear()
        self.intent_history.clear()
        logger.info(f"Intent recognizer {self.agent_id} shut down successfully")
