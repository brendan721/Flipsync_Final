"""Market trend detection and analysis agent."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fs_agt_clean.agents.market.base_market_agent import BaseMarketUnifiedAgent
from fs_agt_clean.agents.market.specialized.market_types import TrendData
from fs_agt_clean.core.config.config_manager import ConfigManager
from fs_agt_clean.core.events.base import Event, EventType
from fs_agt_clean.core.monitoring.alerts.alert_manager import AlertManager
from fs_agt_clean.core.monitoring.alerts.models import (
    Alert,
    AlertSeverity,
    AlertStatus,
    AlertType,
)
from fs_agt_clean.core.monitoring.metric_types import MetricType
from fs_agt_clean.mobile.battery_optimizer import BatteryOptimizer

logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysisData:
    """Data class for market trends."""

    trend_type: str
    start_time: datetime
    end_time: datetime
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert trend data to dictionary format."""
        return {
            "trend_type": self.trend_type,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


class TrendDetector(BaseMarketUnifiedAgent):
    """
    UnifiedAgent for detecting market trends in real-time.

    Capabilities:
    - Pattern recognition and temporal analysis
    - Predictive analytics and seasonal adjustment
    - Anomaly detection in market data
    - Trend confidence scoring
    - Real-time trend alerts
    """

    def __init__(
        self,
        marketplace: str = "ebay",
        config_manager: Optional[ConfigManager] = None,
        alert_manager: Optional[AlertManager] = None,
        battery_optimizer: Optional[BatteryOptimizer] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize the trend detector agent.

        Args:
            marketplace: The marketplace to analyze
            config_manager: Optional configuration manager
            alert_manager: Optional alert manager
            battery_optimizer: Optional battery optimizer for mobile efficiency
            config: Optional configuration dictionary
        """
        agent_id = str(uuid4())
        if config_manager is None:
            config_manager = ConfigManager()
        if alert_manager is None:
            alert_manager = AlertManager()
        if battery_optimizer is None:
            battery_optimizer = BatteryOptimizer()

        super().__init__(
            agent_id,
            marketplace,
            config_manager,
            alert_manager,
            battery_optimizer,
            config,
        )
        self.trends: List[TrendAnalysisData] = []

    def _get_required_config_fields(self) -> List[str]:
        """Get required configuration fields."""
        fields = super()._get_required_config_fields()
        fields.extend(
            [
                "trend_threshold",
                "analysis_interval",
                "confidence_threshold",
                "data_window_size",
                "seasonal_adjustment",
            ]
        )
        return fields

    async def analyze_trend(
        self, market_data: Dict[str, Any]
    ) -> Optional[TrendAnalysisData]:
        """Analyze market data for trends.

        Args:
            market_data: Market data to analyze

        Returns:
            Detected trend data if found, None otherwise
        """
        try:
            # Extract relevant metrics from market data
            price_data = market_data.get("price_history", [])
            volume_data = market_data.get("volume_history", [])

            if not price_data or len(price_data) < 3:
                return None

            # Perform trend analysis
            trend_type = self._detect_trend_type(price_data, volume_data)
            confidence = self._calculate_trend_confidence(price_data, volume_data)

            # Only return trends above threshold
            threshold = self.config.get("trend_threshold", 0.5)
            if confidence < threshold:
                return None

            return TrendAnalysisData(
                trend_type=trend_type,
                start_time=datetime.now(timezone.utc) - timedelta(hours=24),
                end_time=datetime.now(timezone.utc),
                confidence=confidence,
                metadata={
                    "price_change": self._calculate_price_change(price_data),
                    "volume_change": self._calculate_volume_change(volume_data),
                    "market_segment": market_data.get("category", "unknown"),
                },
            )

        except Exception as e:
            logger.error("Error analyzing trend: %s", e)
            return None

    async def get_historical_trends(self, timeframe: str) -> List[TrendAnalysisData]:
        """Get historical trends for a given timeframe.

        Args:
            timeframe: Time period to get trends for

        Returns:
            List of historical trends
        """
        # Filter trends based on timeframe
        cutoff_time = self._parse_timeframe(timeframe)
        return [trend for trend in self.trends if trend.start_time >= cutoff_time]

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle marketplace events.

        Args:
            event: Event to process
        """
        event_type = event.get("type")
        if event_type == EventType.DATA_ACQUIRED.value:
            if trend := await self.analyze_trend(event.get("data", {})):
                self.trends.append(trend)
                await self._send_trend_alert(trend)
        else:
            await super()._handle_event(event)

    async def _send_trend_alert(self, trend: TrendAnalysisData) -> None:
        """Send alert for detected trend."""
        try:
            alert = Alert(
                alert_id=str(uuid4()),
                severity=AlertSeverity.LOW,
                alert_type=AlertType.CUSTOM,
                message=f"New {trend.trend_type} trend detected with {trend.confidence:.2%} confidence",
                metric_type=MetricType.GAUGE,
                metric_value=trend.confidence,
                threshold=self.config.get("trend_threshold", 0.5),
                timestamp=datetime.now(timezone.utc),
                status=AlertStatus.NEW,
                labels={
                    "marketplace": self.marketplace,
                    "trend_type": trend.trend_type,
                },
            )
            await self.alert_manager.process_alert(alert)
        except Exception as e:
            logger.error("Error sending trend alert: %s", e)

    def _detect_trend_type(
        self, price_data: List[float], volume_data: List[float]
    ) -> str:
        """Detect the type of trend from price and volume data."""
        if len(price_data) < 2:
            return "insufficient_data"

        price_change = (price_data[-1] - price_data[0]) / price_data[0]
        volume_change = (
            (volume_data[-1] - volume_data[0]) / volume_data[0] if volume_data else 0
        )

        if price_change > 0.05 and volume_change > 0.1:
            return "bullish_momentum"
        elif price_change < -0.05 and volume_change > 0.1:
            return "bearish_momentum"
        elif abs(price_change) < 0.02:
            return "sideways_consolidation"
        elif price_change > 0.02:
            return "upward_trend"
        elif price_change < -0.02:
            return "downward_trend"
        else:
            return "neutral"

    def _calculate_trend_confidence(
        self, price_data: List[float], volume_data: List[float]
    ) -> float:
        """Calculate confidence level for the detected trend."""
        if len(price_data) < 3:
            return 0.0

        # Calculate price volatility
        price_changes = [
            abs((price_data[i] - price_data[i - 1]) / price_data[i - 1])
            for i in range(1, len(price_data))
        ]
        volatility = sum(price_changes) / len(price_changes)

        # Lower volatility = higher confidence
        volatility_score = max(0, 1 - volatility * 10)

        # Data quality score based on sample size
        sample_score = min(1.0, len(price_data) / 10)

        # Volume confirmation score
        volume_score = 0.5
        if volume_data and len(volume_data) >= 2:
            volume_trend = (volume_data[-1] - volume_data[0]) / volume_data[0]
            volume_score = min(1.0, abs(volume_trend) + 0.5)

        # Combined confidence score
        confidence = volatility_score * 0.4 + sample_score * 0.3 + volume_score * 0.3
        return min(1.0, max(0.0, confidence))

    def _calculate_price_change(self, price_data: List[float]) -> float:
        """Calculate percentage price change."""
        if len(price_data) < 2:
            return 0.0
        return (price_data[-1] - price_data[0]) / price_data[0]

    def _calculate_volume_change(self, volume_data: List[float]) -> float:
        """Calculate percentage volume change."""
        if not volume_data or len(volume_data) < 2:
            return 0.0
        return (volume_data[-1] - volume_data[0]) / volume_data[0]

    def _parse_timeframe(self, timeframe: str) -> datetime:
        """Parse timeframe string to datetime cutoff."""
        now = datetime.now(timezone.utc)
        if timeframe == "1h":
            return now - timedelta(hours=1)
        elif timeframe == "24h":
            return now - timedelta(hours=24)
        elif timeframe == "7d":
            return now - timedelta(days=7)
        elif timeframe == "30d":
            return now - timedelta(days=30)
        else:
            return now - timedelta(hours=24)  # Default to 24h

    async def get_trend_summary(self) -> Dict[str, Any]:
        """Get summary of current trends."""
        recent_trends = await self.get_historical_trends("24h")

        trend_counts = {}
        total_confidence = 0

        for trend in recent_trends:
            trend_type = trend.trend_type
            trend_counts[trend_type] = trend_counts.get(trend_type, 0) + 1
            total_confidence += trend.confidence

        avg_confidence = total_confidence / len(recent_trends) if recent_trends else 0

        return {
            "total_trends": len(recent_trends),
            "trend_distribution": trend_counts,
            "average_confidence": avg_confidence,
            "dominant_trend": (
                max(trend_counts.items(), key=lambda x: x[1])[0]
                if trend_counts
                else None
            ),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
