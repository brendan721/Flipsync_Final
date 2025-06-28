"""
Enhanced Trend Detector UnifiedAgent for FlipSync
Detects market trends, seasonal patterns, and emerging opportunities using available dependencies.
"""

import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fs_agt_clean.agents.base_conversational_agent import (
    UnifiedAgentResponse,
    BaseConversationalUnifiedAgent,
)
from fs_agt_clean.core.ai.prompt_templates import UnifiedAgentRole

logger = logging.getLogger(__name__)


@dataclass
class TrendData:
    """Market trend data structure."""

    product_category: str
    time_period: str
    price_trend: float  # Percentage change
    volume_trend: float  # Percentage change
    search_trend: float  # Relative search volume
    seasonality_score: float
    confidence: float
    detected_at: datetime


@dataclass
class TrendAlert:
    """Trend alert structure."""

    alert_id: str
    trend_type: str  # "price_increase", "demand_spike", "seasonal_peak", etc.
    product_category: str
    severity: str  # "low", "medium", "high"
    description: str
    recommended_action: str
    confidence: float
    created_at: datetime


class EnhancedTrendDetector(BaseConversationalUnifiedAgent):
    """
    Enhanced trend detector using available dependencies.

    Capabilities:
    - Market trend analysis and detection
    - Seasonal pattern identification
    - Price trend forecasting
    - Demand spike detection
    - Opportunity identification
    """

    def __init__(
        self, agent_id: str = "enhanced_trend_detector", use_fast_model: bool = True
    ):
        """Initialize the enhanced trend detector."""
        super().__init__(
            agent_role=UnifiedAgentRole.MARKET,
            agent_id=agent_id,
            use_fast_model=use_fast_model,
        )

        # Trend tracking
        self.trend_data: Dict[str, List[TrendData]] = {}
        self.trend_alerts: List[TrendAlert] = []
        self.price_history: Dict[str, pd.DataFrame] = {}

        # Analysis parameters
        self.trend_threshold = 0.15  # 15% change threshold
        self.seasonality_window = 30  # Days for seasonality analysis

        logger.info(f"EnhancedTrendDetector initialized: {self.agent_id}")

    async def _get_agent_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get agent-specific context for prompt generation."""
        return {
            "agent_type": "enhanced_trend_detector",
            "capabilities": [
                "Market trend analysis",
                "Seasonal pattern identification",
                "Price trend forecasting",
                "Demand spike detection",
                "Opportunity identification",
            ],
            "tracked_categories": len(self.trend_data),
            "active_alerts": len(self.trend_alerts),
        }

    async def detect_trends(
        self, product_category: str, time_period: str = "30d"
    ) -> TrendData:
        """Detect trends for a specific product category."""
        try:
            # Generate mock historical data for analysis
            historical_data = self._generate_mock_historical_data(
                product_category, time_period
            )

            # Store price history
            self.price_history[product_category] = historical_data

            # Analyze trends
            trend_analysis = await self._analyze_trends(
                historical_data, product_category
            )

            # Store trend data
            if product_category not in self.trend_data:
                self.trend_data[product_category] = []
            self.trend_data[product_category].append(trend_analysis)

            # Check for alerts
            await self._check_trend_alerts(trend_analysis)

            return trend_analysis

        except Exception as e:
            logger.error(f"Error detecting trends: {e}")
            raise

    def _generate_mock_historical_data(
        self, category: str, time_period: str
    ) -> pd.DataFrame:
        """Generate mock historical data for trend analysis."""
        # Parse time period
        days = 30
        if time_period.endswith("d"):
            days = int(time_period[:-1])
        elif time_period.endswith("w"):
            days = int(time_period[:-1]) * 7
        elif time_period.endswith("m"):
            days = int(time_period[:-1]) * 30

        # Generate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")

        # Base values by category
        base_price = 100.0
        base_volume = 1000
        if "iphone" in category.lower() or "phone" in category.lower():
            base_price = 800.0
            base_volume = 500
        elif "macbook" in category.lower() or "laptop" in category.lower():
            base_price = 1500.0
            base_volume = 200
        elif "electronics" in category.lower():
            base_price = 300.0
            base_volume = 800

        # Generate realistic trends
        data = []
        for i, date in enumerate(date_range):
            # Add seasonal effects
            day_of_year = date.timetuple().tm_yday
            seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * day_of_year / 365)

            # Add weekly patterns (higher on weekends)
            weekly_factor = 1.1 if date.weekday() >= 5 else 1.0

            # Add random noise
            noise = np.random.normal(0, 0.05)

            # Add trend (slight upward trend)
            trend_factor = 1 + (i / len(date_range)) * 0.1

            price = base_price * seasonal_factor * trend_factor * (1 + noise)
            volume = base_volume * seasonal_factor * weekly_factor * (1 + noise * 0.5)
            search_volume = 100 * seasonal_factor * weekly_factor * (1 + noise * 0.3)

            data.append(
                {
                    "date": date,
                    "price": max(price, base_price * 0.5),  # Minimum price floor
                    "volume": max(int(volume), 10),  # Minimum volume
                    "search_volume": max(search_volume, 10),
                }
            )

        return pd.DataFrame(data)

    async def _analyze_trends(self, df: pd.DataFrame, category: str) -> TrendData:
        """Analyze trends in the historical data."""

        # Calculate price trend (percentage change from start to end)
        price_start = df["price"].iloc[0]
        price_end = df["price"].iloc[-1]
        price_trend = ((price_end - price_start) / price_start) * 100

        # Calculate volume trend
        volume_start = df["volume"].iloc[0]
        volume_end = df["volume"].iloc[-1]
        volume_trend = ((volume_end - volume_start) / volume_start) * 100

        # Calculate search trend
        search_start = df["search_volume"].iloc[0]
        search_end = df["search_volume"].iloc[-1]
        search_trend = ((search_end - search_start) / search_start) * 100

        # Calculate seasonality score using standard deviation
        price_volatility = df["price"].std() / df["price"].mean()
        seasonality_score = min(price_volatility * 10, 1.0)  # Normalize to 0-1

        # Calculate confidence based on data consistency
        confidence = self._calculate_trend_confidence(df)

        return TrendData(
            product_category=category,
            time_period="30d",
            price_trend=round(price_trend, 2),
            volume_trend=round(volume_trend, 2),
            search_trend=round(search_trend, 2),
            seasonality_score=round(seasonality_score, 3),
            confidence=confidence,
            detected_at=datetime.now(timezone.utc),
        )

    def _calculate_trend_confidence(self, df: pd.DataFrame) -> float:
        """Calculate confidence in trend analysis."""
        confidence = 0.5  # Base confidence

        # More data points = higher confidence
        if len(df) >= 30:
            confidence += 0.2
        elif len(df) >= 14:
            confidence += 0.1

        # Lower volatility = higher confidence
        price_cv = df["price"].std() / df["price"].mean()
        if price_cv < 0.1:
            confidence += 0.2
        elif price_cv < 0.2:
            confidence += 0.1

        # Consistent volume data = higher confidence
        volume_cv = df["volume"].std() / df["volume"].mean()
        if volume_cv < 0.3:
            confidence += 0.1

        return min(1.0, confidence)

    async def _check_trend_alerts(self, trend_data: TrendData):
        """Check if trends warrant alerts."""
        alerts = []

        # Price trend alerts
        if abs(trend_data.price_trend) > self.trend_threshold * 100:
            alert_type = (
                "price_increase" if trend_data.price_trend > 0 else "price_decrease"
            )
            severity = "high" if abs(trend_data.price_trend) > 25 else "medium"

            alerts.append(
                TrendAlert(
                    alert_id=f"price_{trend_data.product_category}_{datetime.now().timestamp()}",
                    trend_type=alert_type,
                    product_category=trend_data.product_category,
                    severity=severity,
                    description=f"Price trend: {trend_data.price_trend:+.1f}% over 30 days",
                    recommended_action=(
                        "Review pricing strategy"
                        if trend_data.price_trend < 0
                        else "Consider inventory increase"
                    ),
                    confidence=trend_data.confidence,
                    created_at=datetime.now(timezone.utc),
                )
            )

        # Volume trend alerts
        if trend_data.volume_trend > 30:
            alerts.append(
                TrendAlert(
                    alert_id=f"volume_{trend_data.product_category}_{datetime.now().timestamp()}",
                    trend_type="demand_spike",
                    product_category=trend_data.product_category,
                    severity="high",
                    description=f"Volume increased {trend_data.volume_trend:+.1f}% - demand spike detected",
                    recommended_action="Increase inventory and optimize pricing",
                    confidence=trend_data.confidence,
                    created_at=datetime.now(timezone.utc),
                )
            )

        # Seasonality alerts
        if trend_data.seasonality_score > 0.7:
            alerts.append(
                TrendAlert(
                    alert_id=f"seasonal_{trend_data.product_category}_{datetime.now().timestamp()}",
                    trend_type="seasonal_pattern",
                    product_category=trend_data.product_category,
                    severity="medium",
                    description=f"High seasonality detected (score: {trend_data.seasonality_score:.2f})",
                    recommended_action="Prepare for seasonal demand variations",
                    confidence=trend_data.confidence,
                    created_at=datetime.now(timezone.utc),
                )
            )

        self.trend_alerts.extend(alerts)

    async def generate_trend_forecast(
        self, category: str, days_ahead: int = 14
    ) -> Dict[str, Any]:
        """Generate trend forecast for a category."""
        try:
            if category not in self.price_history:
                await self.detect_trends(category)

            df = self.price_history[category]

            # Simple linear trend extrapolation
            x = np.arange(len(df))
            y = df["price"].values

            # Fit linear trend
            coeffs = np.polyfit(x, y, 1)
            trend_line = np.poly1d(coeffs)

            # Forecast future values
            future_x = np.arange(len(df), len(df) + days_ahead)
            forecast_prices = trend_line(future_x)

            # Calculate forecast confidence (decreases with distance)
            base_confidence = 0.8
            confidence_decay = 0.05
            forecast_confidence = [
                max(0.1, base_confidence - i * confidence_decay)
                for i in range(days_ahead)
            ]

            return {
                "category": category,
                "forecast_period": f"{days_ahead} days",
                "current_price": float(df["price"].iloc[-1]),
                "forecast_prices": [float(p) for p in forecast_prices],
                "confidence_scores": forecast_confidence,
                "trend_direction": "upward" if coeffs[0] > 0 else "downward",
                "trend_strength": abs(float(coeffs[0])),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            raise

    async def _process_response(self, response: Any) -> str:
        """Process and format the response."""
        if hasattr(response, "content"):
            return response.content
        return str(response)

    async def handle_message(
        self, message: str, conversation_id: str, user_id: str
    ) -> UnifiedAgentResponse:
        """Handle trend detection queries."""
        try:
            system_prompt = """You are FlipSync's Enhanced Trend Detector, an expert in market trend analysis and forecasting.

Your capabilities include:
- Market trend analysis and detection
- Seasonal pattern identification  
- Price trend forecasting
- Demand spike detection
- Opportunity identification using data science

Provide specific, data-driven trend insights and actionable recommendations for marketplace optimization."""

            response = await self.llm_client.generate_response(
                prompt=message, system_prompt=system_prompt
            )

            return UnifiedAgentResponse(
                content=response.content,
                agent_type="enhanced_trend_detector",
                confidence=0.9,
                response_time=response.response_time,
                metadata={
                    "tracked_categories": len(self.trend_data),
                    "active_alerts": len(self.trend_alerts),
                    "analysis_capabilities": [
                        "trend_detection",
                        "seasonality_analysis",
                        "forecasting",
                    ],
                },
            )

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return UnifiedAgentResponse(
                content="I'm having trouble processing your trend analysis request right now. Please try again.",
                agent_type="enhanced_trend_detector",
                confidence=0.1,
                response_time=0.0,
            )
