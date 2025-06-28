"""Analytics engine for campaign performance analysis."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from fs_agt_clean.core.monitoring.metrics_collector import MetricsCollector
from fs_agt_clean.core.services.resource_management import ResourceManager

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class CampaignMetrics:
    """Campaign performance metrics."""

    campaign_id: str
    impressions: int = 0
    clicks: int = 0
    conversions: int = 0
    revenue: float = 0.0
    cost: float = 0.0
    timestamp: datetime = datetime.now()


class AnalyticsEngine:
    """Engine for analyzing campaign performance."""

    def __init__(
        self,
        resource_manager: ResourceManager,
        metrics_collector: MetricsCollector,
    ):
        """Initialize analytics engine.

        Args:
            resource_manager: Resource manager instance
            metrics_collector: Metrics collector instance
        """
        self.resource_manager = resource_manager
        self.metrics_collector = metrics_collector
        self._campaign_metrics: Dict[str, List[CampaignMetrics]] = {}

    async def record_metrics(self, metrics: CampaignMetrics) -> None:
        """Record campaign metrics.

        Args:
            metrics: Campaign metrics to record
        """
        if metrics.campaign_id not in self._campaign_metrics:
            self._campaign_metrics[metrics.campaign_id] = []
        self._campaign_metrics[metrics.campaign_id].append(metrics)
        await self.metrics_collector.record(
            "campaign.impressions",
            metrics.impressions,
            {"campaign_id": metrics.campaign_id},
        )
        await self.metrics_collector.record(
            "campaign.clicks", metrics.clicks, {"campaign_id": metrics.campaign_id}
        )
        await self.metrics_collector.record(
            "campaign.conversions",
            metrics.conversions,
            {"campaign_id": metrics.campaign_id},
        )
        await self.metrics_collector.record(
            "campaign.revenue", metrics.revenue, {"campaign_id": metrics.campaign_id}
        )
        await self.metrics_collector.record(
            "campaign.cost", metrics.cost, {"campaign_id": metrics.campaign_id}
        )

    def get_campaign_metrics(
        self,
        campaign_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> List[CampaignMetrics]:
        """Get metrics for a campaign.

        Args:
            campaign_id: Campaign identifier
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of campaign metrics
        """
        if campaign_id not in self._campaign_metrics:
            return []
        metrics = self._campaign_metrics[campaign_id]
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        return metrics

    def calculate_campaign_performance(self, campaign_id: str) -> Dict[str, float]:
        """Calculate performance metrics for a campaign.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Dictionary of performance metrics
        """
        metrics = self.get_campaign_metrics(campaign_id)
        if not metrics:
            return {"ctr": 0.0, "cvr": 0.0, "roas": 0.0, "cpa": 0.0}
        total_impressions = sum(m.impressions for m in metrics)
        total_clicks = sum(m.clicks for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)
        total_revenue = sum(m.revenue for m in metrics)
        total_cost = sum(m.cost for m in metrics)
        ctr = total_clicks / total_impressions if total_impressions > 0 else 0
        cvr = total_conversions / total_clicks if total_clicks > 0 else 0
        roas = total_revenue / total_cost if total_cost > 0 else 0
        cpa = total_cost / total_conversions if total_conversions > 0 else 0
        return {"ctr": ctr, "cvr": cvr, "roas": roas, "cpa": cpa}

    def clear_metrics(
        self,
        campaign_id: Optional[str] = None,
        before_time: Optional[datetime] = None,
    ) -> None:
        """Clear recorded metrics.

        Args:
            campaign_id: Optional campaign ID filter
            before_time: Optional time filter
        """
        if campaign_id:
            if campaign_id in self._campaign_metrics:
                if before_time:
                    self._campaign_metrics[campaign_id] = [
                        m
                        for m in self._campaign_metrics[campaign_id]
                        if m.timestamp > before_time
                    ]
                else:
                    del self._campaign_metrics[campaign_id]
        elif before_time:
            for camp_id in list(self._campaign_metrics.keys()):
                self._campaign_metrics[camp_id] = [
                    m
                    for m in self._campaign_metrics[camp_id]
                    if m.timestamp > before_time
                ]
        else:
            self._campaign_metrics.clear()
