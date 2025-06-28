"""
Intent recognition service for FlipSync chatbot.

This module provides intent recognition capabilities for understanding
user messages and routing them to appropriate agents.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.models.chat import MessageIntent

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """
    Legacy intent recognizer for backward compatibility.

    This class provides basic intent recognition capabilities
    that are used by the chatbot service for legacy support.
    """

    def __init__(self):
        """Initialize the intent recognizer."""
        self.intent_patterns = self._load_intent_patterns()
        self.initialized = True
        logger.info("IntentRecognizer initialized for legacy support")

    def _load_intent_patterns(self) -> Dict[str, List[str]]:
        """Load intent recognition patterns."""
        return {
            "greeting": [
                r"\b(hello|hi|hey|greetings|good morning|good afternoon|good evening)\b",
                r"\b(start|begin|help me get started)\b",
            ],
            "listing": [
                r"\b(list|listing|sell|post|upload|add product)\b",
                r"\b(create listing|new listing|list item)\b",
            ],
            "pricing": [
                r"\b(price|pricing|cost|value|worth)\b",
                r"\b(how much|what price|price check)\b",
            ],
            "inventory": [
                r"\b(inventory|stock|items|products)\b",
                r"\b(manage inventory|check stock)\b",
            ],
            "customer_service": [
                r"\b(customer|service|support|help|issue|problem)\b",
                r"\b(complaint|refund|return)\b",
            ],
            "order": [
                r"\b(order|purchase|buy|sale|transaction)\b",
                r"\b(order status|track order)\b",
            ],
            "shipping": [
                r"\b(ship|shipping|delivery|send|mail)\b",
                r"\b(shipping cost|delivery time)\b",
            ],
            "analytics": [
                r"\b(analytics|report|stats|statistics|performance)\b",
                r"\b(sales data|metrics|insights)\b",
            ],
            "farewell": [
                r"\b(bye|goodbye|see you|farewell|thanks|thank you)\b",
                r"\b(that's all|done|finished)\b",
            ],
        }

    async def recognize_intent(
        self,
        message: str,
        conversation_history: Optional[List[Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> MessageIntent:
        """
        Recognize intent from a user message.

        Args:
            message: UnifiedUser message text
            conversation_history: Optional conversation history
            context: Optional context information

        Returns:
            MessageIntent object with recognized intent
        """
        try:
            message_lower = message.lower().strip()

            # Check patterns for each intent
            best_intent = "general"
            best_confidence = 0.0

            for intent_type, patterns in self.intent_patterns.items():
                confidence = 0.0
                matches = 0

                for pattern in patterns:
                    if re.search(pattern, message_lower):
                        matches += 1
                        confidence += 0.3  # Base confidence per pattern match

                # Normalize confidence based on number of patterns
                if matches > 0:
                    confidence = min(confidence / len(patterns), 1.0)

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_intent = intent_type

            # Ensure minimum confidence
            if best_confidence < 0.1:
                best_confidence = 0.1
                best_intent = "general"

            return MessageIntent(
                intent_type=best_intent,
                confidence=best_confidence,
                entities=[],
                metadata={
                    "message_length": len(message),
                    "timestamp": datetime.now().isoformat(),
                    "recognition_method": "pattern_matching",
                },
            )

        except Exception as e:
            logger.error(f"Error recognizing intent: {e}")
            return MessageIntent(
                intent_type="general",
                confidence=0.1,
                entities=[],
                metadata={"error": str(e), "timestamp": datetime.now().isoformat()},
            )
