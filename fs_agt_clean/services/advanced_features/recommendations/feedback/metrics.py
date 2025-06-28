#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Recommendation Quality Metrics

This module implements metrics for evaluating recommendation quality based on
feedback data. It includes metrics for relevance, diversity, novelty, serendipity,
coverage, and business impact.

It includes:
1. Core metrics calculation for recommendation evaluation
2. Periodic reporting of recommendation quality
3. Historical tracking and trend analysis
4. Multi-dimensional evaluation metrics
5. Business impact metric correlation
"""

import json
import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from scipy import stats

from fs_agt_clean.core.types import JsonDict

logger = logging.getLogger(__name__)


class MetricCategory(str, Enum):
    """Categories of recommendation quality metrics."""

    RELEVANCE = "relevance"  # How relevant recommendations are to users
    DIVERSITY = "diversity"  # How diverse the recommendations are
    NOVELTY = "novelty"  # How novel/surprising recommendations are
    COVERAGE = "coverage"  # Coverage of the item catalog
    SERENDIPITY = "serendipity"  # Unexpected but relevant recommendations
    BUSINESS = "business"  # Business impact (revenue, conversions)
    ENGAGEMENT = "engagement"  # UnifiedUser engagement with recommendations
    TECHNICAL = "technical"  # Technical performance (latency, etc.)


class MetricAggregation(str, Enum):
    """Types of metric aggregation."""

    MEAN = "mean"  # Arithmetic mean
    MEDIAN = "median"  # Median value
    MIN = "min"  # Minimum value
    MAX = "max"  # Maximum value
    SUM = "sum"  # Sum of values
    STD_DEV = "std_dev"  # Standard deviation
    PERCENTILE_95 = "percentile_95"  # 95th percentile
    COUNT = "count"  # Count of occurrences


class MetricTrend(str, Enum):
    """Trend directions for metrics."""

    IMPROVING = "improving"  # Metric is improving
    STABLE = "stable"  # Metric is stable
    DEGRADING = "degrading"  # Metric is degrading
    UNKNOWN = "unknown"  # Trend cannot be determined


@dataclass
class RecommendationMetric:
    """Base class for recommendation quality metrics."""

    name: str
    category: MetricCategory
    value: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    confidence: float = 1.0
    sample_size: int = 0
    source: str = "feedback"
    algorithm_id: Optional[str] = None
    segment_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "category": self.category.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence,
            "sample_size": self.sample_size,
            "source": self.source,
            "algorithm_id": self.algorithm_id,
            "segment_id": self.segment_id,
            "metadata": self.metadata,
        }


@dataclass
class MetricSnapshot:
    """A snapshot of metrics at a point in time."""

    timestamp: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, RecommendationMetric] = field(default_factory=dict)
    algorithm_id: Optional[str] = None
    segment_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "metrics": {
                name: metric.to_dict() for name, metric in self.metrics.items()
            },
            "algorithm_id": self.algorithm_id,
            "segment_id": self.segment_id,
        }

    def add_metric(self, metric: RecommendationMetric) -> None:
        """Add a metric to the snapshot."""
        self.metrics[metric.name] = metric

    def get_metric(self, name: str) -> Optional[RecommendationMetric]:
        """Get a metric by name."""
        return self.metrics.get(name)


@dataclass
class MetricTimeSeries:
    """A time series of metric values."""

    name: str
    category: MetricCategory
    values: List[float] = field(default_factory=list)
    timestamps: List[datetime] = field(default_factory=list)
    sample_sizes: List[int] = field(default_factory=list)
    confidences: List[float] = field(default_factory=list)

    def add_point(
        self,
        value: float,
        timestamp: datetime = None,
        sample_size: int = 0,
        confidence: float = 1.0,
    ) -> None:
        """Add a data point to the time series."""
        self.values.append(value)
        self.timestamps.append(timestamp or datetime.now())
        self.sample_sizes.append(sample_size)
        self.confidences.append(confidence)

    def get_trend(self, window: int = 5) -> MetricTrend:
        """Calculate the trend over the last N data points."""
        if len(self.values) < window:
            return MetricTrend.UNKNOWN

        recent_values = self.values[-window:]

        # Simple linear regression to determine trend
        x = list(range(len(recent_values)))
        slope, _, r_value, p_value, _ = stats.linregress(x, recent_values)

        # Check if trend is statistically significant
        if p_value > 0.05 or abs(r_value) < 0.5:
            return MetricTrend.STABLE

        if slope > 0:
            return MetricTrend.IMPROVING
        else:
            return MetricTrend.DEGRADING

    def get_latest(self) -> Tuple[float, datetime]:
        """Get the latest value and timestamp."""
        if not self.values:
            return 0.0, datetime.now()
        return self.values[-1], self.timestamps[-1]

    def get_aggregated(self, aggregation: MetricAggregation) -> float:
        """Get an aggregated value using the specified method."""
        if not self.values:
            return 0.0

        if aggregation == MetricAggregation.MEAN:
            return sum(self.values) / len(self.values)
        elif aggregation == MetricAggregation.MEDIAN:
            return sorted(self.values)[len(self.values) // 2]
        elif aggregation == MetricAggregation.MIN:
            return min(self.values)
        elif aggregation == MetricAggregation.MAX:
            return max(self.values)
        elif aggregation == MetricAggregation.SUM:
            return sum(self.values)
        elif aggregation == MetricAggregation.STD_DEV:
            mean = sum(self.values) / len(self.values)
            return math.sqrt(
                sum((x - mean) ** 2 for x in self.values) / len(self.values)
            )
        elif aggregation == MetricAggregation.PERCENTILE_95:
            return sorted(self.values)[int(len(self.values) * 0.95)]
        elif aggregation == MetricAggregation.COUNT:
            return len(self.values)

        return 0.0


class QualityMetricsService:
    """Service for tracking and analyzing recommendation quality metrics."""

    def __init__(
        self, storage_service=None, analytics_service=None, window_size: int = 30
    ):  # days
        self.storage_service = storage_service
        self.analytics_service = analytics_service
        self.window_size = window_size

        # In-memory cache
        self.metrics_history = defaultdict(
            list
        )  # metric_name -> List[RecommendationMetric]
        self._snapshots = []  # List[MetricSnapshot]
        self._time_series = {}  # metric_name -> MetricTimeSeries
        self._algorithm_metrics = defaultdict(
            dict
        )  # algorithm_id -> metric_name -> value
        self._segment_metrics = defaultdict(dict)  # segment_id -> metric_name -> value

    def add_metric(self, metric: RecommendationMetric) -> None:
        """Add a new metric reading."""
        # Store in history
        self.metrics_history[metric.name].append(metric)

        # Track in algorithm metrics if applicable
        if metric.algorithm_id:
            self._algorithm_metrics[metric.algorithm_id][metric.name] = metric.value

        # Track in segment metrics if applicable
        if metric.segment_id:
            self._segment_metrics[metric.segment_id][metric.name] = metric.value

        # Add to time series
        if metric.name not in self._time_series:
            self._time_series[metric.name] = MetricTimeSeries(
                name=metric.name, category=metric.category
            )

        self._time_series[metric.name].add_point(
            value=metric.value,
            timestamp=metric.timestamp,
            sample_size=metric.sample_size,
            confidence=metric.confidence,
        )

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.store_metric(metric)

        # Track in analytics if available
        if self.analytics_service:
            self.analytics_service.track_event(
                event_type="recommendation_metric", properties=metric.to_dict()
            )

    def create_snapshot(
        self, algorithm_id: Optional[str] = None, segment_id: Optional[str] = None
    ) -> MetricSnapshot:
        """Create a snapshot of current metrics."""
        snapshot = MetricSnapshot(algorithm_id=algorithm_id, segment_id=segment_id)

        # Add latest metrics to snapshot
        for name, time_series in self._time_series.items():
            if not time_series.values:
                continue

            latest_value, latest_timestamp = time_series.get_latest()

            # Get latest confidence and sample size
            confidence = time_series.confidences[-1] if time_series.confidences else 1.0
            sample_size = (
                time_series.sample_sizes[-1] if time_series.sample_sizes else 0
            )

            # Filter by algorithm if specified
            if algorithm_id and name in self.metrics_history:
                # Get most recent metric for this algorithm
                algorithm_metrics = [
                    m
                    for m in self.metrics_history[name]
                    if m.algorithm_id == algorithm_id
                ]
                if algorithm_metrics:
                    latest_metric = max(algorithm_metrics, key=lambda m: m.timestamp)
                    latest_value = latest_metric.value
                    latest_timestamp = latest_metric.timestamp
                    confidence = latest_metric.confidence
                    sample_size = latest_metric.sample_size

            # Filter by segment if specified
            if segment_id and name in self.metrics_history:
                # Get most recent metric for this segment
                segment_metrics = [
                    m for m in self.metrics_history[name] if m.segment_id == segment_id
                ]
                if segment_metrics:
                    latest_metric = max(segment_metrics, key=lambda m: m.timestamp)
                    latest_value = latest_metric.value
                    latest_timestamp = latest_metric.timestamp
                    confidence = latest_metric.confidence
                    sample_size = latest_metric.sample_size

            # Create metric with latest values
            original_metrics = self.metrics_history.get(name, [])
            if original_metrics:
                category = original_metrics[0].category
            else:
                # If no history, try to get category from time series
                category = time_series.category

            metric = RecommendationMetric(
                name=name,
                category=category,
                value=latest_value,
                timestamp=latest_timestamp,
                confidence=confidence,
                sample_size=sample_size,
                algorithm_id=algorithm_id,
                segment_id=segment_id,
            )

            snapshot.add_metric(metric)

        # Store snapshot
        self._snapshots.append(snapshot)

        # Persist if storage service available
        if self.storage_service:
            self.storage_service.store_snapshot(snapshot)

        return snapshot

    def get_metric_history(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        algorithm_id: Optional[str] = None,
        segment_id: Optional[str] = None,
    ) -> List[RecommendationMetric]:
        """Get historical values for a metric."""
        if metric_name not in self.metrics_history:
            return []

        metrics = self.metrics_history[metric_name]

        # Apply filters
        if start_time:
            metrics = [m for m in metrics if m.timestamp >= start_time]
        if end_time:
            metrics = [m for m in metrics if m.timestamp <= end_time]
        if algorithm_id:
            metrics = [m for m in metrics if m.algorithm_id == algorithm_id]
        if segment_id:
            metrics = [m for m in metrics if m.segment_id == segment_id]

        # Sort by timestamp
        metrics.sort(key=lambda m: m.timestamp)

        return metrics

    def get_metric_trend(
        self, metric_name: str, window: int = 5, algorithm_id: Optional[str] = None
    ) -> MetricTrend:
        """Get the trend for a metric."""
        if metric_name not in self._time_series:
            return MetricTrend.UNKNOWN

        # If looking for algorithm-specific trend
        if algorithm_id:
            metrics = self.get_metric_history(
                metric_name=metric_name, algorithm_id=algorithm_id
            )

            if len(metrics) < window:
                return MetricTrend.UNKNOWN

            values = [m.value for m in metrics[-window:]]

            # Simple linear regression to determine trend
            x = list(range(len(values)))
            slope, _, r_value, p_value, _ = stats.linregress(x, values)

            # Check if trend is statistically significant
            if p_value > 0.05 or abs(r_value) < 0.5:
                return MetricTrend.STABLE

            if slope > 0:
                return MetricTrend.IMPROVING
            else:
                return MetricTrend.DEGRADING

        # Use time series trend analysis
        return self._time_series[metric_name].get_trend(window=window)

    def get_algorithm_performance(self, algorithm_id: str) -> Dict[str, float]:
        """Get the latest performance metrics for an algorithm."""
        return dict(self._algorithm_metrics.get(algorithm_id, {}))

    def get_segment_performance(self, segment_id: str) -> Dict[str, float]:
        """Get the latest performance metrics for a user segment."""
        return dict(self._segment_metrics.get(segment_id, {}))

    def compare_algorithms(
        self, algorithm_ids: List[str], metrics: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """Compare multiple algorithms based on specified metrics."""
        results = {}

        for algorithm_id in algorithm_ids:
            algorithm_results = {}

            for metric_name in metrics:
                # Get latest value for this metric and algorithm
                if (
                    algorithm_id in self._algorithm_metrics
                    and metric_name in self._algorithm_metrics[algorithm_id]
                ):
                    algorithm_results[metric_name] = self._algorithm_metrics[
                        algorithm_id
                    ][metric_name]
                else:
                    algorithm_results[metric_name] = 0.0

            results[algorithm_id] = algorithm_results

        return results

    def get_overall_score(self, algorithm_id: Optional[str] = None) -> float:
        """Calculate an overall quality score across all metrics."""
        # Define weights for different metric categories
        category_weights = {
            MetricCategory.RELEVANCE: 0.4,
            MetricCategory.DIVERSITY: 0.1,
            MetricCategory.NOVELTY: 0.1,
            MetricCategory.COVERAGE: 0.05,
            MetricCategory.SERENDIPITY: 0.05,
            MetricCategory.BUSINESS: 0.2,
            MetricCategory.ENGAGEMENT: 0.1,
            MetricCategory.TECHNICAL: 0.0,  # Not included in overall score
        }

        # Get metrics to include in score
        metrics_by_category = defaultdict(list)

        for name, time_series in self._time_series.items():
            # Skip if no values
            if not time_series.values:
                continue

            # If algorithm_id specified, only include metrics for that algorithm
            if algorithm_id:
                metrics = self.get_metric_history(name, algorithm_id=algorithm_id)
                if not metrics:
                    continue
                latest_metric = max(metrics, key=lambda m: m.timestamp)
                metrics_by_category[latest_metric.category].append(latest_metric.value)
            else:
                # Get latest value from time series
                latest_value, _ = time_series.get_latest()
                metrics_by_category[time_series.category].append(latest_value)

        # Calculate weighted average across categories
        total_score = 0.0
        total_weight = 0.0

        for category, values in metrics_by_category.items():
            if not values:
                continue

            # Average within category
            category_avg = sum(values) / len(values)

            # Apply category weight
            weight = category_weights.get(category, 0.0)
            total_score += category_avg * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_score / total_weight


# Metric calculation functions


def calculate_relevance_metrics(
    feedback_events: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    algorithm_id: Optional[str] = None,
) -> List[RecommendationMetric]:
    """Calculate relevance metrics from feedback data."""
    metrics = []

    if not feedback_events or not recommendations:
        return metrics

    # Sample size
    sample_size = len(recommendations)

    # Calculate precision (clicked / recommended)
    clicked_recs = set()
    for event in feedback_events:
        if event.get("type") == "click" and "recommendation_id" in event:
            clicked_recs.add(event["recommendation_id"])

    precision = len(clicked_recs) / sample_size if sample_size > 0 else 0

    # Add precision metric
    metrics.append(
        RecommendationMetric(
            name="precision",
            category=MetricCategory.RELEVANCE,
            value=precision,
            sample_size=sample_size,
            algorithm_id=algorithm_id,
            confidence=min(1.0, sample_size / 100),
        )
    )

    # Calculate normalized discounted cumulative gain (nDCG)
    if sample_size > 0:
        # Create mapping from recommendation ID to position
        rec_positions = {rec["id"]: i for i, rec in enumerate(recommendations)}

        # Calculate relevance scores (using explicit ratings when available)
        relevance_scores = {}
        for event in feedback_events:
            rec_id = event.get("recommendation_id")
            if not rec_id:
                continue

            # Use rating if available, otherwise use binary signals
            if event.get("type") == "rating":
                relevance_scores[rec_id] = (
                    event.get("value", 0) / 5.0
                )  # Normalize to 0-1
            elif event.get("type") == "click":
                relevance_scores[rec_id] = 1.0
            elif event.get("type") == "purchase":
                relevance_scores[rec_id] = 1.0

        # Calculate DCG
        dcg = 0.0
        for rec_id, position in rec_positions.items():
            if rec_id in relevance_scores:
                # DCG formula: relevance / log2(position + 2)
                dcg += relevance_scores[rec_id] / math.log2(position + 2)

        # Calculate ideal DCG (items sorted by relevance)
        ideal_relevance = sorted(relevance_scores.values(), reverse=True)
        idcg = 0.0
        for i, rel in enumerate(ideal_relevance):
            idcg += rel / math.log2(i + 2)

        # Calculate nDCG
        ndcg = dcg / idcg if idcg > 0 else 0.0

        # Add nDCG metric
        metrics.append(
            RecommendationMetric(
                name="ndcg",
                category=MetricCategory.RELEVANCE,
                value=ndcg,
                sample_size=sample_size,
                algorithm_id=algorithm_id,
                confidence=min(1.0, sample_size / 100),
            )
        )

    # Calculate mean reciprocal rank (MRR)
    if sample_size > 0:
        # Create mapping from recommendation ID to position
        rec_positions = {rec["id"]: i + 1 for i, rec in enumerate(recommendations)}

        # Find position of first relevant item for each user session
        first_relevant_ranks = []
        sessions = defaultdict(list)

        # Group events by session
        for event in feedback_events:
            session_id = event.get("session_id")
            if session_id and event.get("type") in ["click", "purchase"]:
                rec_id = event.get("recommendation_id")
                if rec_id in rec_positions:
                    sessions[session_id].append((rec_id, rec_positions[rec_id]))

        # For each session, find first relevant item
        for session_events in sessions.values():
            if session_events:
                # Sort by position
                session_events.sort(key=lambda x: x[1])
                # Add reciprocal rank of first item
                first_relevant_ranks.append(1.0 / session_events[0][1])

        # Calculate MRR
        mrr = (
            sum(first_relevant_ranks) / len(first_relevant_ranks)
            if first_relevant_ranks
            else 0.0
        )

        # Add MRR metric
        metrics.append(
            RecommendationMetric(
                name="mrr",
                category=MetricCategory.RELEVANCE,
                value=mrr,
                sample_size=len(first_relevant_ranks),
                algorithm_id=algorithm_id,
                confidence=min(1.0, len(first_relevant_ranks) / 50),
            )
        )

    return metrics


def calculate_diversity_metrics(
    recommendations: List[Dict[str, Any]], algorithm_id: Optional[str] = None
) -> List[RecommendationMetric]:
    """Calculate diversity metrics for recommendations."""
    metrics = []

    if not recommendations:
        return metrics

    # Sample size
    sample_size = len(recommendations)

    # Extract categories and attributes
    categories = []
    attributes = defaultdict(list)

    for rec in recommendations:
        if "category" in rec:
            categories.append(rec["category"])

        # Extract other attributes
        for attr in ["brand", "price_tier", "style", "target_audience"]:
            if attr in rec:
                attributes[attr].append(rec[attr])

    # Calculate category diversity (unique categories / total)
    if categories:
        category_diversity = len(set(categories)) / len(categories)

        metrics.append(
            RecommendationMetric(
                name="category_diversity",
                category=MetricCategory.DIVERSITY,
                value=category_diversity,
                sample_size=sample_size,
                algorithm_id=algorithm_id,
            )
        )

    # Calculate attribute diversity for each attribute
    for attr_name, attr_values in attributes.items():
        if attr_values:
            attr_diversity = len(set(attr_values)) / len(attr_values)

            metrics.append(
                RecommendationMetric(
                    name=f"{attr_name}_diversity",
                    category=MetricCategory.DIVERSITY,
                    value=attr_diversity,
                    sample_size=sample_size,
                    algorithm_id=algorithm_id,
                )
            )

    # Calculate intra-list similarity if item vectors available
    # This would require item vector embeddings, not included in this implementation

    return metrics


def calculate_novelty_metrics(
    recommendations: List[Dict[str, Any]],
    user_history: List[Dict[str, Any]],
    global_popularity: Dict[str, float],
    algorithm_id: Optional[str] = None,
) -> List[RecommendationMetric]:
    """Calculate novelty metrics for recommendations."""
    metrics = []

    if not recommendations:
        return metrics

    # Sample size
    sample_size = len(recommendations)

    # Calculate popularity-based novelty
    if global_popularity:
        # Extract item IDs from recommendations
        rec_ids = [rec["id"] for rec in recommendations]

        # Calculate inverse popularity scores (higher = more novel)
        novelty_scores = []
        for item_id in rec_ids:
            popularity = global_popularity.get(item_id, 0.0)
            # Avoid division by zero
            inverse_popularity = 1.0 / (popularity + 0.01)
            novelty_scores.append(inverse_popularity)

        # Normalize scores to 0-1 range
        if novelty_scores:
            max_score = max(novelty_scores)
            if max_score > 0:
                novelty_scores = [score / max_score for score in novelty_scores]

            # Calculate mean novelty
            mean_novelty = sum(novelty_scores) / len(novelty_scores)

            metrics.append(
                RecommendationMetric(
                    name="popularity_novelty",
                    category=MetricCategory.NOVELTY,
                    value=mean_novelty,
                    sample_size=sample_size,
                    algorithm_id=algorithm_id,
                )
            )

    # Calculate user history novelty (not seen before by user)
    if user_history:
        # Extract item IDs from user history
        history_ids = set(item["id"] for item in user_history)

        # Count items not in user history
        new_items = [rec for rec in recommendations if rec["id"] not in history_ids]
        history_novelty = len(new_items) / sample_size

        metrics.append(
            RecommendationMetric(
                name="history_novelty",
                category=MetricCategory.NOVELTY,
                value=history_novelty,
                sample_size=sample_size,
                algorithm_id=algorithm_id,
            )
        )

    return metrics


def calculate_business_metrics(
    feedback_events: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    algorithm_id: Optional[str] = None,
) -> List[RecommendationMetric]:
    """Calculate business impact metrics from feedback data."""
    metrics = []

    if not feedback_events or not recommendations:
        return metrics

    # Sample size
    sample_size = len(recommendations)

    # Calculate CTR
    clicks = sum(1 for event in feedback_events if event.get("type") == "click")
    ctr = clicks / sample_size if sample_size > 0 else 0.0

    metrics.append(
        RecommendationMetric(
            name="ctr",
            category=MetricCategory.BUSINESS,
            value=ctr,
            sample_size=sample_size,
            algorithm_id=algorithm_id,
        )
    )

    # Calculate conversion rate
    conversions = sum(1 for event in feedback_events if event.get("type") == "purchase")
    conversion_rate = conversions / sample_size if sample_size > 0 else 0.0

    metrics.append(
        RecommendationMetric(
            name="conversion_rate",
            category=MetricCategory.BUSINESS,
            value=conversion_rate,
            sample_size=sample_size,
            algorithm_id=algorithm_id,
        )
    )

    # Calculate revenue per recommendation
    total_revenue = sum(
        event.get("metadata", {}).get("revenue", 0)
        for event in feedback_events
        if event.get("type") == "purchase"
    )
    revenue_per_rec = total_revenue / sample_size if sample_size > 0 else 0.0

    metrics.append(
        RecommendationMetric(
            name="revenue_per_recommendation",
            category=MetricCategory.BUSINESS,
            value=revenue_per_rec,
            sample_size=sample_size,
            algorithm_id=algorithm_id,
        )
    )

    return metrics


def calculate_all_metrics(
    feedback_events: List[Dict[str, Any]],
    recommendations: List[Dict[str, Any]],
    user_history: Optional[List[Dict[str, Any]]] = None,
    global_popularity: Optional[Dict[str, float]] = None,
    algorithm_id: Optional[str] = None,
    metrics_service: Optional[QualityMetricsService] = None,
) -> List[RecommendationMetric]:
    """Calculate all recommendation quality metrics."""
    all_metrics = []

    # Calculate relevance metrics
    relevance_metrics = calculate_relevance_metrics(
        feedback_events=feedback_events,
        recommendations=recommendations,
        algorithm_id=algorithm_id,
    )
    all_metrics.extend(relevance_metrics)

    # Calculate diversity metrics
    diversity_metrics = calculate_diversity_metrics(
        recommendations=recommendations, algorithm_id=algorithm_id
    )
    all_metrics.extend(diversity_metrics)

    # Calculate novelty metrics if user history available
    if user_history or global_popularity:
        novelty_metrics = calculate_novelty_metrics(
            recommendations=recommendations,
            user_history=user_history or [],
            global_popularity=global_popularity or {},
            algorithm_id=algorithm_id,
        )
        all_metrics.extend(novelty_metrics)

    # Calculate business metrics
    business_metrics = calculate_business_metrics(
        feedback_events=feedback_events,
        recommendations=recommendations,
        algorithm_id=algorithm_id,
    )
    all_metrics.extend(business_metrics)

    # Record metrics in service if provided
    if metrics_service:
        for metric in all_metrics:
            metrics_service.add_metric(metric)

    return all_metrics
