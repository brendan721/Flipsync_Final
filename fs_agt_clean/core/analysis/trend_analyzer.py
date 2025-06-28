"""
Trend Analysis for market data.

This module provides trend analysis capabilities for market data, including
detection of trends, seasonality, and pattern recognition.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

from fs_agt_clean.core.analysis.models import MarketTrend, TrendDirection

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyzes market trends using statistical methods.

    This class provides methods for detecting trends, seasonality, and patterns
    in market data using various statistical techniques.
    """

    def __init__(self, config: Optional[Dict[str, Union[int, float, str]]] = None):
        """
        Initialize the trend analyzer.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.min_data_points = self.config.get("min_data_points", 5)
        self.significance_level = self.config.get("significance_level", 0.05)
        self.trend_threshold = self.config.get("trend_threshold", 0.1)
        self.seasonality_threshold = self.config.get("seasonality_threshold", 0.2)

    async def analyze_trend(
        self, data: List[float], timestamps: List[datetime], metric_name: str
    ) -> MarketTrend:
        """
        Analyze trend in time series data.

        Args:
            data: List of data points
            timestamps: List of corresponding timestamps
            metric_name: Name of the metric being analyzed

        Returns:
            MarketTrend object with trend analysis results
        """
        if len(data) < self.min_data_points:
            return MarketTrend(
                metric=metric_name,
                direction=TrendDirection.STABLE,
                magnitude=0.0,
                confidence=0.0,
                timeframe_days=self._calculate_timeframe_days(timestamps),
                data_points=data,
                timestamps=timestamps,
                description="Insufficient data for trend analysis",
            )

        # Calculate trend using linear regression
        x = list(range(len(data)))
        y = data

        slope, intercept, r_value, p_value, std_err = self._linear_regression(x, y)

        # Determine trend direction
        direction = self._determine_trend_direction(slope, p_value, data)

        # Calculate magnitude (normalized slope)
        magnitude = self._calculate_magnitude(slope, data)

        # Calculate confidence based on r-squared and p-value
        confidence = self._calculate_confidence(r_value, p_value)

        # Generate description
        description = self._generate_trend_description(
            direction, magnitude, confidence, metric_name
        )

        return MarketTrend(
            metric=metric_name,
            direction=direction,
            magnitude=magnitude,
            confidence=confidence,
            timeframe_days=self._calculate_timeframe_days(timestamps),
            data_points=data,
            timestamps=timestamps,
            description=description,
        )

    def _determine_trend_direction(
        self, slope: float, p_value: float, data: List[float]
    ) -> TrendDirection:
        """
        Determine the direction of a trend.

        Args:
            slope: Slope of the linear regression
            p_value: P-value of the linear regression
            data: Original data points

        Returns:
            TrendDirection enum value
        """
        # Check if trend is statistically significant
        if p_value > self.significance_level:
            # Check for volatility
            if self._is_volatile(data):
                return TrendDirection.VOLATILE
            return TrendDirection.STABLE

        if slope > self.trend_threshold:
            return TrendDirection.INCREASING
        elif slope < -self.trend_threshold:
            return TrendDirection.DECREASING
        else:
            return TrendDirection.STABLE

    def _is_volatile(self, data: List[float]) -> bool:
        """
        Check if data shows volatility.

        Args:
            data: List of data points

        Returns:
            True if data is volatile, False otherwise
        """
        if len(data) < 4:
            return False

        # Calculate differences between consecutive points
        diffs = [abs(data[i] - data[i - 1]) for i in range(1, len(data))]

        # Calculate coefficient of variation
        mean_diff = sum(diffs) / len(diffs)
        std_diff = math.sqrt(sum((d - mean_diff) ** 2 for d in diffs) / len(diffs))

        # Check if coefficient of variation is high
        if mean_diff == 0:
            return False

        cv = std_diff / mean_diff
        return cv > 0.5  # Threshold for volatility

    def _calculate_magnitude(self, slope: float, data: List[float]) -> float:
        """
        Calculate the magnitude of a trend.

        Args:
            slope: Slope of the linear regression
            data: Original data points

        Returns:
            Normalized magnitude between 0 and 1
        """
        if not data:
            return 0.0

        # Normalize slope by the mean of the data
        mean_value = sum(data) / len(data)
        if mean_value == 0:
            return 0.0

        # Calculate relative change over the period
        relative_change = abs(slope * len(data) / mean_value)

        # Cap at 1.0
        return min(relative_change, 1.0)

    def _calculate_confidence(self, r_value: float, p_value: float) -> float:
        """
        Calculate confidence in the trend.

        Args:
            r_value: R-value of the linear regression
            p_value: P-value of the linear regression

        Returns:
            Confidence score between 0 and 1
        """
        # R-squared measures goodness of fit
        r_squared = r_value**2

        # P-value measures statistical significance
        p_factor = 1.0 - min(p_value / self.significance_level, 1.0)

        # Combine both factors
        confidence = (r_squared * 0.7) + (p_factor * 0.3)

        return min(confidence, 1.0)

    def _linear_regression(
        self, x: List[float], y: List[float]
    ) -> Tuple[float, float, float, float, float]:
        """
        Calculate linear regression statistics.

        Args:
            x: Independent variable values
            y: Dependent variable values

        Returns:
            Tuple of (slope, intercept, r_value, p_value, std_err)
        """
        n = len(x)
        if n < 2:
            return 0.0, 0.0, 0.0, 1.0, 0.0

        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        # Calculate slope and intercept
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0, y_mean, 0.0, 1.0, 0.0

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Calculate correlation coefficient
        x_var = sum((x[i] - x_mean) ** 2 for i in range(n))
        y_var = sum((y[i] - y_mean) ** 2 for i in range(n))

        if x_var == 0 or y_var == 0:
            r_value = 0.0
        else:
            r_value = numerator / math.sqrt(x_var * y_var)

        # Calculate standard error (simplified)
        y_pred = [intercept + slope * x[i] for i in range(n)]
        residuals = [(y[i] - y_pred[i]) ** 2 for i in range(n)]
        mse = sum(residuals) / max(n - 2, 1)
        std_err = math.sqrt(mse / max(denominator, 1))

        # Simplified p-value calculation (not exact but reasonable approximation)
        if n > 2:
            t_stat = abs(slope) / max(std_err, 1e-10)
            # Rough approximation for p-value
            p_value = max(0.001, 2 * (1 - min(0.999, t_stat / (t_stat + n - 2))))
        else:
            p_value = 1.0

        return slope, intercept, r_value, p_value, std_err

    def _calculate_timeframe_days(self, timestamps: List[datetime]) -> int:
        """
        Calculate the timeframe in days.

        Args:
            timestamps: List of timestamps

        Returns:
            Timeframe in days
        """
        if not timestamps or len(timestamps) < 2:
            return 0

        # Sort timestamps to ensure correct calculation
        sorted_timestamps = sorted(timestamps)

        # Calculate difference between first and last timestamp
        delta = sorted_timestamps[-1] - sorted_timestamps[0]

        return max(delta.days, 1)  # Ensure at least 1 day

    def _generate_trend_description(
        self,
        direction: TrendDirection,
        magnitude: float,
        confidence: float,
        metric_name: str,
    ) -> str:
        """
        Generate a human-readable description of the trend.

        Args:
            direction: Direction of the trend
            magnitude: Magnitude of the trend
            confidence: Confidence in the trend
            metric_name: Name of the metric

        Returns:
            Human-readable description
        """
        # Describe magnitude
        if magnitude < 0.1:
            magnitude_desc = "slight"
        elif magnitude < 0.3:
            magnitude_desc = "moderate"
        elif magnitude < 0.6:
            magnitude_desc = "significant"
        else:
            magnitude_desc = "strong"

        # Describe confidence
        if confidence < 0.3:
            confidence_desc = "low confidence"
        elif confidence < 0.7:
            confidence_desc = "moderate confidence"
        else:
            confidence_desc = "high confidence"

        # Generate description based on direction
        if direction == TrendDirection.INCREASING:
            return f"{magnitude_desc.capitalize()} increasing trend in {metric_name} with {confidence_desc}"
        elif direction == TrendDirection.DECREASING:
            return f"{magnitude_desc.capitalize()} decreasing trend in {metric_name} with {confidence_desc}"
        elif direction == TrendDirection.VOLATILE:
            return f"Volatile pattern in {metric_name} with {confidence_desc}"
        else:
            return f"Stable {metric_name} with {confidence_desc}"

    async def detect_seasonality(
        self, data: List[float], timestamps: List[datetime]
    ) -> Dict[str, Union[bool, float, List[int]]]:
        """
        Detect seasonality in time series data.

        Args:
            data: List of data points
            timestamps: List of corresponding timestamps

        Returns:
            Dictionary with seasonality analysis results
        """
        if len(data) < 12:  # Need at least a year of data for reliable seasonality
            return {
                "has_seasonality": False,
                "seasonality_strength": 0.0,
                "seasonal_periods": [],
                "confidence": 0.0,
            }

        # Detrend the data
        x = list(range(len(data)))
        slope, intercept, _, _, _ = self._linear_regression(x, data)
        trend = [slope * x[i] + intercept for i in range(len(data))]
        detrended = [data[i] - trend[i] for i in range(len(data))]

        # Calculate autocorrelation
        autocorr = self._autocorrelation(detrended)

        # Find peaks in autocorrelation (simplified peak detection)
        peaks = self._find_peaks(autocorr, height=0.1, distance=2)

        # Filter out peaks that are too small
        significant_peaks = [
            p for p in peaks if autocorr[p] > self.seasonality_threshold
        ]

        # Calculate seasonality strength
        if significant_peaks:
            seasonality_strength = max(autocorr[p] for p in significant_peaks)
        else:
            seasonality_strength = 0.0

        # Calculate confidence
        confidence = min(seasonality_strength * 1.5, 1.0)

        return {
            "has_seasonality": seasonality_strength > self.seasonality_threshold,
            "seasonality_strength": seasonality_strength,
            "seasonal_periods": significant_peaks,
            "confidence": confidence,
        }

    def _autocorrelation(self, x: List[float]) -> List[float]:
        """
        Calculate autocorrelation of a time series.

        Args:
            x: Time series data

        Returns:
            Autocorrelation values
        """
        n = len(x)
        if n == 0:
            return []

        # Calculate mean and variance
        mean_x = sum(x) / n
        variance = sum((val - mean_x) ** 2 for val in x) / n

        if variance == 0:
            return [1.0] + [0.0] * (n - 1)

        # Center the data
        centered = [val - mean_x for val in x]

        # Calculate autocorrelation
        autocorr = []
        for lag in range(n):
            if lag == 0:
                autocorr.append(1.0)
            else:
                correlation = sum(
                    centered[i] * centered[i - lag] for i in range(lag, n)
                )
                correlation /= variance * (n - lag)
                autocorr.append(correlation)

        return autocorr

    def _find_peaks(
        self, data: List[float], height: float = 0.1, distance: int = 2
    ) -> List[int]:
        """
        Simple peak detection algorithm.

        Args:
            data: Data to find peaks in
            height: Minimum height for peaks
            distance: Minimum distance between peaks

        Returns:
            List of peak indices
        """
        peaks = []
        n = len(data)

        for i in range(1, n - 1):
            # Check if current point is higher than neighbors
            if data[i] > data[i - 1] and data[i] > data[i + 1] and data[i] >= height:
                # Check distance constraint
                if not peaks or i - peaks[-1] >= distance:
                    peaks.append(i)

        return peaks
