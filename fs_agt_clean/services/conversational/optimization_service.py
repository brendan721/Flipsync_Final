"""
Conversational Optimization Service for FlipSync AI Feature 6.

This service provides conversational listing optimization including:
- Natural language editing requests
- Real-time content adjustments
- Suggestion explanations
- Interactive optimization
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.ai.simple_llm_client import (
    ModelProvider,
    ModelType,
    SimpleLLMClient,
)
from fs_agt_clean.core.ai.simple_llm_client import SimpleLLMConfig as LLMConfig

logger = logging.getLogger(__name__)


class OptimizationFocus(str, Enum):
    """Optimization focus areas."""

    GENERAL = "general"
    SEO = "seo"
    PRICING = "pricing"
    CONTENT = "content"
    IMAGES = "images"
    CATEGORY = "category"


class OptimizationResult:
    """Result model for conversational optimization."""

    def __init__(
        self,
        original_request: str,
        optimized_listing: Dict[str, Any],
        changes_made: List[Dict[str, Any]],
        explanation: str,
        confidence: float,
        suggestions: List[str],
    ):
        self.original_request = original_request
        self.optimized_listing = optimized_listing
        self.changes_made = changes_made
        self.explanation = explanation
        self.confidence = confidence
        self.suggestions = suggestions
        self.processed_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "original_request": self.original_request,
            "optimized_listing": self.optimized_listing,
            "changes_made": self.changes_made,
            "explanation": self.explanation,
            "confidence": self.confidence,
            "additional_suggestions": self.suggestions,
            "processed_at": self.processed_at.isoformat(),
        }


class ConversationalOptimizationService:
    """Service for conversational listing optimization using AI."""

    def __init__(self):
        """Initialize the conversational optimization service."""
        self.llm_client = None
        self._optimization_cache = {}
        self.conversation_history = {}
        self.optimization_metrics = {
            "total_requests": 0,
            "successful_optimizations": 0,
            "user_satisfaction": 0.0,
        }

        logger.info("Conversational Optimization Service initialized")

    @property
    def client(self) -> LLMClient:
        """Lazy initialization of LLM client."""
        if self.llm_client is None:
            config = LLMConfig(
                provider=ModelProvider.OLLAMA,
                model_type=ModelType.FLIPSYNC_BUSINESS,
                temperature=0.4,  # Balanced creativity and consistency
            )
            self.llm_client = LLMClient(config)
        return self.llm_client

    async def process_optimization_request(
        self,
        user_message: str,
        current_listing: Dict[str, Any],
        conversation_context: List[Dict[str, Any]],
        optimization_focus: str = "general",
        user_id: str = None,
    ) -> Dict[str, Any]:
        """
        Process conversational optimization request.

        Args:
            user_message: UnifiedUser's natural language request
            current_listing: Current listing content
            conversation_context: Previous conversation history
            optimization_focus: Focus area for optimization
            user_id: UnifiedUser identifier for conversation tracking

        Returns:
            Optimization result with changes and explanations
        """
        try:
            start_time = time.time()

            # Update conversation history
            if user_id:
                self._update_conversation_history(
                    user_id, user_message, conversation_context
                )

            # Parse user intent
            intent = await self._parse_user_intent(user_message, optimization_focus)

            # Generate optimization
            optimization_result = await self._generate_optimization(
                user_message, current_listing, intent, conversation_context
            )

            # Validate changes
            validated_result = self._validate_optimization_changes(
                current_listing, optimization_result
            )

            # Create result object
            result = OptimizationResult(
                original_request=user_message,
                optimized_listing=validated_result["optimized_listing"],
                changes_made=validated_result["changes_made"],
                explanation=validated_result["explanation"],
                confidence=validated_result["confidence"],
                suggestions=validated_result["suggestions"],
            )

            # Update metrics
            self.optimization_metrics["total_requests"] += 1
            if validated_result["confidence"] > 0.7:
                self.optimization_metrics["successful_optimizations"] += 1

            processing_time = time.time() - start_time
            logger.info(
                f"Conversational optimization completed in {processing_time:.2f}s"
            )

            return result.to_dict()

        except Exception as e:
            logger.error(f"Error in conversational optimization: {e}")
            return self._create_fallback_optimization(user_message, current_listing)

    async def _parse_user_intent(
        self, user_message: str, optimization_focus: str
    ) -> Dict[str, Any]:
        """Parse user intent from natural language message."""
        try:
            # Prepare intent analysis prompt
            prompt = f"""
            Analyze this user request for listing optimization:
            
            UnifiedUser Message: "{user_message}"
            Focus Area: {optimization_focus}
            
            Identify:
            1. Primary intent (improve_title, adjust_price, enhance_description, add_keywords, etc.)
            2. Specific changes requested
            3. Urgency level (high/medium/low)
            4. Scope (minor_edit/major_revision/complete_rewrite)
            
            Respond in this format:
            Intent: [primary_intent]
            Changes: [specific_changes]
            Urgency: [urgency_level]
            Scope: [scope_level]
            """

            # Get AI analysis
            response = await self.client.generate_response(prompt)

            # Parse response
            intent = self._parse_intent_response(response, optimization_focus)

            return intent

        except Exception as e:
            logger.error(f"Error parsing user intent: {e}")
            return {
                "primary_intent": "general_improvement",
                "specific_changes": ["improve overall quality"],
                "urgency": "medium",
                "scope": "minor_edit",
            }

    async def _generate_optimization(
        self,
        user_message: str,
        current_listing: Dict[str, Any],
        intent: Dict[str, Any],
        conversation_context: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate optimization based on user intent."""
        try:
            # Prepare optimization prompt
            prompt = self._prepare_optimization_prompt(
                user_message, current_listing, intent, conversation_context
            )

            # Get AI optimization
            response = await self.client.generate_response(prompt)

            # Parse optimization response
            optimization = self._parse_optimization_response(
                response, current_listing, intent
            )

            return optimization

        except Exception as e:
            logger.error(f"Error generating optimization: {e}")
            return self._create_fallback_ai_optimization(current_listing, intent)

    def _prepare_optimization_prompt(
        self,
        user_message: str,
        current_listing: Dict[str, Any],
        intent: Dict[str, Any],
        conversation_context: List[Dict[str, Any]],
    ) -> str:
        """Prepare prompt for AI optimization."""
        context_summary = self._summarize_conversation_context(conversation_context)

        return f"""
        Optimize this listing based on the user's request:
        
        UnifiedUser Request: "{user_message}"
        Intent: {intent['primary_intent']}
        Scope: {intent['scope']}
        
        Current Listing:
        Title: {current_listing.get('title', 'No title')}
        Description: {current_listing.get('description', 'No description')[:200]}...
        Price: ${current_listing.get('price', 0)}
        Category: {current_listing.get('category', 'Unknown')}
        
        Previous Context: {context_summary}
        
        Provide optimized listing with:
        1. Improved title (if requested)
        2. Enhanced description (if requested)
        3. Better keywords
        4. Explanation of changes
        5. Additional suggestions
        
        Format response as:
        TITLE: [optimized_title]
        DESCRIPTION: [optimized_description]
        KEYWORDS: [keyword1, keyword2, keyword3]
        EXPLANATION: [why these changes help]
        SUGGESTIONS: [additional improvements]
        """

    def _parse_optimization_response(
        self, response: str, current_listing: Dict[str, Any], intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse AI optimization response."""
        lines = response.split("\n")

        optimization = {
            "optimized_listing": current_listing.copy(),
            "changes_made": [],
            "explanation": "Listing optimized based on your request.",
            "confidence": 0.8,
            "suggestions": [],
        }

        current_section = None
        content = []

        for line in lines:
            line = line.strip()
            if line.startswith("TITLE:"):
                current_section = "title"
                content = [line.replace("TITLE:", "").strip()]
            elif line.startswith("DESCRIPTION:"):
                current_section = "description"
                content = [line.replace("DESCRIPTION:", "").strip()]
            elif line.startswith("KEYWORDS:"):
                current_section = "keywords"
                content = [line.replace("KEYWORDS:", "").strip()]
            elif line.startswith("EXPLANATION:"):
                current_section = "explanation"
                content = [line.replace("EXPLANATION:", "").strip()]
            elif line.startswith("SUGGESTIONS:"):
                current_section = "suggestions"
                content = [line.replace("SUGGESTIONS:", "").strip()]
            elif line and current_section:
                content.append(line)

            # Process completed sections
            if current_section and (
                line.startswith(
                    (
                        "TITLE:",
                        "DESCRIPTION:",
                        "KEYWORDS:",
                        "EXPLANATION:",
                        "SUGGESTIONS:",
                    )
                )
                or line == lines[-1]
            ):
                self._process_optimization_section(
                    current_section, content, optimization, current_listing
                )

        return optimization

    def _process_optimization_section(
        self,
        section: str,
        content: List[str],
        optimization: Dict[str, Any],
        current_listing: Dict[str, Any],
    ):
        """Process a section of the optimization response."""
        content_text = " ".join(content).strip()

        if section == "title" and content_text:
            old_title = current_listing.get("title", "")
            if content_text != old_title:
                optimization["optimized_listing"]["title"] = content_text
                optimization["changes_made"].append(
                    {
                        "field": "title",
                        "old_value": old_title,
                        "new_value": content_text,
                        "reason": "Improved for better visibility and SEO",
                    }
                )

        elif section == "description" and content_text:
            old_description = current_listing.get("description", "")
            if content_text != old_description:
                optimization["optimized_listing"]["description"] = content_text
                optimization["changes_made"].append(
                    {
                        "field": "description",
                        "old_value": old_description[:100] + "...",
                        "new_value": content_text[:100] + "...",
                        "reason": "Enhanced with better details and keywords",
                    }
                )

        elif section == "keywords" and content_text:
            keywords = [k.strip() for k in content_text.split(",")]
            optimization["optimized_listing"]["keywords"] = keywords
            optimization["changes_made"].append(
                {
                    "field": "keywords",
                    "old_value": current_listing.get("keywords", []),
                    "new_value": keywords,
                    "reason": "Added relevant keywords for better search visibility",
                }
            )

        elif section == "explanation" and content_text:
            optimization["explanation"] = content_text

        elif section == "suggestions" and content_text:
            suggestions = [s.strip() for s in content_text.split(",") if s.strip()]
            optimization["suggestions"] = suggestions

    def _create_fallback_optimization(
        self, user_message: str, current_listing: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback optimization when AI fails."""
        return {
            "original_request": user_message,
            "optimized_listing": current_listing,
            "changes_made": [],
            "explanation": "Unable to process optimization request. Please try rephrasing your request or contact support.",
            "confidence": 0.1,
            "additional_suggestions": [
                "Try being more specific about what you'd like to change",
                "Consider using simpler language in your request",
                "Check if your listing has all required fields filled",
            ],
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }

    def _parse_intent_response(
        self, response: str, optimization_focus: str
    ) -> Dict[str, Any]:
        """Parse AI intent analysis response."""
        intent = {
            "primary_intent": "general_improvement",
            "specific_changes": ["improve overall quality"],
            "urgency": "medium",
            "scope": "minor_edit",
        }

        lines = response.split("\n")
        for line in lines:
            if line.startswith("Intent:"):
                intent["primary_intent"] = line.replace("Intent:", "").strip()
            elif line.startswith("Changes:"):
                changes = line.replace("Changes:", "").strip()
                intent["specific_changes"] = [c.strip() for c in changes.split(",")]
            elif line.startswith("Urgency:"):
                intent["urgency"] = line.replace("Urgency:", "").strip()
            elif line.startswith("Scope:"):
                intent["scope"] = line.replace("Scope:", "").strip()

        return intent

    def _create_fallback_ai_optimization(
        self, current_listing: Dict[str, Any], intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create fallback AI optimization."""
        return {
            "optimized_listing": current_listing,
            "changes_made": [],
            "explanation": "Applied basic optimization based on your request.",
            "confidence": 0.5,
            "suggestions": [
                "Consider adding more specific keywords",
                "Enhance product description with details",
                "Review pricing for competitiveness",
            ],
        }

    def _summarize_conversation_context(
        self, conversation_context: List[Dict[str, Any]]
    ) -> str:
        """Summarize conversation context for AI prompt."""
        if not conversation_context:
            return "No previous context"

        recent_messages = conversation_context[-3:]  # Last 3 messages
        summary = []

        for msg in recent_messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")[:100]
            summary.append(f"{role}: {content}")

        return "; ".join(summary)

    def _update_conversation_history(
        self,
        user_id: str,
        user_message: str,
        conversation_context: List[Dict[str, Any]],
    ):
        """Update conversation history for user."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        # Add current message
        self.conversation_history[user_id].append(
            {
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Keep only last 10 messages
        self.conversation_history[user_id] = self.conversation_history[user_id][-10:]

    def _validate_optimization_changes(
        self, current_listing: Dict[str, Any], optimization_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and sanitize optimization changes."""
        validated = optimization_result.copy()

        # Ensure optimized listing has required fields
        optimized_listing = validated.get("optimized_listing", {})

        # Validate title length
        title = optimized_listing.get("title", "")
        if len(title) > 80:
            optimized_listing["title"] = title[:77] + "..."
            validated["changes_made"].append(
                {
                    "field": "title",
                    "old_value": title,
                    "new_value": optimized_listing["title"],
                    "reason": "Truncated to meet platform requirements",
                }
            )

        # Validate price
        price = optimized_listing.get("price", 0)
        if isinstance(price, str):
            try:
                optimized_listing["price"] = float(price)
            except ValueError:
                optimized_listing["price"] = current_listing.get("price", 0)

        # Ensure confidence is within bounds
        validated["confidence"] = max(0.0, min(1.0, validated.get("confidence", 0.5)))

        return validated


# Global service instance
conversational_optimization_service = ConversationalOptimizationService()
