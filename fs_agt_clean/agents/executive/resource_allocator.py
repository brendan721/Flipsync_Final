"""
Resource Allocation Engine for FlipSync Executive UnifiedAgent
======================================================

This module provides intelligent resource allocation algorithms for optimizing
resource distribution across business initiatives, projects, and operations.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from fs_agt_clean.core.models.business_models import (
    BusinessInitiative,
    BusinessObjective,
    FinancialMetrics,
    Priority,
    ResourceAllocation,
    RiskLevel,
)

logger = logging.getLogger(__name__)


@dataclass
class ResourceConstraint:
    """Resource constraint definition."""

    resource_type: str
    total_available: float
    allocated: float
    reserved: float
    unit: str
    constraint_type: str = "hard"  # "hard" or "soft"


@dataclass
class ResourceDemand:
    """Resource demand from an initiative."""

    initiative_id: str
    resource_type: str
    amount_requested: float
    priority_score: float
    urgency: Priority
    justification: str
    alternative_amounts: List[float]


@dataclass
class AllocationResult:
    """Result of resource allocation optimization."""

    allocations: List[ResourceAllocation]
    total_satisfaction: float
    unmet_demands: List[ResourceDemand]
    resource_utilization: Dict[str, float]
    optimization_score: float
    recommendations: List[str]


class ResourceAllocator:
    """Advanced resource allocation engine using optimization algorithms."""

    def __init__(self):
        """Initialize the resource allocator."""
        # Resource types and their characteristics
        self.resource_types = {
            "budget": {
                "unit": "USD",
                "divisible": True,
                "transferable": True,
                "depreciation_rate": 0.0,
            },
            "personnel": {
                "unit": "FTE",
                "divisible": False,
                "transferable": True,
                "depreciation_rate": 0.0,
            },
            "time": {
                "unit": "hours",
                "divisible": True,
                "transferable": False,
                "depreciation_rate": 0.0,
            },
            "technology": {
                "unit": "licenses",
                "divisible": False,
                "transferable": True,
                "depreciation_rate": 0.1,
            },
            "equipment": {
                "unit": "units",
                "divisible": False,
                "transferable": True,
                "depreciation_rate": 0.15,
            },
        }

        # Priority weights for allocation decisions
        self.priority_weights = {
            Priority.CRITICAL: 1.0,
            Priority.HIGH: 0.8,
            Priority.MEDIUM: 0.6,
            Priority.LOW: 0.4,
        }

        logger.info("Resource allocator initialized")

    async def optimize_allocation(
        self,
        initiatives: List[BusinessInitiative],
        constraints: List[ResourceConstraint],
        optimization_objective: str = "maximize_value",
    ) -> AllocationResult:
        """
        Optimize resource allocation across initiatives.

        Args:
            initiatives: List of business initiatives requiring resources
            constraints: Available resource constraints
            optimization_objective: Optimization goal ("maximize_value", "minimize_risk", "balance")

        Returns:
            AllocationResult with optimized allocations
        """
        try:
            # Convert initiatives to resource demands
            demands = await self._extract_resource_demands(initiatives)

            # Apply optimization algorithm
            if optimization_objective == "maximize_value":
                allocations = await self._maximize_value_allocation(
                    demands, constraints
                )
            elif optimization_objective == "minimize_risk":
                allocations = await self._minimize_risk_allocation(
                    demands, constraints, initiatives
                )
            else:  # balance
                allocations = await self._balanced_allocation(
                    demands, constraints, initiatives
                )

            # Calculate satisfaction and utilization
            satisfaction = self._calculate_satisfaction(demands, allocations)
            utilization = self._calculate_utilization(constraints, allocations)

            # Identify unmet demands
            unmet_demands = self._identify_unmet_demands(demands, allocations)

            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(
                satisfaction, utilization, len(unmet_demands), len(demands)
            )

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                allocations, unmet_demands, constraints, utilization
            )

            return AllocationResult(
                allocations=allocations,
                total_satisfaction=satisfaction,
                unmet_demands=unmet_demands,
                resource_utilization=utilization,
                optimization_score=optimization_score,
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error in resource allocation optimization: {e}")
            return await self._create_fallback_allocation(initiatives, constraints)

    async def _extract_resource_demands(
        self, initiatives: List[BusinessInitiative]
    ) -> List[ResourceDemand]:
        """Extract resource demands from business initiatives."""
        demands = []

        for initiative in initiatives:
            # Calculate priority score
            priority_score = self.priority_weights.get(initiative.priority, 0.6)

            # Adjust priority score based on ROI
            roi_bonus = min(initiative.estimated_roi / 100, 0.5)
            priority_score += roi_bonus

            # Extract resource requirements
            for resource_type, amount in initiative.required_resources.items():
                if resource_type in self.resource_types:
                    # Generate alternative amounts (80%, 100%, 120% of requested)
                    alternatives = [amount * 0.8, amount, amount * 1.2]

                    demand = ResourceDemand(
                        initiative_id=initiative.initiative_id,
                        resource_type=resource_type,
                        amount_requested=amount,
                        priority_score=priority_score,
                        urgency=initiative.priority,
                        justification=f"Required for {initiative.name}",
                        alternative_amounts=alternatives,
                    )
                    demands.append(demand)

        return demands

    async def _maximize_value_allocation(
        self, demands: List[ResourceDemand], constraints: List[ResourceConstraint]
    ) -> List[ResourceAllocation]:
        """Allocate resources to maximize overall value."""
        allocations = []

        # Create constraint tracking
        available_resources = {
            constraint.resource_type: constraint.total_available
            - constraint.allocated
            - constraint.reserved
            for constraint in constraints
        }

        # Sort demands by priority score (highest first)
        sorted_demands = sorted(demands, key=lambda d: d.priority_score, reverse=True)

        for demand in sorted_demands:
            available = available_resources.get(demand.resource_type, 0)

            if available >= demand.amount_requested:
                # Full allocation
                allocated_amount = demand.amount_requested
                allocation_score = demand.priority_score
            elif available > 0:
                # Partial allocation
                allocated_amount = available
                allocation_score = demand.priority_score * (
                    allocated_amount / demand.amount_requested
                )
            else:
                # No allocation possible
                continue

            if allocated_amount > 0:
                allocation = ResourceAllocation(
                    initiative_id=demand.initiative_id,
                    resource_type=demand.resource_type,
                    amount=allocated_amount,
                    unit=self.resource_types[demand.resource_type]["unit"],
                    justification=demand.justification,
                    priority_score=allocation_score,
                    expected_impact={"value_score": allocation_score},
                )
                allocations.append(allocation)

                # Update available resources
                available_resources[demand.resource_type] -= allocated_amount

        return allocations

    async def _minimize_risk_allocation(
        self,
        demands: List[ResourceDemand],
        constraints: List[ResourceConstraint],
        initiatives: List[BusinessInitiative],
    ) -> List[ResourceAllocation]:
        """Allocate resources to minimize overall risk."""
        allocations = []

        # Create initiative risk mapping
        initiative_risks = {init.initiative_id: len(init.risks) for init in initiatives}

        # Create constraint tracking
        available_resources = {
            constraint.resource_type: constraint.total_available
            - constraint.allocated
            - constraint.reserved
            for constraint in constraints
        }

        # Sort demands by risk (lowest risk first) and priority
        def risk_priority_score(demand):
            risk_count = initiative_risks.get(demand.initiative_id, 0)
            risk_penalty = risk_count * 0.1
            return demand.priority_score - risk_penalty

        sorted_demands = sorted(demands, key=risk_priority_score, reverse=True)

        for demand in sorted_demands:
            available = available_resources.get(demand.resource_type, 0)

            # Conservative allocation (prefer 80% of requested to reduce risk)
            conservative_amount = demand.amount_requested * 0.8

            if available >= conservative_amount:
                allocated_amount = conservative_amount
            elif available > 0:
                allocated_amount = min(available, demand.amount_requested * 0.6)
            else:
                continue

            if allocated_amount > 0:
                risk_score = 1.0 - (initiative_risks.get(demand.initiative_id, 0) * 0.1)

                allocation = ResourceAllocation(
                    initiative_id=demand.initiative_id,
                    resource_type=demand.resource_type,
                    amount=allocated_amount,
                    unit=self.resource_types[demand.resource_type]["unit"],
                    justification=f"Conservative allocation for {demand.justification}",
                    priority_score=demand.priority_score * risk_score,
                    expected_impact={"risk_mitigation": risk_score},
                )
                allocations.append(allocation)

                # Update available resources
                available_resources[demand.resource_type] -= allocated_amount

        return allocations

    async def _balanced_allocation(
        self,
        demands: List[ResourceDemand],
        constraints: List[ResourceConstraint],
        initiatives: List[BusinessInitiative],
    ) -> List[ResourceAllocation]:
        """Allocate resources using a balanced approach."""
        allocations = []

        # Create constraint tracking
        available_resources = {
            constraint.resource_type: constraint.total_available
            - constraint.allocated
            - constraint.reserved
            for constraint in constraints
        }

        # Group demands by resource type
        demands_by_type = {}
        for demand in demands:
            if demand.resource_type not in demands_by_type:
                demands_by_type[demand.resource_type] = []
            demands_by_type[demand.resource_type].append(demand)

        # Allocate each resource type separately
        for resource_type, type_demands in demands_by_type.items():
            available = available_resources.get(resource_type, 0)

            if available <= 0:
                continue

            # Calculate total requested
            total_requested = sum(d.amount_requested for d in type_demands)

            if total_requested <= available:
                # Full allocation for all
                for demand in type_demands:
                    allocation = ResourceAllocation(
                        initiative_id=demand.initiative_id,
                        resource_type=demand.resource_type,
                        amount=demand.amount_requested,
                        unit=self.resource_types[demand.resource_type]["unit"],
                        justification=demand.justification,
                        priority_score=demand.priority_score,
                        expected_impact={"allocation_ratio": 1.0},
                    )
                    allocations.append(allocation)
            else:
                # Proportional allocation based on priority
                total_priority = sum(d.priority_score for d in type_demands)

                for demand in type_demands:
                    if total_priority > 0:
                        allocation_ratio = demand.priority_score / total_priority
                        allocated_amount = available * allocation_ratio
                    else:
                        allocated_amount = available / len(type_demands)

                    allocation = ResourceAllocation(
                        initiative_id=demand.initiative_id,
                        resource_type=demand.resource_type,
                        amount=allocated_amount,
                        unit=self.resource_types[demand.resource_type]["unit"],
                        justification=f"Proportional allocation: {demand.justification}",
                        priority_score=demand.priority_score,
                        expected_impact={
                            "allocation_ratio": allocated_amount
                            / demand.amount_requested
                        },
                    )
                    allocations.append(allocation)

        return allocations

    def _calculate_satisfaction(
        self, demands: List[ResourceDemand], allocations: List[ResourceAllocation]
    ) -> float:
        """Calculate overall satisfaction score."""
        if not demands:
            return 1.0

        # Create allocation mapping
        allocation_map = {}
        for allocation in allocations:
            key = (allocation.initiative_id, allocation.resource_type)
            allocation_map[key] = allocation.amount

        total_satisfaction = 0.0
        total_weight = 0.0

        for demand in demands:
            key = (demand.initiative_id, demand.resource_type)
            allocated = allocation_map.get(key, 0)

            if demand.amount_requested > 0:
                satisfaction = min(allocated / demand.amount_requested, 1.0)
            else:
                satisfaction = 1.0

            # Weight by priority
            weight = demand.priority_score
            total_satisfaction += satisfaction * weight
            total_weight += weight

        return total_satisfaction / total_weight if total_weight > 0 else 0.0

    def _calculate_utilization(
        self,
        constraints: List[ResourceConstraint],
        allocations: List[ResourceAllocation],
    ) -> Dict[str, float]:
        """Calculate resource utilization rates."""
        utilization = {}

        # Calculate allocated amounts by resource type
        allocated_by_type = {}
        for allocation in allocations:
            if allocation.resource_type not in allocated_by_type:
                allocated_by_type[allocation.resource_type] = 0
            allocated_by_type[allocation.resource_type] += allocation.amount

        # Calculate utilization rates
        for constraint in constraints:
            total_available = constraint.total_available
            already_allocated = constraint.allocated + constraint.reserved
            new_allocated = allocated_by_type.get(constraint.resource_type, 0)

            if total_available > 0:
                utilization[constraint.resource_type] = (
                    already_allocated + new_allocated
                ) / total_available
            else:
                utilization[constraint.resource_type] = 0.0

        return utilization

    def _identify_unmet_demands(
        self, demands: List[ResourceDemand], allocations: List[ResourceAllocation]
    ) -> List[ResourceDemand]:
        """Identify demands that were not fully met."""
        unmet = []

        # Create allocation mapping
        allocation_map = {}
        for allocation in allocations:
            key = (allocation.initiative_id, allocation.resource_type)
            allocation_map[key] = allocation.amount

        for demand in demands:
            key = (demand.initiative_id, demand.resource_type)
            allocated = allocation_map.get(key, 0)

            if allocated < demand.amount_requested:
                # Create unmet demand with remaining amount
                unmet_demand = ResourceDemand(
                    initiative_id=demand.initiative_id,
                    resource_type=demand.resource_type,
                    amount_requested=demand.amount_requested - allocated,
                    priority_score=demand.priority_score,
                    urgency=demand.urgency,
                    justification=f"Unmet portion of: {demand.justification}",
                    alternative_amounts=demand.alternative_amounts,
                )
                unmet.append(unmet_demand)

        return unmet

    def _calculate_optimization_score(
        self,
        satisfaction: float,
        utilization: Dict[str, float],
        unmet_count: int,
        total_demands: int,
    ) -> float:
        """Calculate overall optimization score."""
        # Base score from satisfaction
        base_score = satisfaction * 0.4

        # Utilization score (prefer 80-90% utilization)
        avg_utilization = (
            sum(utilization.values()) / len(utilization) if utilization else 0
        )
        if 0.8 <= avg_utilization <= 0.9:
            utilization_score = 0.3
        else:
            utilization_score = 0.3 * (1 - abs(avg_utilization - 0.85) / 0.85)

        # Demand fulfillment score
        fulfillment_rate = 1 - (unmet_count / total_demands) if total_demands > 0 else 1
        fulfillment_score = fulfillment_rate * 0.3

        return base_score + utilization_score + fulfillment_score

    async def _generate_recommendations(
        self,
        allocations: List[ResourceAllocation],
        unmet_demands: List[ResourceDemand],
        constraints: List[ResourceConstraint],
        utilization: Dict[str, float],
    ) -> List[str]:
        """Generate recommendations for resource allocation improvement."""
        recommendations = []

        # Utilization recommendations
        for resource_type, util_rate in utilization.items():
            if util_rate > 0.95:
                recommendations.append(
                    f"Consider increasing {resource_type} capacity - currently at {util_rate:.1%} utilization"
                )
            elif util_rate < 0.5:
                recommendations.append(
                    f"Consider reallocating excess {resource_type} capacity - currently at {util_rate:.1%} utilization"
                )

        # Unmet demand recommendations
        if unmet_demands:
            high_priority_unmet = [
                d
                for d in unmet_demands
                if d.urgency in [Priority.CRITICAL, Priority.HIGH]
            ]
            if high_priority_unmet:
                recommendations.append(
                    f"Address {len(high_priority_unmet)} high-priority unmet resource demands"
                )

        # Allocation efficiency recommendations
        if len(allocations) > 10:
            recommendations.append(
                "Consider consolidating similar initiatives to improve resource efficiency"
            )

        # Risk recommendations
        critical_allocations = [a for a in allocations if a.priority_score > 0.9]
        if len(critical_allocations) > 3:
            recommendations.append(
                "Monitor critical allocations closely and maintain contingency resources"
            )

        return recommendations

    async def _create_fallback_allocation(
        self,
        initiatives: List[BusinessInitiative],
        constraints: List[ResourceConstraint],
    ) -> AllocationResult:
        """Create a basic fallback allocation when optimization fails."""
        allocations = []

        # Simple equal distribution among top initiatives
        top_initiatives = sorted(
            initiatives, key=lambda i: i.estimated_roi, reverse=True
        )[:3]

        for constraint in constraints:
            available = (
                constraint.total_available - constraint.allocated - constraint.reserved
            )
            per_initiative = available / len(top_initiatives) if top_initiatives else 0

            for initiative in top_initiatives:
                if per_initiative > 0:
                    allocation = ResourceAllocation(
                        initiative_id=initiative.initiative_id,
                        resource_type=constraint.resource_type,
                        amount=per_initiative,
                        unit=constraint.unit,
                        justification=f"Equal distribution allocation for {initiative.name}",
                        priority_score=0.5,
                    )
                    allocations.append(allocation)

        return AllocationResult(
            allocations=allocations,
            total_satisfaction=0.5,
            unmet_demands=[],
            resource_utilization={c.resource_type: 0.5 for c in constraints},
            optimization_score=0.5,
            recommendations=[
                "Review allocation strategy",
                "Gather more detailed requirements",
            ],
        )
