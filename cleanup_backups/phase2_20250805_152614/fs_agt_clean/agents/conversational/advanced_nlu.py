"""
Advanced Natural Language Understanding for FlipSync Conversational Interface.

This module provides sophisticated NLU capabilities including intent recognition,
entity extraction, context management, and intelligent agent routing.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an extracted entity from user input."""

    entity_type: str
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Intent:
    """Represents a recognized user intent."""

    intent_name: str
    confidence: float
    entities: List[Entity] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    suggested_agent: Optional[str] = None


@dataclass
class ConversationContext:
    """Maintains conversation context and history."""

    session_id: UUID = field(default_factory=uuid4)
    user_id: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    current_topic: Optional[str] = None
    active_entities: Dict[str, Entity] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    last_interaction: datetime = field(default_factory=datetime.utcnow)


class AdvancedNLU:
    """
    Advanced Natural Language Understanding system.

    Features:
    - Intent recognition with confidence scoring
    - Named entity recognition and extraction
    - Context-aware understanding
    - UnifiedAgent routing recommendations
    - Multi-turn conversation support
    - E-commerce domain specialization
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Advanced NLU system.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.agent_routing_rules = self._load_agent_routing_rules()
        self.conversation_contexts: Dict[str, ConversationContext] = {}

        logger.info("AdvancedNLU initialized")

    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent recognition patterns."""
        return {
            "price_inquiry": [
                r"what.*price.*",
                r"how much.*cost.*",
                r"price.*for.*",
                r"cost.*of.*",
                r".*pricing.*",
            ],
            "inventory_check": [
                r".*in stock.*",
                r".*available.*",
                r".*inventory.*",
                r"how many.*",
                r".*quantity.*",
            ],
            "ebay_inventory_query": [
                r".*ebay.*inventory.*",
                r".*my.*ebay.*listings.*",
                r".*ebay.*items.*",
                r".*how many.*ebay.*items.*",
                r".*see.*my.*ebay.*inventory.*",
                r".*ebay.*stock.*",
                r".*ebay.*products.*",
                r".*my.*ebay.*store.*",
                r".*can.*you.*see.*my.*ebay.*inventory.*",
                r".*show.*me.*my.*ebay.*inventory.*",
                r".*ebay.*listing.*count.*",
            ],
            "marketplace_inventory_query": [
                r".*marketplace.*inventory.*",
                r".*my.*listings.*",
                r".*how many.*items.*do.*i.*have.*",
                r".*inventory.*count.*",
                r".*total.*items.*",
                r".*item.*count.*",
                r".*listing.*count.*",
                r".*my.*products.*",
                r".*my.*inventory.*",
                r".*how many.*products.*",
            ],
            "listing_management": [
                r".*create.*listing.*",
                r".*update.*listing.*",
                r".*edit.*product.*",
                r".*modify.*description.*",
                r".*change.*title.*",
            ],
            "sales_analytics": [
                r".*sales.*report.*",
                r".*performance.*",
                r".*analytics.*",
                r".*metrics.*",
                r"how.*selling.*",
            ],
            "shipping_inquiry": [
                r".*shipping.*",
                r".*delivery.*",
                r".*tracking.*",
                r".*shipment.*",
                r"when.*arrive.*",
            ],
            "competitor_analysis": [
                r".*competitor.*",
                r".*competition.*",
                r".*market.*analysis.*",
                r".*compare.*prices.*",
                r".*other.*sellers.*",
            ],
            "strategy_planning": [
                r".*strategy.*",
                r".*plan.*",
                r".*optimize.*",
                r".*improve.*sales.*",
                r".*recommendations.*",
            ],
        }

    def _load_entity_patterns(self) -> Dict[str, str]:
        """Load entity extraction patterns."""
        return {
            "product_sku": r"\b[A-Z0-9]{6,12}\b",
            "price": r"\$?\d+\.?\d*",
            "quantity": r"\b\d+\s*(pieces?|items?|units?)?\b",
            "marketplace": r"\b(amazon|ebay|etsy|shopify)\b",
            "category": r"\b(electronics|clothing|books|toys|home)\b",
            "time_period": r"\b(today|yesterday|week|month|year|daily|weekly|monthly)\b",
            "order_id": r"\b\d{10,15}\b",
        }

    def _load_agent_routing_rules(self) -> Dict[str, str]:
        """Load agent routing rules based on intents."""
        return {
            "price_inquiry": "market_agent",
            "inventory_check": "ebay_agent",  # Route to eBay agent for inventory queries
            "listing_management": "content_agent",
            "sales_analytics": "executive_agent",
            "shipping_inquiry": "logistics_agent",
            "competitor_analysis": "market_analyzer",
            "strategy_planning": "strategy_agent",
            # New eBay-specific routing rules
            "ebay_inventory_query": "ebay_agent",
            "marketplace_inventory_query": "ebay_agent",
        }

    async def understand(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Intent:
        """
        Understand user input and extract intent, entities, and context.

        Args:
            user_input: UnifiedUser's natural language input
            session_id: Optional session identifier
            user_id: Optional user identifier

        Returns:
            Recognized intent with entities and routing information
        """
        # Get or create conversation context
        context = self._get_conversation_context(session_id, user_id)

        # Recognize intent
        intent_name, intent_confidence = self._recognize_intent(user_input, context)

        # Extract entities
        entities = self._extract_entities(user_input)

        # Update context with new entities
        self._update_context_entities(context, entities)

        # Determine suggested agent
        suggested_agent = self._route_to_agent(intent_name, entities, context)

        # Create intent object
        intent = Intent(
            intent_name=intent_name,
            confidence=intent_confidence,
            entities=entities,
            context=context.active_entities,
            suggested_agent=suggested_agent,
        )

        # Update conversation history
        self._update_conversation_history(context, user_input, intent)

        logger.info(
            f"Understood intent: {intent_name} (confidence: {intent_confidence:.2f})"
        )
        return intent

    def _get_conversation_context(
        self, session_id: Optional[str], user_id: Optional[str]
    ) -> ConversationContext:
        """Get or create conversation context."""
        if session_id and session_id in self.conversation_contexts:
            context = self.conversation_contexts[session_id]
            context.last_interaction = datetime.utcnow()
            return context

        # Create new context
        context = ConversationContext(user_id=user_id)
        if session_id:
            self.conversation_contexts[session_id] = context

        return context

    def _recognize_intent(
        self, user_input: str, context: ConversationContext
    ) -> Tuple[str, float]:
        """Recognize user intent from input."""
        user_input_lower = user_input.lower()
        best_intent = "general_inquiry"
        best_confidence = 0.0

        for intent_name, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    # Calculate confidence based on pattern match quality
                    confidence = self._calculate_pattern_confidence(
                        pattern, user_input_lower
                    )

                    # Boost confidence if related to current topic
                    if context.current_topic and intent_name in context.current_topic:
                        confidence *= 1.2

                    if confidence > best_confidence:
                        best_intent = intent_name
                        best_confidence = confidence

        return best_intent, min(1.0, best_confidence)

    def _extract_entities(self, user_input: str) -> List[Entity]:
        """Extract entities from user input."""
        entities = []

        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, user_input, re.IGNORECASE)

            for match in matches:
                entity = Entity(
                    entity_type=entity_type,
                    value=match.group(),
                    confidence=0.8,  # Base confidence for pattern matches
                    start_pos=match.start(),
                    end_pos=match.end(),
                )
                entities.append(entity)

        return entities

    def _update_context_entities(
        self, context: ConversationContext, entities: List[Entity]
    ) -> None:
        """Update conversation context with new entities."""
        for entity in entities:
            # Keep most recent entity of each type
            context.active_entities[entity.entity_type] = entity

    def _route_to_agent(
        self, intent_name: str, entities: List[Entity], context: ConversationContext
    ) -> Optional[str]:
        """Determine which agent should handle this request."""
        # Primary routing based on intent
        suggested_agent = self.agent_routing_rules.get(intent_name)

        # Secondary routing based on entities
        if not suggested_agent:
            for entity in entities:
                if entity.entity_type == "marketplace":
                    suggested_agent = f"{entity.value}_agent"
                    break
                elif entity.entity_type == "category":
                    suggested_agent = "content_agent"
                    break

        # Context-based routing
        if not suggested_agent and context.current_topic:
            if "pricing" in context.current_topic:
                suggested_agent = "market_agent"
            elif "inventory" in context.current_topic:
                suggested_agent = "inventory_agent"

        return suggested_agent or "general_assistant"

    def _calculate_pattern_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for pattern match."""
        # Simple confidence calculation based on pattern specificity
        base_confidence = 0.7

        # Boost for exact matches
        if pattern.replace(".*", "").replace(r"\b", "") in text:
            base_confidence += 0.2

        # Boost for multiple keyword matches
        keywords = re.findall(r"\w+", pattern.replace(".*", ""))
        keyword_matches = sum(1 for keyword in keywords if keyword in text)
        if keywords:
            keyword_ratio = keyword_matches / len(keywords)
            base_confidence += keyword_ratio * 0.1

        return min(1.0, base_confidence)

    def _update_conversation_history(
        self, context: ConversationContext, user_input: str, intent: Intent
    ) -> None:
        """Update conversation history."""
        history_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_input": user_input,
            "intent": intent.intent_name,
            "confidence": intent.confidence,
            "entities": [entity.entity_type for entity in intent.entities],
            "suggested_agent": intent.suggested_agent,
        }

        context.conversation_history.append(history_entry)

        # Keep only last 10 interactions
        if len(context.conversation_history) > 10:
            context.conversation_history = context.conversation_history[-10:]

        # Update current topic
        context.current_topic = intent.intent_name

    async def get_context_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary of conversation context."""
        if session_id not in self.conversation_contexts:
            return {"error": "Session not found"}

        context = self.conversation_contexts[session_id]

        return {
            "session_id": str(context.session_id),
            "user_id": context.user_id,
            "current_topic": context.current_topic,
            "active_entities": {
                entity_type: entity.value
                for entity_type, entity in context.active_entities.items()
            },
            "conversation_length": len(context.conversation_history),
            "last_interaction": context.last_interaction.isoformat(),
        }

    async def clear_context(self, session_id: str) -> bool:
        """Clear conversation context for a session."""
        if session_id in self.conversation_contexts:
            del self.conversation_contexts[session_id]
            return True
        return False
