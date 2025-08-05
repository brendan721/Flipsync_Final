"""Decision engine for the brain service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Decision:
    """Decision data structure."""

    action: str
    confidence: float
    reasoning: str
    metadata: Optional[Dict[str, Any]] = None


class DecisionEngine:
    """Makes decisions based on events, context, and memory."""

    async def make_decision(
        self,
        context: Dict[str, Any],
        actions: List[str],
        memory_context: Dict[str, Any],
    ) -> Decision:
        """Make a decision based on context and available actions.

        Args:
            context: Current context
            actions: Available actions
            memory_context: Memory context

        Returns:
            Decision with action and confidence
        """
        # Default to processing with medium confidence if no better option
        action = "process"
        confidence = 0.5
        reasoning = "Default processing action"

        # Adjust based on event type if present
        if "type" in context:
            event_type = context["type"]
            if event_type == "error":
                action = "retry" if "retry" in actions else "escalate"
                confidence = 0.8
                reasoning = "Error event requires immediate attention"
            elif event_type == "alert":
                action = "investigate"
                confidence = 0.7
                reasoning = "Alert requires investigation"
            elif event_type == "request":
                # Check memory for similar requests
                similar_requests = memory_context.get("short_term", [])
                if similar_requests:
                    action = "approve"
                    confidence = 0.6
                    reasoning = "Similar requests were approved recently"

        return Decision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            metadata={"context": context, "memory_used": bool(memory_context)},
        )
