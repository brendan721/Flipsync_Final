"""
Database Models for Executive Agent
==================================

SQLAlchemy models for storing executive decisions, strategic plans,
resource allocations, and risk assessments.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from fs_agt_clean.database.models.base import Base


class ExecutiveDecisionModel(Base):
    """Executive decision records."""

    __tablename__ = "executive_decisions"

    id = Column(Integer, primary_key=True, index=True)
    decision_id = Column(
        String(50), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    decision_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Decision context and analysis
    context = Column(JSON)
    criteria = Column(JSON)  # List of decision criteria
    alternatives = Column(JSON)  # List of decision alternatives
    recommended_alternative = Column(String(100))
    recommendation_reasoning = Column(Text)
    confidence_score = Column(Numeric(3, 2))

    # Financial impact
    financial_impact = Column(JSON)

    # Risk assessment
    risk_assessment = Column(JSON)  # List of risk factors

    # Implementation
    implementation_plan = Column(JSON)  # List of implementation steps
    success_metrics = Column(JSON)  # List of success metrics

    # Approval workflow
    approval_required = Column(Boolean, default=True)
    urgency = Column(String(20), default="medium")
    stakeholders = Column(JSON)  # List of stakeholders

    # Status tracking
    status = Column(String(20), default="pending", index=True)
    created_by = Column(String(100), default="executive_agent")
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(String(100))

    # Indexes for performance
    __table_args__ = (
        Index("idx_executive_decisions_type_status", "decision_type", "status"),
        Index("idx_executive_decisions_created_at", "created_at"),
        Index("idx_executive_decisions_urgency", "urgency"),
    )


class StrategicPlanModel(Base):
    """Strategic business plans."""

    __tablename__ = "strategic_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(
        String(50), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    name = Column(String(200), nullable=False)
    description = Column(Text)
    time_horizon = Column(
        String(20), nullable=False
    )  # "quarterly", "1_year", "3_year", "5_year"

    # Strategic elements
    objectives = Column(JSON)  # List of business objectives
    initiatives = Column(JSON)  # List of business initiatives
    total_budget = Column(Numeric(15, 2))
    expected_roi = Column(Numeric(5, 2))

    # Success criteria
    key_metrics = Column(JSON)  # List of key metrics
    success_criteria = Column(JSON)  # List of success criteria

    # Risk and milestones
    risks = Column(JSON)  # List of risk factors
    milestones = Column(JSON)  # List of milestones

    # Status and approval
    status = Column(String(20), default="draft", index=True)
    created_by = Column(String(100))
    approved_by = Column(String(100))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    approved_at = Column(DateTime(timezone=True))

    # Indexes
    __table_args__ = (
        Index("idx_strategic_plans_horizon_status", "time_horizon", "status"),
        Index("idx_strategic_plans_created_at", "created_at"),
    )


class BusinessInitiativeModel(Base):
    """Business initiatives and projects."""

    __tablename__ = "business_initiatives"

    id = Column(Integer, primary_key=True, index=True)
    initiative_id = Column(
        String(50), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    strategic_plan_id = Column(String(50), ForeignKey("strategic_plans.plan_id"))

    name = Column(String(200), nullable=False)
    description = Column(Text)
    objective = Column(String(50), nullable=False, index=True)
    priority = Column(String(20), nullable=False, index=True)

    # Financial projections
    estimated_cost = Column(Numeric(15, 2))
    estimated_revenue = Column(Numeric(15, 2))
    estimated_roi = Column(Numeric(5, 2))
    timeline_months = Column(Integer)

    # Resources and requirements
    required_resources = Column(JSON)
    success_metrics = Column(JSON)
    risks = Column(JSON)
    dependencies = Column(JSON)

    # Status tracking
    status = Column(String(20), default="proposed", index=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    strategic_plan = relationship("StrategicPlanModel", backref="initiatives")

    # Indexes
    __table_args__ = (
        Index("idx_business_initiatives_objective_priority", "objective", "priority"),
        Index("idx_business_initiatives_status_created", "status", "created_at"),
    )


class ResourceAllocationModel(Base):
    """Resource allocation records."""

    __tablename__ = "resource_allocations"

    id = Column(Integer, primary_key=True, index=True)
    allocation_id = Column(
        String(50), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )
    initiative_id = Column(String(50), ForeignKey("business_initiatives.initiative_id"))

    resource_type = Column(String(50), nullable=False, index=True)
    amount = Column(Numeric(15, 2))
    unit = Column(String(20))
    justification = Column(Text)
    priority_score = Column(Numeric(3, 2))

    # Expected impact and constraints
    expected_impact = Column(JSON)
    constraints = Column(JSON)
    alternatives = Column(JSON)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    initiative = relationship("BusinessInitiativeModel", backref="resource_allocations")

    # Indexes
    __table_args__ = (
        Index("idx_resource_allocations_type_amount", "resource_type", "amount"),
        Index("idx_resource_allocations_created_at", "created_at"),
    )


class RiskAssessmentModel(Base):
    """Risk assessment records."""

    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(
        String(50), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )

    # Assessment context
    assessment_type = Column(
        String(50), nullable=False, index=True
    )  # "initiative", "decision", "strategic"
    related_entity_id = Column(
        String(50), index=True
    )  # ID of related initiative/decision/plan

    # Risk analysis results
    overall_risk_level = Column(String(20), nullable=False, index=True)
    risk_score = Column(Numeric(3, 2))
    identified_risks = Column(JSON)  # List of risk factors
    risk_scenarios = Column(JSON)  # List of risk scenarios

    # Mitigation and monitoring
    mitigation_plan = Column(JSON)  # List of mitigation strategies
    monitoring_requirements = Column(JSON)  # List of monitoring requirements
    contingency_recommendations = Column(JSON)  # List of contingency recommendations

    # Assessment metadata
    risk_tolerance_alignment = Column(String(100))
    confidence_score = Column(Numeric(3, 2))

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Indexes
    __table_args__ = (
        Index(
            "idx_risk_assessments_type_level", "assessment_type", "overall_risk_level"
        ),
        Index("idx_risk_assessments_entity_created", "related_entity_id", "created_at"),
    )


class InvestmentOpportunityModel(Base):
    """Investment opportunity analysis."""

    __tablename__ = "investment_opportunities"

    id = Column(Integer, primary_key=True, index=True)
    opportunity_id = Column(
        String(50), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )

    name = Column(String(200), nullable=False)
    description = Column(Text)
    investment_type = Column(String(50), nullable=False, index=True)

    # Financial analysis
    required_investment = Column(Numeric(15, 2))
    expected_return = Column(Numeric(15, 2))
    payback_period_months = Column(Integer)
    roi = Column(Numeric(5, 2))
    npv = Column(Numeric(15, 2))  # Net Present Value
    irr = Column(Numeric(5, 2))  # Internal Rate of Return

    # Risk and market analysis
    risk_assessment = Column(String(20), index=True)
    market_size = Column(Numeric(15, 2))
    competitive_advantage = Column(JSON)
    success_probability = Column(Numeric(3, 2))

    # Projections and analysis
    financial_projections = Column(JSON)
    risks = Column(JSON)
    recommendation = Column(Text)
    confidence_score = Column(Numeric(3, 2))

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Indexes
    __table_args__ = (
        Index("idx_investment_opportunities_type_roi", "investment_type", "roi"),
        Index(
            "idx_investment_opportunities_risk_return",
            "risk_assessment",
            "expected_return",
        ),
    )


class PerformanceKPIModel(Base):
    """Key Performance Indicator tracking."""

    __tablename__ = "performance_kpis"

    id = Column(Integer, primary_key=True, index=True)
    kpi_id = Column(
        String(50), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )

    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False, index=True)

    # Current performance
    current_value = Column(Numeric(15, 4))
    target_value = Column(Numeric(15, 4))
    unit = Column(String(20))

    # Performance analysis
    trend = Column(String(20), default="stable", index=True)
    performance_status = Column(String(20), default="on_track", index=True)
    historical_values = Column(JSON)
    benchmark_value = Column(Numeric(15, 4))

    # Ownership and updates
    owner = Column(String(100))
    update_frequency = Column(String(20))
    last_updated = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    # Indexes
    __table_args__ = (
        Index("idx_performance_kpis_category_status", "category", "performance_status"),
        Index("idx_performance_kpis_trend_updated", "trend", "last_updated"),
    )


class BusinessIntelligenceModel(Base):
    """Business intelligence data for decision making."""

    __tablename__ = "business_intelligence"

    id = Column(Integer, primary_key=True, index=True)
    data_id = Column(
        String(50), unique=True, index=True, default=lambda: str(uuid.uuid4())
    )

    data_type = Column(String(50), nullable=False, index=True)
    source = Column(String(100), nullable=False)

    # Intelligence data
    metrics = Column(JSON)
    insights = Column(JSON)
    trends = Column(JSON)
    recommendations = Column(JSON)

    # Data quality
    confidence_level = Column(Numeric(3, 2))
    data_quality = Column(String(20), default="high")

    # Validity
    last_updated = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    valid_until = Column(DateTime(timezone=True))

    # Indexes
    __table_args__ = (
        Index("idx_business_intelligence_type_source", "data_type", "source"),
        Index("idx_business_intelligence_updated_valid", "last_updated", "valid_until"),
    )
