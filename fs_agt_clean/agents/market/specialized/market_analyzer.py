import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, cast

import numpy as np

from fs_agt_clean.agents.market.specialized.market_types import (
    CompetitorProfile,
    MarketData,
)
from fs_agt_clean.core.models.vector_store.store import VectorStore
from fs_agt_clean.core.monitoring.alerts.manager import AlertManager
from fs_agt_clean.services.marketplace.amazon.service import AmazonService
from fs_agt_clean.services.marketplace.ebay.service import EbayService

logger: logging.Logger = logging.getLogger(__name__)


# Create a simple MetricsMixin class to replace the missing import
class MetricsMixin:
    """Simple metrics mixin for market analyzer."""

    def __init__(self, *args, **kwargs):
        self.metrics = {}

    def record_metric(self, name: str, value: float) -> None:
        """Record a metric."""
        self.metrics[name] = value

    def get_metric(self, name: str) -> Optional[float]:
        """Get a metric value."""
        return self.metrics.get(name)


class MarketAnalyzer(MetricsMixin):
    """Provides centralized market analysis functionality."""

    def __init__(
        self,
        amazon_service: Optional[AmazonService] = None,
        ebay_service: Optional[EbayService] = None,
    ):
        super().__init__(service_name="market_analyzer")
        self.alert_manager = AlertManager()
        self.amazon_service = amazon_service
        self.ebay_service = ebay_service
        if not amazon_service or not ebay_service:
            raise ValueError("Both amazon_service and ebay_service must be provided")

    async def analyze_market(
        self, asin: str, category_id: Optional[str] = None, timeframe_days: int = 30
    ) -> Optional[MarketData]:
        """Analyze market data for a given product."""
        start_time = datetime.utcnow()
        try:
            await self.metrics.record_latency("analyze_market_start", 0.0)
            competitors = await self._get_competitor_data(asin)
            sales_data = await self._get_sales_data(asin, timeframe_days)
            trend_data = await self._get_trend_data(asin, category_id, timeframe_days)
            price_metrics = self._calculate_price_metrics(competitors)
            velocity = self._calculate_sales_velocity(sales_data)
            keywords = await self._get_top_keywords(asin, category_id, competitors)
            market_data = MarketData(
                average_price=price_metrics["average"],
                median_price=price_metrics["median"],
                price_range=(price_metrics["min"], price_metrics["max"]),
                total_listings=len(competitors),
                active_listings=sum((1 for c in competitors if c["active"])),
                sales_velocity=velocity,
                top_keywords=keywords,
                competitors=competitors,
                trends=trend_data,
                timestamp=datetime.utcnow(),
            )
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds()
            await self.metrics.record_latency("analyze_market", latency)
            return market_data
        except Exception as e:
            await self.metrics.record_error("analyze_market", str(e))
            raise

    async def _get_competitor_data(self, asin: str) -> List[Dict[str, Any]]:
        """Get competitor data for a product."""
        try:
            if not self.amazon_service:
                return []
            product_data = await self.amazon_service.get_product_data(asin)
            return product_data.get("competitors", [])
        except Exception as e:
            logger.error("Failed to get competitor data: %s", str(e))
            return []

    async def _get_sales_data(self, asin: str, timeframe_days: int) -> Dict[str, Any]:
        """Get sales data for a product."""
        try:
            if not self.amazon_service:
                return {}
            product_data = await self.amazon_service.get_product_data(asin)
            return product_data.get("sales_data", {})
        except Exception as e:
            logger.error("Failed to get sales data: %s", str(e))
            return {}

    async def _get_trend_data(
        self, asin: str, category_id: Optional[str], timeframe_days: int
    ) -> Dict[str, Any]:
        """Get trend data for a product."""
        try:
            if not self.amazon_service:
                return {}
            product_data = await self.amazon_service.get_product_data(asin)
            return product_data.get("trend_data", {})
        except Exception as e:
            logger.error("Failed to get trend data: %s", str(e))
            return {}

    def _calculate_price_metrics(
        self, competitors: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate price distribution metrics."""
        try:
            prices = [
                float(comp["price"]) for comp in competitors if float(comp["price"]) > 0
            ]
            if not prices:
                return {
                    "average": 0.0,
                    "median": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                }
            return {
                "average": float(np.mean(prices)),
                "median": float(np.median(prices)),
                "min": float(min(prices)),
                "max": float(max(prices)),
            }
        except Exception as e:
            logger.error("Failed to calculate price metrics: %s", str(e))
            return {
                "average": 0.0,
                "median": 0.0,
                "min": 0.0,
                "max": 0.0,
            }

    def _calculate_sales_velocity(self, sales_data: Dict[str, Any]) -> float:
        """Calculate sales velocity metric."""
        try:
            if not sales_data:
                return 0.0
            recent_sales = sales_data.get("recent_sales", 0)
            timeframe_days = sales_data.get("timeframe_days", 30)
            return recent_sales / timeframe_days if timeframe_days > 0 else 0.0
        except Exception as e:
            logger.error("Failed to calculate sales velocity: %s", str(e))
            return 0.0

    async def _get_top_keywords(
        self, asin: str, category_id: Optional[str], competitors: List[Dict[str, Any]]
    ) -> List[str]:
        """Get top keywords for a product."""
        try:
            if not self.amazon_service:
                return []
            product_data = await self.amazon_service.get_product_data(asin)
            return product_data.get("keywords", [])
        except Exception as e:
            logger.error("Failed to get top keywords: %s", str(e))
            return []
