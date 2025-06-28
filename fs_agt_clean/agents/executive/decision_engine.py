import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List

from fs_agt_clean.core.models.business_models import (
    BusinessObjective,
    DecisionAlternative,
    DecisionCriteria,
    DecisionType,
    ExecutiveDecision,
    FinancialMetrics,
    Priority,
    RiskFactor,
    RiskLevel,
    assess_risk_level,
    calculate_weighted_score,
)

logger = logging.getLogger(__name__)

"\nDecision engine module for the FlipSync UnifiedAgentic System.\nHandles decision-making processes and strategy application.\n"


@dataclass
class Decision:
    """Represents a decision made by the engine"""

    action: str
    confidence: float
    context: Dict[str, Any]
    timestamp: datetime
    reasoning: List[str]


@dataclass
class DecisionContext:
    """Context information for decision making."""

    business_objectives: List[BusinessObjective]
    available_budget: Decimal
    time_constraints: str
    risk_tolerance: RiskLevel
    strategic_priorities: List[str]
    current_performance: Dict[str, float]
    market_conditions: Dict[str, Any]
    competitive_landscape: Dict[str, Any]


@dataclass
class DecisionRecommendation:
    """Decision recommendation with detailed analysis."""

    recommended_alternative: DecisionAlternative
    confidence_score: float
    reasoning: str
    risk_assessment: List[RiskFactor]
    implementation_steps: List[str]
    success_probability: float
    expected_outcomes: Dict[str, Any]
    monitoring_metrics: List[str]


class DecisionEngine:
    """
    Decision engine that:
    - Evaluates actions based on context
    - Applies strategies
    - Maintains decision history
    - Provides reasoning for decisions
    """

    def __init__(self, min_confidence: float = 0.7):
        self.min_confidence = min_confidence
        self.strategies: Dict[str, Dict[str, Any]] = {}
        self.decision_history: List[Decision] = []
        self.max_history = 1000

    async def add_strategy(self, name: str, strategy: Dict[str, Any]) -> None:
        """Add a new decision strategy"""
        self.strategies[name] = {
            "config": strategy,
            "added": datetime.utcnow(),
            "usage_count": 0,
        }

    async def make_decision(
        self,
        context: Dict[str, Any],
        actions: List[str],
        memory_context: Dict[str, Any],
    ) -> Decision:
        """Make a decision based on context and available actions"""
        if not actions:
            raise Exception("No actions provided")
        scores = await self._evaluate_actions(actions, context, memory_context)
        action = await self._select_best_action(scores)
        decision = Decision(
            action=action,
            confidence=scores[action],
            context=context,
            timestamp=datetime.utcnow(),
            reasoning=[f"Selected {action} with confidence {scores[action]:.2f}"],
        )
        self.decision_history.append(decision)
        if len(self.decision_history) > self.max_history:
            self.decision_history = self.decision_history[-self.max_history :]
        return decision

    async def _evaluate_actions(
        self,
        actions: List[str],
        context: Dict[str, Any],
        memory_context: Dict[str, Any],
    ) -> Dict[str, float]:
        """Evaluate all possible actions"""
        scores = {}
        for action in actions:
            strategy_score = await self._apply_strategies(action, context)
            history_score = await self._evaluate_history(action, context)
            memory_score = await self._evaluate_memory_context(action, memory_context)
            scores[action] = (
                0.4 * strategy_score + 0.3 * history_score + 0.3 * memory_score
            )
        return scores

    async def _apply_strategies(self, action: str, context: Dict[str, Any]) -> float:
        """Apply all strategies to evaluate an action"""
        if not self.strategies:
            return 0.7
        scores = []
        for strategy in self.strategies.values():
            config = strategy["config"]
            if "rules" in config:
                confidence = config["rules"].get(
                    "confidence_threshold", self.min_confidence
                )
                scores.append(confidence)
            if "weights" in config:
                weighted_score = 0
                total_weight = 0
                for key, weight in config["weights"].items():
                    if key in context:
                        weighted_score += weight
                        total_weight += weight
                if total_weight > 0:
                    scores.append(weighted_score / total_weight)
            strategy["usage_count"] += 1
        return sum(scores) / len(scores) if scores else self.min_confidence

    async def _evaluate_history(self, action: str, context: Dict[str, Any]) -> float:
        """Evaluate action based on historical performance"""
        if not self.decision_history:
            return self.min_confidence
        relevant_decisions = []
        for decision in self.decision_history:
            if decision.action == action:
                similarity = await self._context_similarity(context, decision.context)
                if similarity > 0.5:
                    relevant_decisions.append(decision)
        if not relevant_decisions:
            return self.min_confidence
        return sum((d.confidence for d in relevant_decisions)) / len(relevant_decisions)

    async def _evaluate_memory_context(
        self, action: str, memory_context: Dict[str, Any]
    ) -> float:
        """Evaluate action based on memory context"""
        if not memory_context or "experiences" not in memory_context:
            return self.min_confidence
        relevant_experiences = [
            exp for exp in memory_context["experiences"] if exp["action"] == action
        ]
        if not relevant_experiences:
            return self.min_confidence
        success_rate = sum((1 for exp in relevant_experiences if exp["success"])) / len(
            relevant_experiences
        )
        return (
            success_rate if success_rate >= self.min_confidence else self.min_confidence
        )

    async def _select_best_action(self, scores: Dict[str, float]) -> str:
        """Select the action with the highest score"""
        if not scores:
            raise ValueError("No action scores provided")
        return max(scores.items(), key=lambda x: x[1])[0]

    async def _context_similarity(
        self, context1: Dict[str, Any], context2: Dict[str, Any]
    ) -> float:
        """Calculate similarity between two contexts"""
        common_keys = set(context1.keys()) & set(context2.keys())
        if not common_keys:
            return 0.0
        matches = sum((1 for k in common_keys if context1[k] == context2[k]))
        return matches / len(common_keys)

    async def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of the decision engine's performance"""
        if not self.decision_history:
            return {
                "total_decisions": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "top_strategies": [],
            }

        total_decisions = len(self.decision_history)
        avg_confidence = (
            sum(d.confidence for d in self.decision_history) / total_decisions
        )

        # Get top strategies by usage count
        sorted_strategies = sorted(
            self.strategies.items(), key=lambda x: x[1]["usage_count"], reverse=True
        )
        top_strategies = [s[0] for s in sorted_strategies[:5]]  # Top 5 strategies

        return {
            "total_decisions": total_decisions,
            "success_rate": avg_confidence,  # Using confidence as proxy for success
            "avg_confidence": avg_confidence,
            "top_strategies": top_strategies,
        }


class MultiCriteriaDecisionEngine:
    """Advanced decision engine using multiple criteria analysis."""

    def __init__(self):
        """Initialize the decision engine."""
        # Standard decision criteria for business decisions
        self.standard_criteria = {
            "financial_return": DecisionCriteria(
                criteria_name="financial_return",
                weight=0.25,
                description="Expected financial return (ROI)",
                measurement_type="quantitative",
                scale_min=0.0,
                scale_max=100.0,
                higher_is_better=True,
            ),
            "risk_level": DecisionCriteria(
                criteria_name="risk_level",
                weight=0.20,
                description="Overall risk assessment",
                measurement_type="qualitative",
                scale_min=1.0,
                scale_max=5.0,
                higher_is_better=False,  # Lower risk is better
            ),
            "strategic_alignment": DecisionCriteria(
                criteria_name="strategic_alignment",
                weight=0.20,
                description="Alignment with business strategy",
                measurement_type="qualitative",
                scale_min=1.0,
                scale_max=10.0,
                higher_is_better=True,
            ),
            "implementation_complexity": DecisionCriteria(
                criteria_name="implementation_complexity",
                weight=0.15,
                description="Complexity of implementation",
                measurement_type="qualitative",
                scale_min=1.0,
                scale_max=5.0,
                higher_is_better=False,  # Lower complexity is better
            ),
            "time_to_value": DecisionCriteria(
                criteria_name="time_to_value",
                weight=0.10,
                description="Time to realize value",
                measurement_type="quantitative",
                scale_min=1.0,
                scale_max=24.0,  # months
                higher_is_better=False,  # Faster is better
            ),
            "resource_requirements": DecisionCriteria(
                criteria_name="resource_requirements",
                weight=0.10,
                description="Required resources",
                measurement_type="quantitative",
                scale_min=1.0,
                scale_max=10.0,
                higher_is_better=False,  # Lower requirements are better
            ),
        }

        logger.info("Multi-criteria decision engine initialized")

    async def analyze_decision(
        self,
        decision_type: DecisionType,
        alternatives: List[DecisionAlternative],
        context: DecisionContext,
        custom_criteria: List[DecisionCriteria] = None,
    ) -> DecisionRecommendation:
        """
        Analyze a decision using multi-criteria analysis.

        Args:
            decision_type: Type of decision being made
            alternatives: List of decision alternatives
            context: Decision context and constraints
            custom_criteria: Optional custom criteria (overrides standard)

        Returns:
            DecisionRecommendation with analysis and recommendation
        """
        try:
            # Use custom criteria or adapt standard criteria based on decision type
            criteria = custom_criteria or self._get_criteria_for_decision_type(
                decision_type, context
            )

            # Score all alternatives against criteria
            scored_alternatives = await self._score_alternatives(
                alternatives, criteria, context
            )

            # Select best alternative
            best_alternative = self._select_best_alternative(scored_alternatives)

            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                scored_alternatives, context
            )

            # Generate reasoning
            reasoning = self._generate_reasoning(
                best_alternative, scored_alternatives, criteria
            )

            # Assess risks
            risk_assessment = await self._assess_decision_risks(
                best_alternative, context
            )

            # Generate implementation steps
            implementation_steps = self._generate_implementation_steps(
                best_alternative, decision_type
            )

            # Calculate success probability
            success_probability = self._calculate_success_probability(
                best_alternative, context
            )

            # Define expected outcomes
            expected_outcomes = self._define_expected_outcomes(
                best_alternative, context
            )

            # Define monitoring metrics
            monitoring_metrics = self._define_monitoring_metrics(
                best_alternative, decision_type
            )

            return DecisionRecommendation(
                recommended_alternative=best_alternative,
                confidence_score=confidence_score,
                reasoning=reasoning,
                risk_assessment=risk_assessment,
                implementation_steps=implementation_steps,
                success_probability=success_probability,
                expected_outcomes=expected_outcomes,
                monitoring_metrics=monitoring_metrics,
            )

        except Exception as e:
            logger.error(f"Error in decision analysis: {e}")
            # Return safe recommendation
            return DecisionRecommendation(
                recommended_alternative=(
                    alternatives[0] if alternatives else DecisionAlternative()
                ),
                confidence_score=0.1,
                reasoning=f"Error in analysis: {e}. Recommend further review.",
                risk_assessment=[],
                implementation_steps=[
                    "Conduct detailed analysis",
                    "Seek expert consultation",
                ],
                success_probability=0.5,
                expected_outcomes={"status": "requires_review"},
                monitoring_metrics=["decision_outcome", "implementation_progress"],
            )

    def _get_criteria_for_decision_type(
        self, decision_type: DecisionType, context: DecisionContext
    ) -> List[DecisionCriteria]:
        """Get appropriate criteria based on decision type."""
        base_criteria = list(self.standard_criteria.values())

        # Adjust weights based on decision type
        if decision_type == DecisionType.INVESTMENT:
            # Emphasize financial return and risk for investments
            for criterion in base_criteria:
                if criterion.criteria_name == "financial_return":
                    criterion.weight = 0.35
                elif criterion.criteria_name == "risk_level":
                    criterion.weight = 0.25
                elif criterion.criteria_name == "strategic_alignment":
                    criterion.weight = 0.15

        elif decision_type == DecisionType.STRATEGIC_PLANNING:
            # Emphasize strategic alignment and long-term value
            for criterion in base_criteria:
                if criterion.criteria_name == "strategic_alignment":
                    criterion.weight = 0.30
                elif criterion.criteria_name == "financial_return":
                    criterion.weight = 0.20
                elif criterion.criteria_name == "time_to_value":
                    criterion.weight = 0.15

        # Normalize weights to sum to 1.0
        total_weight = sum(c.weight for c in base_criteria)
        for criterion in base_criteria:
            criterion.weight = criterion.weight / total_weight

        return base_criteria

    async def _score_alternatives(
        self,
        alternatives: List[DecisionAlternative],
        criteria: List[DecisionCriteria],
        context: DecisionContext,
    ) -> List[DecisionAlternative]:
        """Score all alternatives against criteria."""
        scored_alternatives = []

        for alternative in alternatives:
            # Calculate scores for missing criteria
            enhanced_scores = alternative.scores.copy()

            # Auto-score based on available data
            enhanced_scores = await self._auto_score_alternative(
                alternative, criteria, context, enhanced_scores
            )

            # Calculate weighted score
            weighted_score = calculate_weighted_score(enhanced_scores, criteria)

            # Create enhanced alternative
            enhanced_alternative = DecisionAlternative(
                alternative_id=alternative.alternative_id,
                name=alternative.name,
                description=alternative.description,
                scores=enhanced_scores,
                weighted_score=weighted_score,
                pros=alternative.pros,
                cons=alternative.cons,
                implementation_complexity=alternative.implementation_complexity,
                resource_requirements=alternative.resource_requirements,
                timeline=alternative.timeline,
                risks=alternative.risks,
            )

            scored_alternatives.append(enhanced_alternative)

        return scored_alternatives

    async def _auto_score_alternative(
        self,
        alternative: DecisionAlternative,
        criteria: List[DecisionCriteria],
        context: DecisionContext,
        existing_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """Automatically score alternative based on available data."""
        scores = existing_scores.copy()

        # Score implementation complexity
        if "implementation_complexity" not in scores:
            complexity_map = {"low": 2.0, "medium": 3.0, "high": 4.0, "very_high": 5.0}
            scores["implementation_complexity"] = complexity_map.get(
                alternative.implementation_complexity, 3.0
            )

        # Score risk level based on number and severity of risks
        if "risk_level" not in scores:
            risk_score = min(1.0 + len(alternative.risks) * 0.5, 5.0)
            scores["risk_level"] = risk_score

        # Score strategic alignment based on description keywords
        if "strategic_alignment" not in scores:
            strategic_keywords = [
                "growth",
                "efficiency",
                "innovation",
                "competitive",
                "market",
            ]
            keyword_count = sum(
                1
                for keyword in strategic_keywords
                if keyword in alternative.description.lower()
            )
            scores["strategic_alignment"] = min(5.0 + keyword_count, 10.0)

        # Score time to value based on timeline
        if "time_to_value" not in scores and alternative.timeline:
            # Extract months from timeline string
            timeline_months = self._extract_timeline_months(alternative.timeline)
            scores["time_to_value"] = min(timeline_months, 24.0)

        # Score resource requirements
        if "resource_requirements" not in scores:
            # Simple scoring based on resource complexity
            resource_count = len(alternative.resource_requirements)
            scores["resource_requirements"] = min(1.0 + resource_count, 10.0)

        return scores

    def _extract_timeline_months(self, timeline: str) -> float:
        """Extract timeline in months from timeline string."""
        timeline_lower = timeline.lower()

        if "week" in timeline_lower:
            # Extract weeks and convert to months
            import re

            weeks = re.findall(r"\d+", timeline_lower)
            if weeks:
                return float(weeks[0]) / 4.0
        elif "month" in timeline_lower:
            import re

            months = re.findall(r"\d+", timeline_lower)
            if months:
                return float(months[0])
        elif "year" in timeline_lower:
            import re

            years = re.findall(r"\d+", timeline_lower)
            if years:
                return float(years[0]) * 12.0

        return 6.0  # Default to 6 months

    def _select_best_alternative(
        self, alternatives: List[DecisionAlternative]
    ) -> DecisionAlternative:
        """Select the best alternative based on weighted scores."""
        if not alternatives:
            return DecisionAlternative()

        return max(alternatives, key=lambda alt: alt.weighted_score)

    def _calculate_confidence_score(
        self, alternatives: List[DecisionAlternative], context: DecisionContext
    ) -> float:
        """Calculate confidence score for the recommendation."""
        if len(alternatives) < 2:
            return 0.5  # Low confidence with only one option

        # Get scores
        scores = [alt.weighted_score for alt in alternatives]

        # Calculate score spread
        max_score = max(scores)
        second_max = sorted(scores, reverse=True)[1]
        score_spread = max_score - second_max

        # Higher spread = higher confidence
        base_confidence = min(score_spread * 2, 0.8)

        # Adjust based on data quality
        data_quality_bonus = 0.1 if len(alternatives) >= 3 else 0.0

        # Adjust based on risk tolerance alignment
        risk_alignment_bonus = (
            0.1 if context.risk_tolerance in [RiskLevel.LOW, RiskLevel.MEDIUM] else 0.0
        )

        return min(base_confidence + data_quality_bonus + risk_alignment_bonus, 1.0)

    def _generate_reasoning(
        self,
        best_alternative: DecisionAlternative,
        all_alternatives: List[DecisionAlternative],
        criteria: List[DecisionCriteria],
    ) -> str:
        """Generate human-readable reasoning for the recommendation."""
        reasoning_parts = []

        # Overall recommendation
        reasoning_parts.append(
            f"Recommending '{best_alternative.name}' based on multi-criteria analysis."
        )

        # Score comparison
        if len(all_alternatives) > 1:
            scores = [alt.weighted_score for alt in all_alternatives]
            avg_score = statistics.mean(scores)
            reasoning_parts.append(
                f"This alternative scored {best_alternative.weighted_score:.2f} "
                f"compared to an average of {avg_score:.2f} across all options."
            )

        # Key strengths
        top_criteria = sorted(criteria, key=lambda c: c.weight, reverse=True)[:3]
        strengths = []
        for criterion in top_criteria:
            if criterion.criteria_name in best_alternative.scores:
                score = best_alternative.scores[criterion.criteria_name]
                if score >= criterion.scale_max * 0.7:  # High score
                    strengths.append(f"strong {criterion.description.lower()}")

        if strengths:
            reasoning_parts.append(f"Key strengths include {', '.join(strengths)}.")

        # Risk considerations
        if best_alternative.risks:
            reasoning_parts.append(
                f"Consider {len(best_alternative.risks)} identified risks during implementation."
            )

        return " ".join(reasoning_parts)

    async def _assess_decision_risks(
        self, alternative: DecisionAlternative, context: DecisionContext
    ) -> List[RiskFactor]:
        """Assess risks for the recommended decision."""
        risks = []

        # Convert string risks to RiskFactor objects
        for i, risk_desc in enumerate(alternative.risks):
            risk_factor = RiskFactor(
                factor_id=f"risk_{i}",
                name=f"Risk {i+1}",
                description=risk_desc,
                probability=0.3,  # Default probability
                impact=0.5,  # Default impact
                risk_level=assess_risk_level(0.3, 0.5),
                mitigation_strategies=[f"Monitor and mitigate {risk_desc.lower()}"],
            )
            risks.append(risk_factor)

        return risks

    def _generate_implementation_steps(
        self, alternative: DecisionAlternative, decision_type: DecisionType
    ) -> List[str]:
        """Generate implementation steps for the recommended alternative."""
        steps = [
            "Secure stakeholder approval and buy-in",
            "Allocate required resources and budget",
            "Develop detailed implementation plan",
        ]

        # Add decision-type specific steps
        if decision_type == DecisionType.INVESTMENT:
            steps.extend(
                [
                    "Conduct final due diligence",
                    "Execute investment agreements",
                    "Establish monitoring and reporting framework",
                ]
            )
        elif decision_type == DecisionType.STRATEGIC_PLANNING:
            steps.extend(
                [
                    "Communicate strategy to organization",
                    "Align departmental plans with strategy",
                    "Establish KPIs and measurement systems",
                ]
            )

        steps.append("Monitor progress and adjust as needed")

        return steps

    def _calculate_success_probability(
        self, alternative: DecisionAlternative, context: DecisionContext
    ) -> float:
        """Calculate probability of successful implementation."""
        base_probability = 0.7

        # Adjust based on complexity
        complexity_map = {"low": 0.1, "medium": 0.0, "high": -0.1, "very_high": -0.2}
        complexity_adjustment = complexity_map.get(
            alternative.implementation_complexity, 0.0
        )

        # Adjust based on risk count
        risk_adjustment = -len(alternative.risks) * 0.05

        # Adjust based on weighted score
        score_adjustment = (alternative.weighted_score - 0.5) * 0.2

        return max(
            0.1,
            min(
                0.95,
                base_probability
                + complexity_adjustment
                + risk_adjustment
                + score_adjustment,
            ),
        )

    def _define_expected_outcomes(
        self, alternative: DecisionAlternative, context: DecisionContext
    ) -> Dict[str, Any]:
        """Define expected outcomes from implementing the alternative."""
        outcomes = {
            "implementation_timeline": alternative.timeline or "6-12 months",
            "resource_utilization": "As planned",
            "risk_mitigation": "Managed within acceptable levels",
        }

        # Add financial outcomes if available
        if "financial_return" in alternative.scores:
            outcomes["expected_roi"] = f"{alternative.scores['financial_return']:.1f}%"

        # Add strategic outcomes
        if "strategic_alignment" in alternative.scores:
            alignment_score = alternative.scores["strategic_alignment"]
            if alignment_score >= 8.0:
                outcomes["strategic_impact"] = "High alignment with business objectives"
            elif alignment_score >= 6.0:
                outcomes["strategic_impact"] = (
                    "Moderate alignment with business objectives"
                )
            else:
                outcomes["strategic_impact"] = "Limited strategic alignment"

        return outcomes

    def _define_monitoring_metrics(
        self, alternative: DecisionAlternative, decision_type: DecisionType
    ) -> List[str]:
        """Define metrics for monitoring implementation success."""
        base_metrics = [
            "Implementation progress (%)",
            "Budget utilization (%)",
            "Timeline adherence",
        ]

        # Add decision-type specific metrics
        if decision_type == DecisionType.INVESTMENT:
            base_metrics.extend(
                [
                    "Return on investment (%)",
                    "Payback period (months)",
                    "Net present value",
                ]
            )
        elif decision_type == DecisionType.STRATEGIC_PLANNING:
            base_metrics.extend(
                [
                    "Strategic objective completion (%)",
                    "KPI achievement",
                    "Stakeholder satisfaction",
                ]
            )

        return base_metrics
