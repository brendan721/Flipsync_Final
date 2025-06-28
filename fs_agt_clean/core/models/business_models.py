"""
Business Strategy Models for FlipSync Executive UnifiedAgent
====================================================

This module defines data models for executive decision-making including
strategic planning, resource allocation, risk assessment, and business intelligence.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class DecisionType(str, Enum):
    """Types of executive decisions."""

    STRATEGIC_PLANNING = "strategic_planning"
    INVESTMENT = "investment"
    RESOURCE_ALLOCATION = "resource_allocation"
    RISK_MITIGATION = "risk_mitigation"
    BUDGET_APPROVAL = "budget_approval"
    MARKET_EXPANSION = "market_expansion"
    PRODUCT_LAUNCH = "product_launch"
    OPERATIONAL_CHANGE = "operational_change"


class RiskLevel(str, Enum):
    """Risk assessment levels."""

    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Priority(str, Enum):
    """Priority levels for initiatives."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class BusinessObjective(str, Enum):
    """Business objectives and goals."""

    REVENUE_GROWTH = "revenue_growth"
    PROFIT_MAXIMIZATION = "profit_maximization"
    MARKET_SHARE = "market_share"
    COST_REDUCTION = "cost_reduction"
    OPERATIONAL_EFFICIENCY = "operational_efficiency"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    BRAND_BUILDING = "brand_building"
    INNOVATION = "innovation"


@dataclass
class FinancialMetrics:
    """Financial performance metrics."""

    revenue: Decimal
    profit: Decimal
    margin: float
    roi: float
    cash_flow: Decimal
    expenses: Decimal
    currency: str = "USD"
    period: str = "monthly"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class RiskFactor:
    """Individual risk factor assessment."""

    factor_id: str
    name: str
    description: str
    probability: float  # 0.0 to 1.0
    impact: float  # 0.0 to 1.0
    risk_level: RiskLevel
    mitigation_strategies: List[str] = field(default_factory=list)
    owner: Optional[str] = None
    timeline: Optional[str] = None


@dataclass
class BusinessInitiative:
    """Business initiative or project."""

    initiative_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    objective: BusinessObjective = BusinessObjective.REVENUE_GROWTH
    priority: Priority = Priority.MEDIUM
    estimated_cost: Decimal = Decimal("0")
    estimated_revenue: Decimal = Decimal("0")
    estimated_roi: float = 0.0
    timeline_months: int = 12
    required_resources: Dict[str, Any] = field(default_factory=dict)
    success_metrics: List[str] = field(default_factory=list)
    risks: List[RiskFactor] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: str = "proposed"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ResourceAllocation:
    """Resource allocation recommendation."""

    allocation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    initiative_id: str = ""
    resource_type: str = ""  # "budget", "personnel", "time", "technology"
    amount: Union[Decimal, int, float] = 0
    unit: str = ""  # "USD", "hours", "people", "licenses"
    justification: str = ""
    priority_score: float = 0.0
    expected_impact: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class StrategicPlan:
    """Strategic business plan."""

    plan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    time_horizon: str = "1_year"  # "quarterly", "1_year", "3_year", "5_year"
    objectives: List[BusinessObjective] = field(default_factory=list)
    initiatives: List[BusinessInitiative] = field(default_factory=list)
    total_budget: Decimal = Decimal("0")
    expected_roi: float = 0.0
    key_metrics: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    risks: List[RiskFactor] = field(default_factory=list)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "draft"
    created_by: Optional[str] = None
    approved_by: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None


@dataclass
class InvestmentOpportunity:
    """Investment opportunity analysis."""

    opportunity_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    investment_type: str = ""  # "product", "market", "technology", "acquisition"
    required_investment: Decimal = Decimal("0")
    expected_return: Decimal = Decimal("0")
    payback_period_months: int = 12
    roi: float = 0.0
    npv: Decimal = Decimal("0")  # Net Present Value
    irr: float = 0.0  # Internal Rate of Return
    risk_assessment: RiskLevel = RiskLevel.MEDIUM
    market_size: Decimal = Decimal("0")
    competitive_advantage: List[str] = field(default_factory=list)
    success_probability: float = 0.5
    financial_projections: List[FinancialMetrics] = field(default_factory=list)
    risks: List[RiskFactor] = field(default_factory=list)
    recommendation: str = ""
    confidence_score: float = 0.0
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DecisionCriteria:
    """Multi-criteria decision analysis criteria."""

    criteria_name: str
    weight: float  # 0.0 to 1.0, sum of all weights should be 1.0
    description: str
    measurement_type: str = "quantitative"  # "quantitative" or "qualitative"
    scale_min: float = 0.0
    scale_max: float = 10.0
    higher_is_better: bool = True


@dataclass
class DecisionAlternative:
    """Alternative option in decision analysis."""

    alternative_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    scores: Dict[str, float] = field(default_factory=dict)  # criteria_name -> score
    weighted_score: float = 0.0
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)
    implementation_complexity: str = "medium"
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    timeline: str = ""
    risks: List[str] = field(default_factory=list)


@dataclass
class ExecutiveDecision:
    """Executive decision with analysis and recommendation."""

    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_type: DecisionType = DecisionType.STRATEGIC_PLANNING
    title: str = ""
    description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    criteria: List[DecisionCriteria] = field(default_factory=list)
    alternatives: List[DecisionAlternative] = field(default_factory=list)
    recommended_alternative: Optional[str] = None
    recommendation_reasoning: str = ""
    confidence_score: float = 0.0
    financial_impact: Optional[FinancialMetrics] = None
    risk_assessment: List[RiskFactor] = field(default_factory=list)
    implementation_plan: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)
    approval_required: bool = True
    urgency: Priority = Priority.MEDIUM
    stakeholders: List[str] = field(default_factory=list)
    created_by: str = "executive_agent"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    status: str = "pending"  # "pending", "approved", "rejected", "implemented"


@dataclass
class BusinessIntelligence:
    """Business intelligence data for decision making."""

    data_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data_type: str = ""  # "market", "financial", "operational", "competitive"
    source: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    trends: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence_level: float = 0.0
    data_quality: str = "high"  # "high", "medium", "low"
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    valid_until: Optional[datetime] = None


@dataclass
class PerformanceKPI:
    """Key Performance Indicator tracking."""

    kpi_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: str = ""  # "financial", "operational", "customer", "growth"
    current_value: float = 0.0
    target_value: float = 0.0
    unit: str = ""
    trend: str = "stable"  # "increasing", "decreasing", "stable"
    performance_status: str = (
        "on_track"  # "exceeding", "on_track", "at_risk", "failing"
    )
    historical_values: List[Dict[str, Any]] = field(default_factory=list)
    benchmark_value: Optional[float] = None
    owner: Optional[str] = None
    update_frequency: str = "monthly"
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# Utility functions for business model operations


def calculate_roi(investment: Decimal, return_amount: Decimal) -> float:
    """Calculate Return on Investment."""
    if investment == 0:
        return 0.0
    return float((return_amount - investment) / investment * 100)


def calculate_payback_period(investment: Decimal, monthly_return: Decimal) -> int:
    """Calculate payback period in months."""
    if monthly_return <= 0:
        return 999  # Never pays back
    return int(investment / monthly_return)


def calculate_npv(cash_flows: List[Decimal], discount_rate: float) -> Decimal:
    """Calculate Net Present Value."""
    npv = Decimal("0")
    for i, cash_flow in enumerate(cash_flows):
        npv += cash_flow / Decimal(str((1 + discount_rate) ** i))
    return npv


def assess_risk_level(probability: float, impact: float) -> RiskLevel:
    """Assess risk level based on probability and impact."""
    risk_score = probability * impact

    if risk_score >= 0.8:
        return RiskLevel.VERY_HIGH
    elif risk_score >= 0.6:
        return RiskLevel.HIGH
    elif risk_score >= 0.4:
        return RiskLevel.MEDIUM
    elif risk_score >= 0.2:
        return RiskLevel.LOW
    else:
        return RiskLevel.VERY_LOW


def calculate_weighted_score(
    scores: Dict[str, float], criteria: List[DecisionCriteria]
) -> float:
    """Calculate weighted score for decision alternative."""
    total_score = 0.0
    total_weight = 0.0

    for criterion in criteria:
        if criterion.criteria_name in scores:
            score = scores[criterion.criteria_name]
            # Normalize score to 0-1 scale
            normalized_score = (score - criterion.scale_min) / (
                criterion.scale_max - criterion.scale_min
            )
            if not criterion.higher_is_better:
                normalized_score = 1.0 - normalized_score

            total_score += normalized_score * criterion.weight
            total_weight += criterion.weight

    return total_score / total_weight if total_weight > 0 else 0.0


def create_financial_metrics(
    revenue: float, expenses: float, period: str = "monthly"
) -> FinancialMetrics:
    """Create financial metrics with calculated values."""
    revenue_decimal = Decimal(str(revenue))
    expenses_decimal = Decimal(str(expenses))
    profit = revenue_decimal - expenses_decimal
    margin = float(profit / revenue_decimal * 100) if revenue > 0 else 0.0
    roi = float(profit / expenses_decimal * 100) if expenses > 0 else 0.0

    return FinancialMetrics(
        revenue=revenue_decimal,
        profit=profit,
        margin=margin,
        roi=roi,
        cash_flow=profit,
        expenses=expenses_decimal,
        period=period,
    )


def prioritize_initiatives(
    initiatives: List[BusinessInitiative],
) -> List[BusinessInitiative]:
    """Prioritize business initiatives based on ROI and strategic importance."""

    def priority_score(initiative: BusinessInitiative) -> float:
        # Base score from ROI
        roi_score = min(initiative.estimated_roi / 100, 1.0)

        # Priority multiplier
        priority_multipliers = {
            Priority.CRITICAL: 2.0,
            Priority.HIGH: 1.5,
            Priority.MEDIUM: 1.0,
            Priority.LOW: 0.5,
        }
        priority_multiplier = priority_multipliers.get(initiative.priority, 1.0)

        # Risk adjustment (lower risk = higher score)
        risk_count = len(initiative.risks)
        risk_adjustment = max(0.5, 1.0 - (risk_count * 0.1))

        return roi_score * priority_multiplier * risk_adjustment

    return sorted(initiatives, key=priority_score, reverse=True)
