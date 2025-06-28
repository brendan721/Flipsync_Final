"""
Executive Repository for Database Operations
===========================================

Repository pattern implementation for executive agent database operations
including strategic plans, decisions, resource allocations, and risk assessments.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from fs_agt_clean.core.models.business_models import (
    BusinessInitiative,
    BusinessIntelligence,
    ExecutiveDecision,
    InvestmentOpportunity,
    PerformanceKPI,
    ResourceAllocation,
    StrategicPlan,
)
from fs_agt_clean.database.models.executive_models import (
    BusinessInitiativeModel,
    BusinessIntelligenceModel,
    ExecutiveDecisionModel,
    InvestmentOpportunityModel,
    PerformanceKPIModel,
    ResourceAllocationModel,
    RiskAssessmentModel,
    StrategicPlanModel,
)

logger = logging.getLogger(__name__)


class ExecutiveRepository:
    """Repository for executive agent database operations."""

    def __init__(self, db_session: Session):
        """Initialize repository with database session."""
        self.db = db_session

    # Executive Decisions
    async def create_executive_decision(self, decision: ExecutiveDecision) -> str:
        """Create a new executive decision record."""
        try:
            db_decision = ExecutiveDecisionModel(
                decision_id=decision.decision_id,
                decision_type=decision.decision_type.value,
                title=decision.title,
                description=decision.description,
                context=decision.context,
                criteria=[
                    {
                        "criteria_name": c.criteria_name,
                        "weight": c.weight,
                        "description": c.description,
                        "measurement_type": c.measurement_type,
                        "scale_min": c.scale_min,
                        "scale_max": c.scale_max,
                        "higher_is_better": c.higher_is_better,
                    }
                    for c in decision.criteria
                ],
                alternatives=[
                    {
                        "alternative_id": a.alternative_id,
                        "name": a.name,
                        "description": a.description,
                        "scores": a.scores,
                        "weighted_score": a.weighted_score,
                        "pros": a.pros,
                        "cons": a.cons,
                        "implementation_complexity": a.implementation_complexity,
                        "resource_requirements": a.resource_requirements,
                        "timeline": a.timeline,
                        "risks": a.risks,
                    }
                    for a in decision.alternatives
                ],
                recommended_alternative=decision.recommended_alternative,
                recommendation_reasoning=decision.recommendation_reasoning,
                confidence_score=decision.confidence_score,
                financial_impact=(
                    {
                        "revenue": float(decision.financial_impact.revenue),
                        "profit": float(decision.financial_impact.profit),
                        "margin": decision.financial_impact.margin,
                        "roi": decision.financial_impact.roi,
                        "cash_flow": float(decision.financial_impact.cash_flow),
                        "expenses": float(decision.financial_impact.expenses),
                        "currency": decision.financial_impact.currency,
                        "period": decision.financial_impact.period,
                    }
                    if decision.financial_impact
                    else None
                ),
                risk_assessment=[
                    {
                        "factor_id": r.factor_id,
                        "name": r.name,
                        "description": r.description,
                        "probability": r.probability,
                        "impact": r.impact,
                        "risk_level": r.risk_level.value,
                        "mitigation_strategies": r.mitigation_strategies,
                        "owner": r.owner,
                        "timeline": r.timeline,
                    }
                    for r in decision.risk_assessment
                ],
                implementation_plan=decision.implementation_plan,
                success_metrics=decision.success_metrics,
                approval_required=decision.approval_required,
                urgency=decision.urgency.value,
                stakeholders=decision.stakeholders,
                status=decision.status,
                created_by=decision.created_by,
                created_at=decision.created_at,
                approved_at=decision.approved_at,
                approved_by=decision.approved_by,
            )

            self.db.add(db_decision)
            self.db.commit()
            self.db.refresh(db_decision)

            logger.info(f"Created executive decision: {decision.decision_id}")
            return db_decision.decision_id

        except Exception as e:
            logger.error(f"Error creating executive decision: {e}")
            self.db.rollback()
            raise

    async def get_executive_decision(
        self, decision_id: str
    ) -> Optional[ExecutiveDecisionModel]:
        """Get executive decision by ID."""
        try:
            return (
                self.db.query(ExecutiveDecisionModel)
                .filter(ExecutiveDecisionModel.decision_id == decision_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting executive decision {decision_id}: {e}")
            return None

    async def get_executive_decisions_by_type(
        self, decision_type: str, limit: int = 50
    ) -> List[ExecutiveDecisionModel]:
        """Get executive decisions by type."""
        try:
            return (
                self.db.query(ExecutiveDecisionModel)
                .filter(ExecutiveDecisionModel.decision_type == decision_type)
                .order_by(desc(ExecutiveDecisionModel.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(
                f"Error getting executive decisions by type {decision_type}: {e}"
            )
            return []

    async def get_pending_decisions(
        self, limit: int = 20
    ) -> List[ExecutiveDecisionModel]:
        """Get pending executive decisions requiring approval."""
        try:
            return (
                self.db.query(ExecutiveDecisionModel)
                .filter(
                    and_(
                        ExecutiveDecisionModel.status == "pending",
                        ExecutiveDecisionModel.approval_required == True,
                    )
                )
                .order_by(desc(ExecutiveDecisionModel.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting pending decisions: {e}")
            return []

    async def update_decision_status(
        self, decision_id: str, status: str, approved_by: Optional[str] = None
    ) -> bool:
        """Update decision status and approval."""
        try:
            decision = await self.get_executive_decision(decision_id)
            if decision:
                decision.status = status
                if approved_by:
                    decision.approved_by = approved_by
                    decision.approved_at = datetime.now(timezone.utc)

                self.db.commit()
                logger.info(f"Updated decision {decision_id} status to {status}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating decision status: {e}")
            self.db.rollback()
            return False

    # Strategic Plans
    async def create_strategic_plan(self, plan: StrategicPlan) -> str:
        """Create a new strategic plan."""
        try:
            db_plan = StrategicPlanModel(
                plan_id=plan.plan_id,
                name=plan.name,
                description=plan.description,
                time_horizon=plan.time_horizon,
                objectives=[obj.value for obj in plan.objectives],
                initiatives=[
                    {
                        "initiative_id": init.initiative_id,
                        "name": init.name,
                        "description": init.description,
                        "objective": init.objective.value,
                        "priority": init.priority.value,
                        "estimated_cost": float(init.estimated_cost),
                        "estimated_revenue": float(init.estimated_revenue),
                        "estimated_roi": init.estimated_roi,
                        "timeline_months": init.timeline_months,
                        "required_resources": init.required_resources,
                        "success_metrics": init.success_metrics,
                        "risks": init.risks,
                        "dependencies": init.dependencies,
                        "status": init.status,
                        "created_at": init.created_at.isoformat(),
                    }
                    for init in plan.initiatives
                ],
                total_budget=plan.total_budget,
                expected_roi=plan.expected_roi,
                key_metrics=plan.key_metrics,
                success_criteria=plan.success_criteria,
                risks=[
                    {
                        "factor_id": r.factor_id,
                        "name": r.name,
                        "description": r.description,
                        "probability": r.probability,
                        "impact": r.impact,
                        "risk_level": r.risk_level.value,
                        "mitigation_strategies": r.mitigation_strategies,
                    }
                    for r in plan.risks
                ],
                milestones=plan.milestones,
                status=plan.status,
                created_by=plan.created_by,
                approved_by=plan.approved_by,
                created_at=plan.created_at,
                approved_at=plan.approved_at,
            )

            self.db.add(db_plan)
            self.db.commit()
            self.db.refresh(db_plan)

            logger.info(f"Created strategic plan: {plan.plan_id}")
            return db_plan.plan_id

        except Exception as e:
            logger.error(f"Error creating strategic plan: {e}")
            self.db.rollback()
            raise

    async def get_strategic_plan(self, plan_id: str) -> Optional[StrategicPlanModel]:
        """Get strategic plan by ID."""
        try:
            return (
                self.db.query(StrategicPlanModel)
                .filter(StrategicPlanModel.plan_id == plan_id)
                .first()
            )
        except Exception as e:
            logger.error(f"Error getting strategic plan {plan_id}: {e}")
            return None

    async def get_strategic_plans_by_horizon(
        self, time_horizon: str, limit: int = 20
    ) -> List[StrategicPlanModel]:
        """Get strategic plans by time horizon."""
        try:
            return (
                self.db.query(StrategicPlanModel)
                .filter(StrategicPlanModel.time_horizon == time_horizon)
                .order_by(desc(StrategicPlanModel.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(
                f"Error getting strategic plans by horizon {time_horizon}: {e}"
            )
            return []

    # Business Initiatives
    async def create_business_initiative(self, initiative: BusinessInitiative) -> str:
        """Create a new business initiative."""
        try:
            db_initiative = BusinessInitiativeModel(
                initiative_id=initiative.initiative_id,
                name=initiative.name,
                description=initiative.description,
                objective=initiative.objective.value,
                priority=initiative.priority.value,
                estimated_cost=initiative.estimated_cost,
                estimated_revenue=initiative.estimated_revenue,
                estimated_roi=initiative.estimated_roi,
                timeline_months=initiative.timeline_months,
                required_resources=initiative.required_resources,
                success_metrics=initiative.success_metrics,
                risks=initiative.risks,
                dependencies=initiative.dependencies,
                status=initiative.status,
                created_at=initiative.created_at,
            )

            self.db.add(db_initiative)
            self.db.commit()
            self.db.refresh(db_initiative)

            logger.info(f"Created business initiative: {initiative.initiative_id}")
            return db_initiative.initiative_id

        except Exception as e:
            logger.error(f"Error creating business initiative: {e}")
            self.db.rollback()
            raise

    async def get_initiatives_by_objective(
        self, objective: str, limit: int = 20
    ) -> List[BusinessInitiativeModel]:
        """Get business initiatives by objective."""
        try:
            return (
                self.db.query(BusinessInitiativeModel)
                .filter(BusinessInitiativeModel.objective == objective)
                .order_by(desc(BusinessInitiativeModel.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting initiatives by objective {objective}: {e}")
            return []

    # Resource Allocations
    async def create_resource_allocation(self, allocation: ResourceAllocation) -> str:
        """Create a new resource allocation."""
        try:
            db_allocation = ResourceAllocationModel(
                allocation_id=allocation.allocation_id,
                initiative_id=allocation.initiative_id,
                resource_type=allocation.resource_type,
                amount=allocation.amount,
                unit=allocation.unit,
                justification=allocation.justification,
                priority_score=allocation.priority_score,
                expected_impact=allocation.expected_impact,
                constraints=allocation.constraints,
                alternatives=allocation.alternatives,
                created_at=allocation.created_at,
            )

            self.db.add(db_allocation)
            self.db.commit()
            self.db.refresh(db_allocation)

            logger.info(f"Created resource allocation: {allocation.allocation_id}")
            return db_allocation.allocation_id

        except Exception as e:
            logger.error(f"Error creating resource allocation: {e}")
            self.db.rollback()
            raise

    async def get_allocations_by_resource_type(
        self, resource_type: str, limit: int = 50
    ) -> List[ResourceAllocationModel]:
        """Get resource allocations by type."""
        try:
            return (
                self.db.query(ResourceAllocationModel)
                .filter(ResourceAllocationModel.resource_type == resource_type)
                .order_by(desc(ResourceAllocationModel.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(
                f"Error getting allocations by resource type {resource_type}: {e}"
            )
            return []

    # Risk Assessments
    async def create_risk_assessment(
        self, assessment_type: str, related_entity_id: str, risk_data: Dict[str, Any]
    ) -> str:
        """Create a new risk assessment."""
        try:
            assessment_id = (
                f"risk_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
            )

            db_assessment = RiskAssessmentModel(
                assessment_id=assessment_id,
                assessment_type=assessment_type,
                related_entity_id=related_entity_id,
                overall_risk_level=risk_data.get("overall_risk_level", "medium"),
                risk_score=risk_data.get("risk_score", 0.5),
                identified_risks=risk_data.get("identified_risks", []),
                risk_scenarios=risk_data.get("risk_scenarios", []),
                mitigation_plan=risk_data.get("mitigation_plan", []),
                monitoring_requirements=risk_data.get("monitoring_requirements", []),
                contingency_recommendations=risk_data.get(
                    "contingency_recommendations", []
                ),
                risk_tolerance_alignment=risk_data.get("risk_tolerance_alignment", ""),
                confidence_score=risk_data.get("confidence_score", 0.7),
            )

            self.db.add(db_assessment)
            self.db.commit()
            self.db.refresh(db_assessment)

            logger.info(f"Created risk assessment: {assessment_id}")
            return assessment_id

        except Exception as e:
            logger.error(f"Error creating risk assessment: {e}")
            self.db.rollback()
            raise

    async def get_risk_assessments_by_entity(
        self, entity_id: str, limit: int = 10
    ) -> List[RiskAssessmentModel]:
        """Get risk assessments for a specific entity."""
        try:
            return (
                self.db.query(RiskAssessmentModel)
                .filter(RiskAssessmentModel.related_entity_id == entity_id)
                .order_by(desc(RiskAssessmentModel.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting risk assessments for entity {entity_id}: {e}")
            return []

    # Investment Opportunities
    async def create_investment_opportunity(
        self, opportunity: InvestmentOpportunity
    ) -> str:
        """Create a new investment opportunity."""
        try:
            db_opportunity = InvestmentOpportunityModel(
                opportunity_id=opportunity.opportunity_id,
                name=opportunity.name,
                description=opportunity.description,
                investment_type=opportunity.investment_type,
                required_investment=opportunity.required_investment,
                expected_return=opportunity.expected_return,
                payback_period_months=opportunity.payback_period_months,
                roi=opportunity.roi,
                npv=opportunity.npv,
                irr=opportunity.irr,
                risk_assessment=opportunity.risk_assessment.value,
                market_size=opportunity.market_size,
                competitive_advantage=opportunity.competitive_advantage,
                success_probability=opportunity.success_probability,
                financial_projections=[
                    {
                        "revenue": float(fp.revenue),
                        "profit": float(fp.profit),
                        "margin": fp.margin,
                        "roi": fp.roi,
                        "cash_flow": float(fp.cash_flow),
                        "expenses": float(fp.expenses),
                        "currency": fp.currency,
                        "period": fp.period,
                        "timestamp": fp.timestamp.isoformat(),
                    }
                    for fp in opportunity.financial_projections
                ],
                risks=[
                    {
                        "factor_id": r.factor_id,
                        "name": r.name,
                        "description": r.description,
                        "probability": r.probability,
                        "impact": r.impact,
                        "risk_level": r.risk_level.value,
                        "mitigation_strategies": r.mitigation_strategies,
                    }
                    for r in opportunity.risks
                ],
                recommendation=opportunity.recommendation,
                confidence_score=opportunity.confidence_score,
                created_at=opportunity.created_at,
            )

            self.db.add(db_opportunity)
            self.db.commit()
            self.db.refresh(db_opportunity)

            logger.info(f"Created investment opportunity: {opportunity.opportunity_id}")
            return db_opportunity.opportunity_id

        except Exception as e:
            logger.error(f"Error creating investment opportunity: {e}")
            self.db.rollback()
            raise

    async def get_investment_opportunities_by_type(
        self, investment_type: str, limit: int = 20
    ) -> List[InvestmentOpportunityModel]:
        """Get investment opportunities by type."""
        try:
            return (
                self.db.query(InvestmentOpportunityModel)
                .filter(InvestmentOpportunityModel.investment_type == investment_type)
                .order_by(desc(InvestmentOpportunityModel.roi))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(
                f"Error getting investment opportunities by type {investment_type}: {e}"
            )
            return []

    # Performance KPIs
    async def create_performance_kpi(self, kpi: PerformanceKPI) -> str:
        """Create a new performance KPI."""
        try:
            db_kpi = PerformanceKPIModel(
                kpi_id=kpi.kpi_id,
                name=kpi.name,
                description=kpi.description,
                category=kpi.category,
                current_value=kpi.current_value,
                target_value=kpi.target_value,
                unit=kpi.unit,
                trend=kpi.trend,
                performance_status=kpi.performance_status,
                historical_values=kpi.historical_values,
                benchmark_value=kpi.benchmark_value,
                owner=kpi.owner,
                update_frequency=kpi.update_frequency,
                last_updated=kpi.last_updated,
            )

            self.db.add(db_kpi)
            self.db.commit()
            self.db.refresh(db_kpi)

            logger.info(f"Created performance KPI: {kpi.kpi_id}")
            return db_kpi.kpi_id

        except Exception as e:
            logger.error(f"Error creating performance KPI: {e}")
            self.db.rollback()
            raise

    async def get_kpis_by_category(
        self, category: str, limit: int = 20
    ) -> List[PerformanceKPIModel]:
        """Get KPIs by category."""
        try:
            return (
                self.db.query(PerformanceKPIModel)
                .filter(PerformanceKPIModel.category == category)
                .order_by(desc(PerformanceKPIModel.last_updated))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(f"Error getting KPIs by category {category}: {e}")
            return []

    # Business Intelligence
    async def create_business_intelligence(
        self, intelligence: BusinessIntelligence
    ) -> str:
        """Create a new business intelligence record."""
        try:
            db_intelligence = BusinessIntelligenceModel(
                data_id=intelligence.data_id,
                data_type=intelligence.data_type,
                source=intelligence.source,
                metrics=intelligence.metrics,
                insights=intelligence.insights,
                trends=intelligence.trends,
                recommendations=intelligence.recommendations,
                confidence_level=intelligence.confidence_level,
                data_quality=intelligence.data_quality,
                last_updated=intelligence.last_updated,
                valid_until=intelligence.valid_until,
            )

            self.db.add(db_intelligence)
            self.db.commit()
            self.db.refresh(db_intelligence)

            logger.info(f"Created business intelligence: {intelligence.data_id}")
            return db_intelligence.data_id

        except Exception as e:
            logger.error(f"Error creating business intelligence: {e}")
            self.db.rollback()
            raise

    async def get_business_intelligence_by_type(
        self, data_type: str, limit: int = 10
    ) -> List[BusinessIntelligenceModel]:
        """Get business intelligence by data type."""
        try:
            return (
                self.db.query(BusinessIntelligenceModel)
                .filter(BusinessIntelligenceModel.data_type == data_type)
                .order_by(desc(BusinessIntelligenceModel.last_updated))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error(
                f"Error getting business intelligence by type {data_type}: {e}"
            )
            return []
