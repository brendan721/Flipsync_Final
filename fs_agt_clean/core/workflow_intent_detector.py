"""
Workflow Intent Detection System for FlipSync
============================================

This module detects when user messages should trigger multi-agent workflows
instead of single-agent responses.
"""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class WorkflowIntent:
    """Represents a detected workflow intent."""

    workflow_type: str
    confidence: float
    participating_agents: List[str]
    context: Dict[str, Any]
    trigger_phrases: List[str]


class WorkflowIntentDetector:
    """Detects workflow intents from user messages."""

    def __init__(self):
        """Initialize the workflow intent detector."""
        self.workflow_patterns = self._initialize_workflow_patterns()
        logger.info("Workflow Intent Detector initialized")

    def _initialize_workflow_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize workflow detection patterns."""
        return {
            # Product Analysis Workflow
            "product_analysis": {
                "patterns": [
                    r"analyze.*product",
                    r"product.*analysis",
                    r"evaluate.*item",
                    r"assess.*product",
                    r"review.*product",
                    r"what.*think.*product",
                    r"should.*sell.*this",
                    r"is.*this.*good.*sell",
                    r"worth.*selling",
                    r"profitable.*product",
                ],
                "keywords": [
                    "analyze product",
                    "product analysis",
                    "evaluate item",
                    "assess product",
                    "review product",
                    "product review",
                    "should I sell",
                    "worth selling",
                    "profitable",
                    "market potential",
                    "product evaluation",
                ],
                "participating_agents": ["content", "market", "executive"],
                "context_extractors": {
                    "product_name": r"(?:product|item|this)\s+(?:is\s+)?([^.!?]+)",
                    "marketplace": r"(?:on|for)\s+(ebay|amazon|etsy|walmart)",
                    "price_mentioned": r"\$?(\d+(?:\.\d{2})?)",
                },
            },
            # Listing Optimization Workflow
            "listing_optimization": {
                "patterns": [
                    r"optimize.*listing",
                    r"improve.*listing",
                    r"better.*listing",
                    r"listing.*optimization",
                    r"seo.*listing",
                    r"listing.*seo",
                    r"improve.*title",
                    r"better.*description",
                    r"optimize.*keywords",
                    r"listing.*performance",
                ],
                "keywords": [
                    "optimize listing",
                    "improve listing",
                    "better listing",
                    "listing optimization",
                    "seo listing",
                    "listing seo",
                    "improve title",
                    "better description",
                    "optimize keywords",
                    "listing performance",
                    "boost visibility",
                    "increase sales",
                ],
                "participating_agents": ["content", "market", "executive"],
                "context_extractors": {
                    "listing_url": r"(?:https?://)?(?:www\.)?(?:ebay|amazon|etsy)\.com/[^\s]+",
                    "marketplace": r"(?:on|for)\s+(ebay|amazon|etsy|walmart)",
                    "optimization_type": r"(seo|keywords|title|description|images|pricing)",
                },
            },
            # Decision Consensus Workflow
            "decision_consensus": {
                "patterns": [
                    r"should.*I.*(?:buy|sell|list|price)",
                    r"what.*do.*you.*think",
                    r"need.*advice",
                    r"help.*decide",
                    r"decision.*help",
                    r"recommend.*strategy",
                    r"best.*approach",
                    r"what.*would.*you.*do",
                    r"consensus.*on",
                    r"team.*opinion",
                ],
                "keywords": [
                    "should I",
                    "what do you think",
                    "need advice",
                    "help decide",
                    "decision help",
                    "recommend strategy",
                    "best approach",
                    "what would you do",
                    "consensus",
                    "team opinion",
                    "multiple perspectives",
                    "agent input",
                ],
                "participating_agents": ["executive", "content", "market"],
                "context_extractors": {
                    "decision_type": r"should.*I\s+(buy|sell|list|price|invest|expand)",
                    "product_mentioned": r"(?:this|the)\s+([^.!?]+)",
                    "budget_mentioned": r"budget.*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)",
                },
            },
            # Pricing Strategy Workflow
            "pricing_strategy": {
                "patterns": [
                    r"pricing.*strategy",
                    r"price.*analysis",
                    r"competitive.*pricing",
                    r"price.*optimization",
                    r"pricing.*help",
                    r"what.*price",
                    r"how.*much.*charge",
                    r"pricing.*advice",
                    r"market.*pricing",
                    r"price.*research",
                ],
                "keywords": [
                    "pricing strategy",
                    "price analysis",
                    "competitive pricing",
                    "price optimization",
                    "pricing help",
                    "what price",
                    "how much charge",
                    "pricing advice",
                    "market pricing",
                    "price research",
                    "pricing model",
                    "dynamic pricing",
                ],
                "participating_agents": ["market", "content", "executive"],
                "context_extractors": {
                    "product_category": r"(?:category|type):\s*([^.!?]+)",
                    "current_price": r"currently.*\$?(\d+(?:\.\d{2})?)",
                    "target_margin": r"margin.*(\d+)%",
                },
            },
            # Market Research Workflow
            "market_research": {
                "patterns": [
                    r"market.*research",
                    r"market.*analysis",
                    r"competitor.*analysis",
                    r"market.*trends",
                    r"research.*market",
                    r"market.*insights",
                    r"competitive.*landscape",
                    r"market.*opportunity",
                    r"demand.*analysis",
                    r"market.*study",
                ],
                "keywords": [
                    "market research",
                    "market analysis",
                    "competitor analysis",
                    "market trends",
                    "research market",
                    "market insights",
                    "competitive landscape",
                    "market opportunity",
                    "demand analysis",
                    "market study",
                    "market intelligence",
                    "trend analysis",
                ],
                "participating_agents": [
                    "market",
                    "competitor_analyzer",
                    "trend_detector",
                    "executive",
                ],
                "context_extractors": {
                    "product_category": r"(?:for|in)\s+([^.!?]+)\s+(?:market|category)",
                    "timeframe": r"(?:next|past|last)\s+(\d+)\s+(days?|weeks?|months?|years?)",
                    "geographic_focus": r"(?:in|for)\s+(US|USA|UK|Canada|Europe|global)",
                },
            },
        }

    def detect_workflow_intent(self, message: str) -> Optional[WorkflowIntent]:
        """
        Detect if a message should trigger a workflow.

        Args:
            message: UnifiedUser message to analyze

        Returns:
            WorkflowIntent if a workflow should be triggered, None otherwise
        """
        message_lower = message.lower().strip()

        # Score each workflow type
        workflow_scores = {}

        for workflow_type, config in self.workflow_patterns.items():
            score = self._calculate_workflow_score(message_lower, config)
            if score > 0:
                workflow_scores[workflow_type] = score

        # If no workflows scored, return None
        if not workflow_scores:
            return None

        # Find the best matching workflow
        best_workflow = max(workflow_scores.keys(), key=lambda k: workflow_scores[k])
        best_score = workflow_scores[best_workflow]

        # Require minimum confidence threshold
        confidence = min(best_score / 10.0, 1.0)  # Normalize to 0-1
        if confidence < 0.3:  # 30% minimum confidence
            return None

        # Extract context for the workflow
        config = self.workflow_patterns[best_workflow]
        context = self._extract_context(message, config.get("context_extractors", {}))

        # Find trigger phrases that matched
        trigger_phrases = self._find_trigger_phrases(message_lower, config)

        logger.info(
            f"Detected workflow intent: {best_workflow} (confidence: {confidence:.2f})"
        )

        return WorkflowIntent(
            workflow_type=best_workflow,
            confidence=confidence,
            participating_agents=config["participating_agents"],
            context=context,
            trigger_phrases=trigger_phrases,
        )

    def _calculate_workflow_score(self, message: str, config: Dict[str, Any]) -> float:
        """Calculate score for a workflow based on pattern and keyword matches."""
        score = 0.0

        # Check regex patterns (higher weight)
        for pattern in config.get("patterns", []):
            if re.search(pattern, message, re.IGNORECASE):
                score += 3.0

        # Check keyword matches (lower weight)
        for keyword in config.get("keywords", []):
            if keyword.lower() in message:
                score += 1.0

        return score

    def _extract_context(
        self, message: str, extractors: Dict[str, str]
    ) -> Dict[str, Any]:
        """Extract context information from the message using regex extractors."""
        context = {}

        for key, pattern in extractors.items():
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                context[key] = match.group(1).strip()

        # Add the original message for reference
        context["original_message"] = message
        context["message_length"] = len(message)

        return context

    def _find_trigger_phrases(self, message: str, config: Dict[str, Any]) -> List[str]:
        """Find which trigger phrases matched in the message."""
        trigger_phrases = []

        # Check keywords that matched
        for keyword in config.get("keywords", []):
            if keyword.lower() in message:
                trigger_phrases.append(keyword)

        # Check patterns that matched (extract the actual matched text)
        for pattern in config.get("patterns", []):
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                trigger_phrases.append(match.group(0))

        return trigger_phrases

    def get_supported_workflows(self) -> List[str]:
        """Get list of supported workflow types."""
        return list(self.workflow_patterns.keys())

    def get_workflow_description(self, workflow_type: str) -> Optional[Dict[str, Any]]:
        """Get description and details for a specific workflow type."""
        if workflow_type not in self.workflow_patterns:
            return None

        config = self.workflow_patterns[workflow_type]
        descriptions = {
            "product_analysis": "Comprehensive analysis of products for selling potential, market fit, and profitability",
            "listing_optimization": "Optimization of product listings for better visibility, SEO, and conversion rates",
            "decision_consensus": "Multi-agent consensus building for important business decisions",
            "pricing_strategy": "Strategic pricing analysis and optimization recommendations",
            "market_research": "In-depth market research and competitive analysis",
        }

        return {
            "workflow_type": workflow_type,
            "participating_agents": config["participating_agents"],
            "example_keywords": config["keywords"][:5],  # First 5 keywords as examples
            "description": descriptions.get(
                workflow_type, f"Workflow for {workflow_type}"
            ),
        }


# Global detector instance
workflow_intent_detector = WorkflowIntentDetector()
