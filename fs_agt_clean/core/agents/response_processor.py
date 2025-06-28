"""
Shared UnifiedAgent Response Processing Utilities

This module provides standardized response processing functionality
to eliminate code duplication across conversational agents.
"""

import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from fs_agt_clean.agents.base_conversational_agent import UnifiedAgentResponse

logger = logging.getLogger(__name__)


class UnifiedAgentResponseProcessor:
    """
    Standardized response processing utilities for conversational agents.

    Eliminates code duplication across ContentUnifiedAgent, LogisticsUnifiedAgent, and ExecutiveUnifiedAgent
    by providing unified response processing, confidence calculation, and metadata handling.
    """

    # Confidence calculation weights by agent type
    CONFIDENCE_WEIGHTS = {
        "content": {
            "data_quality": 0.3,
            "seo_score": 0.25,
            "template_match": 0.2,
            "keyword_relevance": 0.15,
            "readability": 0.1,
        },
        "logistics": {
            "data_accuracy": 0.35,
            "cost_optimization": 0.25,
            "delivery_reliability": 0.2,
            "carrier_availability": 0.15,
            "route_efficiency": 0.05,
        },
        "executive": {
            "strategic_alignment": 0.4,
            "financial_impact": 0.3,
            "risk_assessment": 0.2,
            "implementation_feasibility": 0.1,
        },
    }

    # Approval thresholds by agent type and request type
    APPROVAL_THRESHOLDS = {
        "content": {
            "generate": {"auto_approve": 0.85, "requires_human": 0.6},
            "optimize": {"auto_approve": 0.8, "requires_human": 0.65},
            "template": {"auto_approve": 0.9, "requires_human": 0.7},
            "analyze": {"auto_approve": 0.75, "requires_human": 0.5},
        },
        "logistics": {
            "shipping": {"auto_approve": 0.8, "requires_human": 0.6},
            "inventory": {"auto_approve": 0.85, "requires_human": 0.65},
            "tracking": {"auto_approve": 0.9, "requires_human": 0.7},
            "optimization": {"auto_approve": 0.75, "requires_human": 0.55},
        },
        "executive": {
            "strategic": {"auto_approve": 0.7, "requires_human": 0.5},
            "financial": {"auto_approve": 0.75, "requires_human": 0.55},
            "investment": {"auto_approve": 0.8, "requires_human": 0.6},
            "resource": {"auto_approve": 0.85, "requires_human": 0.65},
        },
    }

    @classmethod
    def calculate_confidence(
        cls,
        agent_type: str,
        response_data: Dict[str, Any],
        metrics: Optional[Dict[str, float]] = None,
    ) -> float:
        """
        Calculate confidence score for agent response using standardized weights.

        Args:
            agent_type: Type of agent (content, logistics, executive)
            response_data: Response data containing quality metrics
            metrics: Optional custom metrics to include

        Returns:
            Confidence score between 0.0 and 1.0
        """
        try:
            weights = cls.CONFIDENCE_WEIGHTS.get(agent_type, {})
            if not weights:
                logger.warning(
                    f"No confidence weights defined for agent type: {agent_type}"
                )
                return 0.5  # Default moderate confidence

            total_score = 0.0
            total_weight = 0.0

            # Calculate weighted confidence based on available metrics
            for metric, weight in weights.items():
                value = None

                # Extract metric value from response_data
                if metric in response_data:
                    value = response_data[metric]
                elif metrics and metric in metrics:
                    value = metrics[metric]
                elif "scores" in response_data and metric in response_data["scores"]:
                    value = response_data["scores"][metric]

                if value is not None:
                    # Normalize value to 0-1 range if needed
                    normalized_value = cls._normalize_metric_value(value, metric)
                    total_score += normalized_value * weight
                    total_weight += weight

            # Calculate final confidence
            if total_weight > 0:
                confidence = total_score / total_weight
            else:
                # Fallback confidence calculation
                confidence = cls._calculate_fallback_confidence(
                    agent_type, response_data
                )

            # Ensure confidence is within valid range
            return max(0.0, min(1.0, confidence))

        except Exception as e:
            logger.error(f"Error calculating confidence for {agent_type}: {e}")
            return 0.5  # Default moderate confidence on error

    @classmethod
    def _normalize_metric_value(
        cls, value: Union[float, int, str], metric: str
    ) -> float:
        """Normalize metric value to 0-1 range."""
        try:
            if isinstance(value, str):
                # Handle string values (e.g., "high", "medium", "low")
                value_map = {"low": 0.3, "medium": 0.6, "high": 0.9}
                return value_map.get(value.lower(), 0.5)

            numeric_value = float(value)

            # Handle different metric scales
            if metric in ["seo_score", "readability", "quality_score"]:
                # Assume 0-100 scale
                return numeric_value / 100.0
            elif metric in ["cost_optimization", "delivery_reliability"]:
                # Assume percentage (0-1 or 0-100)
                return numeric_value if numeric_value <= 1.0 else numeric_value / 100.0
            else:
                # Assume already normalized (0-1)
                return numeric_value if numeric_value <= 1.0 else numeric_value / 100.0

        except (ValueError, TypeError):
            return 0.5  # Default value for invalid inputs

    @classmethod
    def _calculate_fallback_confidence(
        cls, agent_type: str, response_data: Dict[str, Any]
    ) -> float:
        """Calculate fallback confidence when standard metrics are unavailable."""
        try:
            # Basic heuristics based on response characteristics
            confidence_factors = []

            # Response completeness
            if "content" in response_data and response_data["content"]:
                content_length = len(str(response_data["content"]))
                if content_length > 100:
                    confidence_factors.append(0.8)
                elif content_length > 50:
                    confidence_factors.append(0.6)
                else:
                    confidence_factors.append(0.4)

            # Data availability
            data_fields = ["data", "analysis", "recommendations", "results"]
            available_data = sum(
                1
                for field in data_fields
                if field in response_data and response_data[field]
            )
            if available_data > 0:
                confidence_factors.append(0.5 + (available_data * 0.1))

            # UnifiedAgent-specific factors
            if agent_type == "content":
                if "keywords" in response_data and response_data["keywords"]:
                    confidence_factors.append(0.7)
            elif agent_type == "logistics":
                if (
                    "cost_savings" in response_data
                    or "efficiency_gain" in response_data
                ):
                    confidence_factors.append(0.75)
            elif agent_type == "executive":
                if "financial_impact" in response_data or "roi" in response_data:
                    confidence_factors.append(0.8)

            return (
                sum(confidence_factors) / len(confidence_factors)
                if confidence_factors
                else 0.5
            )

        except Exception as e:
            logger.error(f"Error in fallback confidence calculation: {e}")
            return 0.5

    @classmethod
    def determine_approval_requirements(
        cls,
        agent_type: str,
        request_type: str,
        confidence: float,
        response_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Determine approval requirements based on agent type, request type, and confidence.

        Args:
            agent_type: Type of agent
            request_type: Type of request being processed
            confidence: Calculated confidence score
            response_data: Optional response data for additional context

        Returns:
            Dictionary with approval requirements
        """
        try:
            # Get thresholds for agent and request type
            agent_thresholds = cls.APPROVAL_THRESHOLDS.get(agent_type, {})
            request_thresholds = agent_thresholds.get(
                request_type, {"auto_approve": 0.8, "requires_human": 0.6}
            )

            auto_approve_threshold = request_thresholds["auto_approve"]
            human_approval_threshold = request_thresholds["requires_human"]

            # Determine approval status
            if confidence >= auto_approve_threshold:
                requires_approval = False
                auto_approve = True
                escalation_required = False
                approval_reason = "High confidence - auto-approved"
            elif confidence >= human_approval_threshold:
                requires_approval = True
                auto_approve = False
                escalation_required = False
                approval_reason = "Medium confidence - requires human approval"
            else:
                requires_approval = True
                auto_approve = False
                escalation_required = True
                approval_reason = "Low confidence - requires escalation"

            # Check for special conditions that always require approval
            if response_data:
                high_impact_indicators = [
                    "budget_change",
                    "strategic_shift",
                    "policy_change",
                    "high_cost",
                    "high_risk",
                    "regulatory_impact",
                ]

                if any(
                    indicator in response_data for indicator in high_impact_indicators
                ):
                    requires_approval = True
                    auto_approve = False
                    approval_reason += " - High impact decision"

            return {
                "requires_approval": requires_approval,
                "auto_approve": auto_approve,
                "escalation_required": escalation_required,
                "approval_reason": approval_reason,
                "confidence_threshold_met": confidence >= auto_approve_threshold,
                "human_threshold_met": confidence >= human_approval_threshold,
            }

        except Exception as e:
            logger.error(f"Error determining approval requirements: {e}")
            return {
                "requires_approval": True,
                "auto_approve": False,
                "escalation_required": True,
                "approval_reason": "Error in approval determination - requires manual review",
                "confidence_threshold_met": False,
                "human_threshold_met": False,
            }

    @classmethod
    def format_standard_metadata(
        cls,
        agent_type: str,
        request_type: str,
        response_data: Dict[str, Any],
        confidence: float,
        processing_time: float,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Format standardized metadata for agent responses.

        Args:
            agent_type: Type of agent
            request_type: Type of request
            response_data: Response data
            confidence: Calculated confidence
            processing_time: Time taken to process request
            additional_metadata: Optional additional metadata

        Returns:
            Standardized metadata dictionary
        """
        try:
            # Get approval requirements
            approval_info = cls.determine_approval_requirements(
                agent_type, request_type, confidence, response_data
            )

            # Build standard metadata
            metadata = {
                "agent_type": agent_type,
                "request_type": request_type,
                "confidence": confidence,
                "processing_time": processing_time,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "requires_approval": approval_info["requires_approval"],
                "auto_approve": approval_info["auto_approve"],
                "escalation_required": approval_info["escalation_required"],
                "approval_reason": approval_info["approval_reason"],
                "data": response_data.get("metadata", {}),
                "performance_metrics": {
                    "response_time": processing_time,
                    "confidence_score": confidence,
                    "data_quality": response_data.get("quality_score", 0.5),
                },
            }

            # Add agent-specific metadata
            if agent_type == "content":
                metadata.update(
                    {
                        "seo_optimized": response_data.get("seo_score", 0) > 0.7,
                        "word_count": response_data.get("word_count", 0),
                        "readability_score": response_data.get(
                            "readability_score", 0.5
                        ),
                    }
                )
            elif agent_type == "logistics":
                metadata.update(
                    {
                        "cost_optimized": response_data.get("cost_savings", 0) > 0,
                        "delivery_optimized": response_data.get(
                            "delivery_improvement", 0
                        )
                        > 0,
                        "carrier_recommendations": len(
                            response_data.get("carriers", [])
                        ),
                    }
                )
            elif agent_type == "executive":
                metadata.update(
                    {
                        "financial_impact": response_data.get("financial_impact", 0),
                        "risk_level": response_data.get("risk_level", "medium"),
                        "strategic_alignment": response_data.get(
                            "strategic_alignment", 0.5
                        ),
                    }
                )

            # Merge additional metadata
            if additional_metadata:
                metadata.update(additional_metadata)

            return metadata

        except Exception as e:
            logger.error(f"Error formatting metadata: {e}")
            return {
                "agent_type": agent_type,
                "request_type": request_type,
                "confidence": confidence,
                "processing_time": processing_time,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "requires_approval": True,
                "error": str(e),
            }

    @classmethod
    def create_standardized_response(
        cls,
        content: str,
        agent_type: str,
        request_type: str,
        response_data: Dict[str, Any],
        processing_start_time: float,
        agent_id: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None,
    ) -> UnifiedAgentResponse:
        """
        Create a standardized UnifiedAgentResponse with calculated confidence and metadata.

        Args:
            content: Response content
            agent_type: Type of agent
            request_type: Type of request
            response_data: Response data for confidence calculation
            processing_start_time: Start time for processing duration calculation
            agent_id: Optional agent identifier
            additional_metadata: Optional additional metadata

        Returns:
            Standardized UnifiedAgentResponse object
        """
        try:
            # Calculate processing time
            processing_time = time.time() - processing_start_time

            # Calculate confidence
            confidence = cls.calculate_confidence(agent_type, response_data)

            # Format metadata
            metadata = cls.format_standard_metadata(
                agent_type=agent_type,
                request_type=request_type,
                response_data=response_data,
                confidence=confidence,
                processing_time=processing_time,
                additional_metadata=additional_metadata,
            )

            # Add agent ID if provided
            if agent_id:
                metadata["agent_id"] = agent_id

            return UnifiedAgentResponse(
                content=content,
                agent_type=agent_type,
                confidence=confidence,
                response_time=processing_time,
                metadata=metadata,
            )

        except Exception as e:
            logger.error(f"Error creating standardized response: {e}")
            # Return error response
            return UnifiedAgentResponse(
                content=f"Error processing request: {str(e)}",
                agent_type=agent_type,
                confidence=0.0,
                response_time=time.time() - processing_start_time,
                metadata={
                    "error": str(e),
                    "requires_approval": True,
                    "agent_type": agent_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
