"""
Demand Forecasting for market analysis.

This module provides demand forecasting capabilities, including time series
forecasting, seasonality analysis, and external factor incorporation.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union

from fs_agt_clean.core.analysis.models import DemandForecast

logger = logging.getLogger(__name__)


class DemandForecaster:
    """
    Forecasts product demand using time series analysis.

    This class provides methods for forecasting future demand based on
    historical sales data, seasonality patterns, and external factors.
    """

    def __init__(self, config: Optional[Dict[str, Union[int, float, str]]] = None):
        """
        Initialize the demand forecaster.

        Args:
            config: Optional configuration parameters
        """
        self.config = config or {}
        self.min_data_points = self.config.get("min_data_points", 10)
        self.forecast_horizon = self.config.get("forecast_horizon", 30)  # days
        self.seasonality_periods = self.config.get(
            "seasonality_periods", [7, 30, 90, 365]
        )
        self.forecast_cache: Dict[str, DemandForecast] = {}

    async def forecast_demand(
        self,
        product_id: Optional[str] = None,
        category_id: Optional[str] = None,
        historical_data: Optional[List[Tuple[datetime, float]]] = None,
        timeframe_days: int = 30,
        external_factors: Optional[Dict[str, float]] = None,
    ) -> DemandForecast:
        """
        Forecast demand for a product or category.

        Args:
            product_id: Optional ID of the product
            category_id: Optional ID of the category
            historical_data: Optional historical sales data as (date, quantity) tuples
            timeframe_days: Number of days to forecast
            external_factors: Optional external factors affecting demand

        Returns:
            DemandForecast object with forecast results

        Raises:
            ValueError: If neither product_id nor category_id is provided
        """
        if not product_id and not category_id:
            raise ValueError("Either product_id or category_id must be provided")

        # Generate cache key
        cache_key = f"{'p' if product_id else 'c'}_{product_id or category_id}"

        # Check cache
        if cache_key in self.forecast_cache:
            cached_forecast = self.forecast_cache[cache_key]
            # Check if forecast is still valid (not expired)
            forecast_age = datetime.now() - cached_forecast.last_updated
            if forecast_age.days < 1:  # Cache for 1 day
                return cached_forecast

        # Get historical data if not provided
        if not historical_data:
            historical_data = await self._get_historical_data(product_id, category_id)

        # Check if we have enough data
        if not historical_data or len(historical_data) < self.min_data_points:
            return self._create_empty_forecast(product_id, category_id, timeframe_days)

        # Sort data by date
        historical_data.sort(key=lambda x: x[0])

        # Extract dates and values
        dates = [entry[0] for entry in historical_data]
        values = [entry[1] for entry in historical_data]

        # Detect seasonality
        seasonality_factors = self._detect_seasonality(values, dates)

        # Generate forecast
        forecast_dates, forecast_values, confidence_intervals = self._generate_forecast(
            dates, values, timeframe_days, seasonality_factors, external_factors
        )

        # Calculate total forecast and growth rate
        total_forecast = sum(forecast_values)

        # Calculate growth rate compared to historical data
        historical_total = (
            sum(values[-timeframe_days:])
            if len(values) >= timeframe_days
            else sum(values)
        )
        if historical_total > 0:
            growth_rate = (total_forecast - historical_total) / historical_total
        else:
            growth_rate = 0.0

        # Create forecast object
        forecast = DemandForecast(
            product_id=product_id,
            category_id=category_id,
            timeframe_days=timeframe_days,
            forecast_values=forecast_values,
            forecast_dates=forecast_dates,
            confidence_intervals=confidence_intervals,
            seasonality_factors=seasonality_factors,
            total_forecast=total_forecast,
            growth_rate=growth_rate,
            forecast_accuracy=self._estimate_forecast_accuracy(values),
            factors=external_factors or {},
            last_updated=datetime.now(),
        )

        # Cache forecast
        self.forecast_cache[cache_key] = forecast

        return forecast

    async def _get_historical_data(
        self, product_id: Optional[str], category_id: Optional[str]
    ) -> List[Tuple[datetime, float]]:
        """
        Get historical sales data for a product or category.

        Args:
            product_id: Optional ID of the product
            category_id: Optional ID of the category

        Returns:
            List of (date, quantity) tuples
        """
        # In a real implementation, this would fetch data from a database
        # For this example, we'll generate mock data

        # Generate 90 days of mock data
        mock_data = []
        base_demand = 100 if product_id else 1000  # Higher for categories

        for day in range(90, 0, -1):
            date = datetime.now() - timedelta(days=day)

            # Add trend (slight increase over time)
            trend_factor = 1.0 + (90 - day) * 0.002

            # Add weekly seasonality (weekends higher)
            weekday = date.weekday()
            weekly_factor = 1.2 if weekday >= 5 else 1.0  # Weekend boost

            # Add monthly seasonality (higher at start/end of month)
            day_of_month = date.day
            monthly_factor = 1.1 if day_of_month <= 5 or day_of_month >= 25 else 1.0

            # Add some randomness
            random_factor = (
                0.8 + (hash(f"{product_id or category_id}_{date}") % 40) / 100
            )

            # Calculate demand
            demand = (
                base_demand
                * trend_factor
                * weekly_factor
                * monthly_factor
                * random_factor
            )

            mock_data.append((date, round(demand, 2)))

        return mock_data

    def _detect_seasonality(
        self, values: List[float], dates: List[datetime]
    ) -> Dict[str, float]:
        """
        Detect seasonality patterns in historical data.

        Args:
            values: Historical demand values
            dates: Corresponding dates

        Returns:
            Dictionary mapping seasonality types to factors
        """
        seasonality_factors = {}

        # Check if we have enough data
        if len(values) < 14:  # Need at least 2 weeks
            return seasonality_factors

        # Detect day-of-week seasonality
        dow_factors = self._calculate_day_of_week_factors(values, dates)
        if any(abs(f - 1.0) > 0.05 for f in dow_factors.values()):
            seasonality_factors.update(dow_factors)

        # Detect day-of-month seasonality if we have enough data
        if len(values) >= 60:  # Need at least 2 months
            dom_factors = self._calculate_day_of_month_factors(values, dates)
            if any(abs(f - 1.0) > 0.05 for f in dom_factors.values()):
                seasonality_factors.update(dom_factors)

        # Detect month-of-year seasonality if we have enough data
        if len(values) >= 365:  # Need at least 1 year
            moy_factors = self._calculate_month_of_year_factors(values, dates)
            if any(abs(f - 1.0) > 0.05 for f in moy_factors.values()):
                seasonality_factors.update(moy_factors)

        return seasonality_factors

    def _calculate_day_of_week_factors(
        self, values: List[float], dates: List[datetime]
    ) -> Dict[str, float]:
        """
        Calculate day-of-week seasonality factors.

        Args:
            values: Historical demand values
            dates: Corresponding dates

        Returns:
            Dictionary mapping day names to seasonality factors
        """
        # Group values by day of week
        dow_values = {i: [] for i in range(7)}

        for date, value in zip(dates, values):
            dow_values[date.weekday()].append(value)

        # Calculate average for each day
        dow_avgs = {
            day: sum(vals) / len(vals) if vals else 0
            for day, vals in dow_values.items()
        }

        # Calculate overall average
        overall_avg = sum(values) / len(values) if values else 0

        # Calculate factors
        if overall_avg > 0:
            dow_factors = {
                f"dow_{day}": avg / overall_avg
                for day, avg in dow_avgs.items()
                if avg > 0
            }
        else:
            dow_factors = {f"dow_{day}": 1.0 for day in range(7)}

        return dow_factors

    def _calculate_day_of_month_factors(
        self, values: List[float], dates: List[datetime]
    ) -> Dict[str, float]:
        """
        Calculate day-of-month seasonality factors.

        Args:
            values: Historical demand values
            dates: Corresponding dates

        Returns:
            Dictionary mapping day groups to seasonality factors
        """
        # Group by day of month ranges
        dom_groups = {
            "dom_1_5": [],  # 1st-5th
            "dom_6_10": [],  # 6th-10th
            "dom_11_15": [],  # 11th-15th
            "dom_16_20": [],  # 16th-20th
            "dom_21_25": [],  # 21st-25th
            "dom_26_31": [],  # 26th-31st
        }

        for date, value in zip(dates, values):
            day = date.day
            if day <= 5:
                dom_groups["dom_1_5"].append(value)
            elif day <= 10:
                dom_groups["dom_6_10"].append(value)
            elif day <= 15:
                dom_groups["dom_11_15"].append(value)
            elif day <= 20:
                dom_groups["dom_16_20"].append(value)
            elif day <= 25:
                dom_groups["dom_21_25"].append(value)
            else:
                dom_groups["dom_26_31"].append(value)

        # Calculate average for each group
        dom_avgs = {
            group: sum(vals) / len(vals) if vals else 0
            for group, vals in dom_groups.items()
        }

        # Calculate overall average
        overall_avg = sum(values) / len(values) if values else 0

        # Calculate factors
        if overall_avg > 0:
            dom_factors = {
                group: avg / overall_avg for group, avg in dom_avgs.items() if avg > 0
            }
        else:
            dom_factors = {group: 1.0 for group in dom_groups.keys()}

        return dom_factors

    def _calculate_month_of_year_factors(
        self, values: List[float], dates: List[datetime]
    ) -> Dict[str, float]:
        """
        Calculate month-of-year seasonality factors.

        Args:
            values: Historical demand values
            dates: Corresponding dates

        Returns:
            Dictionary mapping month names to seasonality factors
        """
        # Group by month
        moy_values = {i: [] for i in range(1, 13)}

        for date, value in zip(dates, values):
            moy_values[date.month].append(value)

        # Calculate average for each month
        moy_avgs = {
            month: sum(vals) / len(vals) if vals else 0
            for month, vals in moy_values.items()
        }

        # Calculate overall average
        overall_avg = sum(values) / len(values) if values else 0

        # Calculate factors
        if overall_avg > 0:
            moy_factors = {
                f"moy_{month}": avg / overall_avg
                for month, avg in moy_avgs.items()
                if avg > 0
            }
        else:
            moy_factors = {f"moy_{month}": 1.0 for month in range(1, 13)}

        return moy_factors

    def _generate_forecast(
        self,
        dates: List[datetime],
        values: List[float],
        timeframe_days: int,
        seasonality_factors: Dict[str, float],
        external_factors: Optional[Dict[str, float]] = None,
    ) -> Tuple[List[datetime], List[float], List[Dict[str, float]]]:
        """
        Generate demand forecast.

        Args:
            dates: Historical dates
            values: Historical values
            timeframe_days: Number of days to forecast
            seasonality_factors: Seasonality factors
            external_factors: External factors affecting demand

        Returns:
            Tuple of (forecast_dates, forecast_values, confidence_intervals)
        """
        # Calculate trend using simple linear regression
        n = len(values)
        x = list(range(n))

        # Calculate slope and intercept manually
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] * x[i] for i in range(n))

        if n * sum_x2 - sum_x * sum_x != 0:
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n
        else:
            slope = 0
            intercept = sum_y / n if n > 0 else 0

        # Calculate standard error for confidence intervals
        if n > 2:
            y_pred = [intercept + slope * x[i] for i in range(n)]
            residuals = [values[i] - y_pred[i] for i in range(n)]
            mse = sum(r * r for r in residuals) / (n - 2)
            std_err = math.sqrt(mse)
        else:
            std_err = 0

        # Generate forecast dates
        last_date = dates[-1]
        forecast_dates = [
            last_date + timedelta(days=i + 1) for i in range(timeframe_days)
        ]

        # Generate base forecast values using trend
        forecast_values = []
        confidence_intervals = []

        for i in range(timeframe_days):
            # Base forecast using trend
            base_forecast = intercept + slope * (len(values) + i)

            # Apply seasonality
            seasonality_multiplier = self._calculate_seasonality_multiplier(
                forecast_dates[i], seasonality_factors
            )

            # Apply external factors
            external_multiplier = self._calculate_external_multiplier(
                external_factors, forecast_dates[i]
            )

            # Calculate final forecast
            forecast = max(
                0, base_forecast * seasonality_multiplier * external_multiplier
            )
            forecast_values.append(round(forecast, 2))

            # Calculate confidence interval
            # Wider intervals for further forecasts
            interval_width = std_err * (1 + i * 0.05)
            confidence_intervals.append(
                {
                    "lower_80": max(0, forecast - interval_width),
                    "upper_80": forecast + interval_width,
                    "lower_95": max(0, forecast - interval_width * 1.96),
                    "upper_95": forecast + interval_width * 1.96,
                }
            )

        return forecast_dates, forecast_values, confidence_intervals

    def _calculate_seasonality_multiplier(
        self, date: datetime, seasonality_factors: Dict[str, float]
    ) -> float:
        """
        Calculate combined seasonality multiplier for a date.

        Args:
            date: Date to calculate for
            seasonality_factors: Dictionary of seasonality factors

        Returns:
            Combined seasonality multiplier
        """
        multiplier = 1.0

        # Apply day of week factor
        dow_key = f"dow_{date.weekday()}"
        if dow_key in seasonality_factors:
            multiplier *= seasonality_factors[dow_key]

        # Apply day of month factor
        day = date.day
        if day <= 5 and "dom_1_5" in seasonality_factors:
            multiplier *= seasonality_factors["dom_1_5"]
        elif day <= 10 and "dom_6_10" in seasonality_factors:
            multiplier *= seasonality_factors["dom_6_10"]
        elif day <= 15 and "dom_11_15" in seasonality_factors:
            multiplier *= seasonality_factors["dom_11_15"]
        elif day <= 20 and "dom_16_20" in seasonality_factors:
            multiplier *= seasonality_factors["dom_16_20"]
        elif day <= 25 and "dom_21_25" in seasonality_factors:
            multiplier *= seasonality_factors["dom_21_25"]
        elif "dom_26_31" in seasonality_factors:
            multiplier *= seasonality_factors["dom_26_31"]

        # Apply month of year factor
        moy_key = f"moy_{date.month}"
        if moy_key in seasonality_factors:
            multiplier *= seasonality_factors[moy_key]

        return multiplier

    def _calculate_external_multiplier(
        self, external_factors: Optional[Dict[str, float]], date: datetime
    ) -> float:
        """
        Calculate multiplier based on external factors.

        Args:
            external_factors: Dictionary of external factors
            date: Date to calculate for

        Returns:
            External factor multiplier
        """
        if not external_factors:
            return 1.0

        multiplier = 1.0

        # Apply promotion factor if applicable
        if "promotion" in external_factors:
            # Check if promotion is active on this date
            promotion_start = external_factors.get("promotion_start_day", 0)
            promotion_end = external_factors.get("promotion_end_day", 0)

            days_from_now = (date - datetime.now()).days

            if promotion_start <= days_from_now <= promotion_end:
                multiplier *= 1.0 + external_factors["promotion"]

        # Apply competition factor
        if "competition_increase" in external_factors:
            multiplier *= 1.0 - external_factors["competition_increase"]

        # Apply market growth factor
        if "market_growth" in external_factors:
            # Apply proportionally to days in future
            days_from_now = (date - datetime.now()).days
            growth_factor = 1.0 + (
                external_factors["market_growth"] * days_from_now / 365
            )
            multiplier *= growth_factor

        # Apply seasonality boost for holidays
        if "holiday_boost" in external_factors:
            # Check if date is near a holiday
            is_holiday = self._is_holiday(date)
            if is_holiday:
                multiplier *= 1.0 + external_factors["holiday_boost"]

        return multiplier

    def _is_holiday(self, date: datetime) -> bool:
        """
        Check if a date is a holiday.

        Args:
            date: Date to check

        Returns:
            True if holiday, False otherwise
        """
        # Simplified holiday check
        # In a real implementation, this would use a holiday calendar

        # Check for major US holidays
        month, day = date.month, date.day

        # New Year's Day
        if month == 1 and day == 1:
            return True

        # Independence Day
        if month == 7 and day == 4:
            return True

        # Christmas
        if month == 12 and day == 25:
            return True

        # Thanksgiving (approximate)
        if month == 11 and 22 <= day <= 28 and date.weekday() == 3:  # Thursday
            return True

        # Black Friday
        if month == 11 and 23 <= day <= 29 and date.weekday() == 4:  # Friday
            return True

        # Cyber Monday
        if month == 11 and 26 <= day <= 30 and date.weekday() == 0:  # Monday
            return True

        return False

    def _estimate_forecast_accuracy(self, historical_values: List[float]) -> float:
        """
        Estimate forecast accuracy based on historical data.

        Args:
            historical_values: Historical demand values

        Returns:
            Estimated forecast accuracy (0.0 to 1.0)
        """
        if len(historical_values) < 10:
            return 0.5  # Default accuracy with limited data

        # Calculate coefficient of variation
        mean_value = sum(historical_values) / len(historical_values)
        if mean_value == 0:
            return 0.5

        variance = sum((x - mean_value) ** 2 for x in historical_values) / len(
            historical_values
        )
        std_dev = math.sqrt(variance)
        cv = std_dev / mean_value

        # Higher variability = lower accuracy
        if cv > 1.0:
            base_accuracy = 0.5
        else:
            base_accuracy = 0.9 - (cv * 0.4)

        # More data = higher accuracy
        data_factor = min(len(historical_values) / 100, 1.0) * 0.1

        # Calculate final accuracy
        accuracy = base_accuracy + data_factor

        # Ensure within bounds
        return max(0.0, min(accuracy, 1.0))

    def _create_empty_forecast(
        self, product_id: Optional[str], category_id: Optional[str], timeframe_days: int
    ) -> DemandForecast:
        """
        Create an empty forecast when insufficient data is available.

        Args:
            product_id: Optional product ID
            category_id: Optional category ID
            timeframe_days: Forecast timeframe in days

        Returns:
            Empty DemandForecast object
        """
        # Generate forecast dates
        forecast_dates = [
            datetime.now() + timedelta(days=i + 1) for i in range(timeframe_days)
        ]

        # Create empty forecast values
        forecast_values = [0.0] * timeframe_days

        return DemandForecast(
            product_id=product_id,
            category_id=category_id,
            timeframe_days=timeframe_days,
            forecast_values=forecast_values,
            forecast_dates=forecast_dates,
            confidence_intervals=None,
            seasonality_factors={},
            total_forecast=0.0,
            growth_rate=0.0,
            forecast_accuracy=0.0,
            factors={},
            last_updated=datetime.now(),
        )
