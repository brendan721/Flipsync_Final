#!/usr/bin/env python3
"""
Cost Tracking System for FlipSync AI Operations
===============================================

This module provides comprehensive cost tracking and budget management
for FlipSync's AI-powered operations across the 35+ agent architecture.

Features:
- Real-time cost tracking per operation
- Daily/monthly budget management
- Model usage analytics
- Cost optimization recommendations
- Integration with intelligent model router
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class CostCategory(Enum):
    """Categories for cost tracking."""

    VISION_ANALYSIS = "vision_analysis"
    TEXT_GENERATION = "text_generation"
    CONVERSATION = "conversation"
    MARKET_RESEARCH = "market_research"
    CONTENT_CREATION = "content_creation"
    SHIPPING_SERVICES = "shipping_services"
    PAYMENT_PROCESSING = "payment_processing"
    INVENTORY_MANAGEMENT = "inventory_management"


@dataclass
class CostEntry:
    """Individual cost entry for tracking."""

    timestamp: datetime
    category: CostCategory
    model: str
    operation: str
    cost: float
    agent_id: str
    workflow_id: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time: Optional[float] = None


@dataclass
class BudgetAlert:
    """Budget alert for monitoring."""

    alert_type: str
    threshold: float
    current_value: float
    message: str
    timestamp: datetime


class CostTracker:
    """
    Comprehensive cost tracking system for FlipSync AI operations.

    Tracks costs across all AI operations and provides budget management
    with real-time monitoring and alerting capabilities.
    """

    def __init__(self, daily_budget: float = 50.0, monthly_budget: float = 1500.0):
        """Initialize cost tracker with budget limits."""
        self.daily_budget = daily_budget
        self.monthly_budget = monthly_budget

        # Cost storage
        self.cost_entries: List[CostEntry] = []
        self.daily_costs: Dict[str, float] = {}  # date -> cost
        self.monthly_costs: Dict[str, float] = {}  # month -> cost

        # Budget tracking
        self.current_daily_cost = 0.0
        self.current_monthly_cost = 0.0
        self.budget_reset_time = self._get_next_reset_time()

        # Alerts
        self.alerts: List[BudgetAlert] = []
        self.alert_thresholds = [0.5, 0.8, 0.9, 1.0]  # 50%, 80%, 90%, 100%
        self.alerts_sent = set()

        # Analytics
        self.model_usage_stats: Dict[str, Dict[str, Any]] = {}
        self.category_stats: Dict[CostCategory, Dict[str, Any]] = {}

        logger.info(
            f"CostTracker initialized: ${daily_budget:.2f} daily, ${monthly_budget:.2f} monthly"
        )

    async def record_cost(
        self,
        category: CostCategory,
        model: str,
        operation: str,
        cost: float,
        agent_id: str,
        workflow_id: Optional[str] = None,
        tokens_used: Optional[int] = None,
        response_time: Optional[float] = None,
    ):
        """Record a cost entry and update tracking."""

        # Create cost entry
        entry = CostEntry(
            timestamp=datetime.now(),
            category=category,
            model=model,
            operation=operation,
            cost=cost,
            agent_id=agent_id,
            workflow_id=workflow_id,
            tokens_used=tokens_used,
            response_time=response_time,
        )

        # Store entry
        self.cost_entries.append(entry)

        # Update current costs
        self.current_daily_cost += cost
        self.current_monthly_cost += cost

        # Update daily tracking
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_costs[today] = self.daily_costs.get(today, 0.0) + cost

        # Update monthly tracking
        month = datetime.now().strftime("%Y-%m")
        self.monthly_costs[month] = self.monthly_costs.get(month, 0.0) + cost

        # Update analytics
        await self._update_analytics(entry)

        # Check budget alerts
        await self._check_budget_alerts()

        logger.debug(
            f"Cost recorded: {category.value} ${cost:.4f} (daily: ${self.current_daily_cost:.2f})"
        )

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""

        # Reset costs if needed
        await self._reset_costs_if_needed()

        return {
            "daily_budget": self.daily_budget,
            "monthly_budget": self.monthly_budget,
            "current_daily_cost": self.current_daily_cost,
            "current_monthly_cost": self.current_monthly_cost,
            "daily_budget_utilization": (self.current_daily_cost / self.daily_budget)
            * 100,
            "monthly_budget_utilization": (
                self.current_monthly_cost / self.monthly_budget
            )
            * 100,
            "total_requests": len(self.cost_entries),
            "model_usage": self.model_usage_stats,
            "category_breakdown": self._get_category_breakdown(),
            "recent_alerts": [asdict(alert) for alert in self.alerts[-5:]],
            "cost_trends": self._get_cost_trends(),
        }

    async def get_cost_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Generate cost optimization recommendations."""

        recommendations = []

        # Analyze model usage patterns
        for model, stats in self.model_usage_stats.items():
            if stats["total_cost"] > 10.0:  # Significant cost
                avg_cost = stats["total_cost"] / stats["usage_count"]

                if "gpt-4o" in model.lower() and avg_cost > 0.01:
                    recommendations.append(
                        {
                            "type": "model_optimization",
                            "priority": "high",
                            "model": model,
                            "suggestion": f"Consider using GPT-4o-mini for {model} operations",
                            "potential_savings": stats["total_cost"] * 0.85,
                            "impact": "85% cost reduction with minimal quality impact",
                        }
                    )

        # Analyze category spending
        for category, stats in self.category_stats.items():
            if stats["total_cost"] > 20.0:  # High spending category
                recommendations.append(
                    {
                        "type": "category_optimization",
                        "priority": "medium",
                        "category": category.value,
                        "suggestion": f"Optimize {category.value} operations with batch processing",
                        "potential_savings": stats["total_cost"] * 0.2,
                        "impact": "20% cost reduction through efficiency improvements",
                    }
                )

        # Budget utilization recommendations
        daily_utilization = (self.current_daily_cost / self.daily_budget) * 100
        if daily_utilization > 80:
            recommendations.append(
                {
                    "type": "budget_management",
                    "priority": "urgent",
                    "suggestion": "Implement stricter rate limiting to control daily spending",
                    "current_utilization": daily_utilization,
                    "impact": "Prevent budget overruns and maintain cost control",
                }
            )

        return recommendations

    def _get_category_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get cost breakdown by category."""
        breakdown = {}

        for category in CostCategory:
            category_entries = [e for e in self.cost_entries if e.category == category]

            if category_entries:
                total_cost = sum(e.cost for e in category_entries)
                avg_cost = total_cost / len(category_entries)

                breakdown[category.value] = {
                    "total_cost": total_cost,
                    "operation_count": len(category_entries),
                    "average_cost": avg_cost,
                    "percentage_of_total": (
                        (total_cost / self.current_monthly_cost) * 100
                        if self.current_monthly_cost > 0
                        else 0
                    ),
                }

        return breakdown

    def _get_cost_trends(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get cost trends over time."""

        # Daily trends (last 7 days)
        daily_trends = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            cost = self.daily_costs.get(date, 0.0)
            daily_trends.append({"date": date, "cost": cost})

        # Monthly trends (last 6 months)
        monthly_trends = []
        for i in range(6):
            date = (datetime.now() - timedelta(days=i * 30)).strftime("%Y-%m")
            cost = self.monthly_costs.get(date, 0.0)
            monthly_trends.append({"month": date, "cost": cost})

        return {"daily": daily_trends, "monthly": monthly_trends}

    async def _update_analytics(self, entry: CostEntry):
        """Update analytics with new cost entry."""

        # Update model usage stats
        model = entry.model
        if model not in self.model_usage_stats:
            self.model_usage_stats[model] = {
                "usage_count": 0,
                "total_cost": 0.0,
                "average_cost": 0.0,
                "total_tokens": 0,
                "average_response_time": 0.0,
            }

        stats = self.model_usage_stats[model]
        stats["usage_count"] += 1
        stats["total_cost"] += entry.cost
        stats["average_cost"] = stats["total_cost"] / stats["usage_count"]

        if entry.tokens_used:
            stats["total_tokens"] += entry.tokens_used

        if entry.response_time:
            # Update running average
            current_avg = stats["average_response_time"]
            count = stats["usage_count"]
            stats["average_response_time"] = (
                (current_avg * (count - 1)) + entry.response_time
            ) / count

        # Update category stats
        category = entry.category
        if category not in self.category_stats:
            self.category_stats[category] = {
                "usage_count": 0,
                "total_cost": 0.0,
                "average_cost": 0.0,
            }

        cat_stats = self.category_stats[category]
        cat_stats["usage_count"] += 1
        cat_stats["total_cost"] += entry.cost
        cat_stats["average_cost"] = cat_stats["total_cost"] / cat_stats["usage_count"]

    async def _check_budget_alerts(self):
        """Check and generate budget alerts."""

        daily_utilization = self.current_daily_cost / self.daily_budget
        monthly_utilization = self.current_monthly_cost / self.monthly_budget

        # Check daily budget alerts
        for threshold in self.alert_thresholds:
            if daily_utilization >= threshold:
                alert_key = f"daily_{threshold}"
                if alert_key not in self.alerts_sent:
                    alert = BudgetAlert(
                        alert_type="daily_budget",
                        threshold=threshold,
                        current_value=daily_utilization,
                        message=f"Daily budget {threshold*100:.0f}% utilized: ${self.current_daily_cost:.2f}/${self.daily_budget:.2f}",
                        timestamp=datetime.now(),
                    )
                    self.alerts.append(alert)
                    self.alerts_sent.add(alert_key)

                    logger.warning(alert.message)

        # Check monthly budget alerts
        for threshold in self.alert_thresholds:
            if monthly_utilization >= threshold:
                alert_key = f"monthly_{threshold}"
                if alert_key not in self.alerts_sent:
                    alert = BudgetAlert(
                        alert_type="monthly_budget",
                        threshold=threshold,
                        current_value=monthly_utilization,
                        message=f"Monthly budget {threshold*100:.0f}% utilized: ${self.current_monthly_cost:.2f}/${self.monthly_budget:.2f}",
                        timestamp=datetime.now(),
                    )
                    self.alerts.append(alert)
                    self.alerts_sent.add(alert_key)

                    logger.warning(alert.message)

    async def _reset_costs_if_needed(self):
        """Reset daily costs if new day."""

        if datetime.now() > self.budget_reset_time:
            self.current_daily_cost = 0.0
            self.budget_reset_time = self._get_next_reset_time()

            # Reset daily alerts
            daily_alerts = [key for key in self.alerts_sent if key.startswith("daily_")]
            for key in daily_alerts:
                self.alerts_sent.remove(key)

            logger.info("Daily budget reset")

    def _get_next_reset_time(self) -> datetime:
        """Get next budget reset time (midnight UTC)."""
        now = datetime.now()
        return datetime(now.year, now.month, now.day) + timedelta(days=1)


# Global cost tracker instance
_cost_tracker_instance = None


def get_cost_tracker(
    daily_budget: float = 50.0, monthly_budget: float = 1500.0
) -> CostTracker:
    """Get global cost tracker instance."""
    global _cost_tracker_instance
    if _cost_tracker_instance is None:
        _cost_tracker_instance = CostTracker(daily_budget, monthly_budget)
    return _cost_tracker_instance


# Convenience function for recording costs
async def record_ai_cost(
    category: str, model: str, operation: str, cost: float, agent_id: str, **kwargs
):
    """Convenience function to record AI operation costs."""
    tracker = get_cost_tracker()
    category_enum = CostCategory(category)
    await tracker.record_cost(
        category=category_enum,
        model=model,
        operation=operation,
        cost=cost,
        agent_id=agent_id,
        **kwargs,
    )
