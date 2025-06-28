"""
Advanced Decision Engine for FlipSync Executive UnifiedAgents.

This module provides sophisticated decision-making capabilities including
multi-criteria analysis, uncertainty handling, and explainable AI features.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID, uuid4

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DecisionCriteria:
    """Represents a decision criterion with weight and constraints."""

    name: str
    weight: float
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    is_maximizing: bool = True
    description: str = ""


@dataclass
class DecisionOption:
    """Represents a decision option with scores and metadata."""

    option_id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.5
    risk_level: str = "medium"


@dataclass
class DecisionResult:
    """Represents the result of a decision analysis."""

    selected_option: DecisionOption
    all_options: List[DecisionOption]
    criteria: List[DecisionCriteria]
    total_score: float
    confidence: float
    explanation: str
    decision_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    reasoning_steps: List[str] = field(default_factory=list)


class AdvancedDecisionEngine:
    """
    Advanced decision engine with multi-criteria analysis capabilities.

    Features:
    - Multi-criteria decision analysis (MCDA)
    - Uncertainty handling
    - Risk assessment
    - Explainable AI decisions
    - Learning from past decisions
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Advanced Decision Engine.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.decision_history: List[DecisionResult] = []
        self.criteria_weights: Dict[str, float] = {}
        self.performance_metrics: Dict[str, float] = {}

        logger.info("AdvancedDecisionEngine initialized")

    def add_criteria(self, criteria: List[DecisionCriteria]) -> None:
        """
        Add decision criteria to the engine.

        Args:
            criteria: List of decision criteria
        """
        for criterion in criteria:
            self.criteria_weights[criterion.name] = criterion.weight

        logger.info(f"Added {len(criteria)} decision criteria")

    def normalize_scores(
        self, options: List[DecisionOption], criteria: List[DecisionCriteria]
    ) -> List[DecisionOption]:
        """
        Normalize scores across all options and criteria.

        Args:
            options: List of decision options
            criteria: List of decision criteria

        Returns:
            List of options with normalized scores
        """
        normalized_options = []

        for option in options:
            normalized_option = DecisionOption(
                option_id=option.option_id,
                name=option.name,
                description=option.description,
                metadata=option.metadata.copy(),
                confidence=option.confidence,
                risk_level=option.risk_level,
            )

            for criterion in criteria:
                if criterion.name in option.scores:
                    raw_score = option.scores[criterion.name]

                    # Normalize based on min/max values
                    if (
                        criterion.min_value is not None
                        and criterion.max_value is not None
                    ):
                        normalized_score = (raw_score - criterion.min_value) / (
                            criterion.max_value - criterion.min_value
                        )
                    else:
                        # Use z-score normalization
                        all_scores = [
                            opt.scores.get(criterion.name, 0) for opt in options
                        ]
                        mean_score = np.mean(all_scores)
                        std_score = np.std(all_scores)

                        if std_score > 0:
                            normalized_score = (raw_score - mean_score) / std_score
                        else:
                            normalized_score = 0.5

                    # Invert if minimizing
                    if not criterion.is_maximizing:
                        normalized_score = 1.0 - normalized_score

                    normalized_option.scores[criterion.name] = max(
                        0, min(1, normalized_score)
                    )
                else:
                    normalized_option.scores[criterion.name] = 0.0

            normalized_options.append(normalized_option)

        return normalized_options

    def calculate_weighted_scores(
        self, options: List[DecisionOption], criteria: List[DecisionCriteria]
    ) -> List[Tuple[DecisionOption, float]]:
        """
        Calculate weighted scores for all options.

        Args:
            options: List of decision options
            criteria: List of decision criteria

        Returns:
            List of tuples (option, weighted_score)
        """
        scored_options = []

        for option in options:
            total_score = 0.0
            total_weight = 0.0

            for criterion in criteria:
                if criterion.name in option.scores:
                    score = option.scores[criterion.name]
                    weight = criterion.weight
                    total_score += score * weight
                    total_weight += weight

            # Normalize by total weight
            if total_weight > 0:
                final_score = total_score / total_weight
            else:
                final_score = 0.0

            scored_options.append((option, final_score))

        return scored_options

    def assess_risk(self, option: DecisionOption) -> Tuple[str, float]:
        """
        Assess risk level for a decision option.

        Args:
            option: Decision option to assess

        Returns:
            Tuple of (risk_level, risk_score)
        """
        risk_factors = []

        # Confidence-based risk
        confidence_risk = 1.0 - option.confidence
        risk_factors.append(confidence_risk)

        # Variance in scores
        if option.scores:
            score_variance = np.var(list(option.scores.values()))
            risk_factors.append(score_variance)

        # Calculate overall risk
        overall_risk = np.mean(risk_factors) if risk_factors else 0.5

        if overall_risk < 0.3:
            risk_level = "low"
        elif overall_risk < 0.7:
            risk_level = "medium"
        else:
            risk_level = "high"

        return risk_level, overall_risk

    async def make_decision(
        self,
        options: List[DecisionOption],
        criteria: List[DecisionCriteria],
        context: Optional[Dict[str, Any]] = None,
    ) -> DecisionResult:
        """
        Make a decision using multi-criteria analysis.

        Args:
            options: List of decision options
            criteria: List of decision criteria
            context: Optional context information

        Returns:
            Decision result with selected option and explanation
        """
        if not options:
            raise ValueError("No options provided for decision making")

        if not criteria:
            raise ValueError("No criteria provided for decision making")

        # Normalize scores
        normalized_options = self.normalize_scores(options, criteria)

        # Calculate weighted scores
        scored_options = self.calculate_weighted_scores(normalized_options, criteria)

        # Sort by score (highest first)
        scored_options.sort(key=lambda x: x[1], reverse=True)

        # Select best option
        best_option, best_score = scored_options[0]

        # Assess risk
        risk_level, risk_score = self.assess_risk(best_option)
        best_option.risk_level = risk_level

        # Generate explanation
        explanation = self._generate_explanation(best_option, criteria, scored_options)

        # Create decision result
        result = DecisionResult(
            selected_option=best_option,
            all_options=[opt for opt, _ in scored_options],
            criteria=criteria,
            total_score=best_score,
            confidence=best_option.confidence,
            explanation=explanation,
            reasoning_steps=self._generate_reasoning_steps(
                best_option, criteria, scored_options
            ),
        )

        # Store in history
        self.decision_history.append(result)

        logger.info(f"Decision made: {best_option.name} (score: {best_score:.3f})")

        return result

    def _generate_explanation(
        self,
        selected_option: DecisionOption,
        criteria: List[DecisionCriteria],
        scored_options: List[Tuple[DecisionOption, float]],
    ) -> str:
        """Generate human-readable explanation for the decision."""
        explanation_parts = [
            f"Selected option: {selected_option.name}",
            f"Total score: {scored_options[0][1]:.3f}",
            f"Risk level: {selected_option.risk_level}",
            "",
            "Key factors:",
        ]

        # Add top criteria contributions
        for criterion in criteria[:3]:  # Top 3 criteria
            if criterion.name in selected_option.scores:
                score = selected_option.scores[criterion.name]
                explanation_parts.append(
                    f"- {criterion.name}: {score:.3f} (weight: {criterion.weight:.2f})"
                )

        return "\n".join(explanation_parts)

    def _generate_reasoning_steps(
        self,
        selected_option: DecisionOption,
        criteria: List[DecisionCriteria],
        scored_options: List[Tuple[DecisionOption, float]],
    ) -> List[str]:
        """Generate step-by-step reasoning for the decision."""
        steps = [
            f"Evaluated {len(scored_options)} options against {len(criteria)} criteria",
            f"Normalized scores across all criteria",
            f"Applied weighted scoring with criteria weights",
            f"Selected highest scoring option: {selected_option.name}",
            f"Assessed risk level: {selected_option.risk_level}",
        ]

        return steps
