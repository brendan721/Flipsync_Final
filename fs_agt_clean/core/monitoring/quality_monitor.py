#!/usr/bin/env python3
"""
Quality Monitoring System for FlipSync AI Operations
====================================================

This module provides comprehensive quality monitoring and validation
for FlipSync's AI-powered operations across the 35+ agent architecture.

Features:
- Real-time quality scoring and validation
- Performance metrics tracking
- Quality threshold enforcement
- Integration with intelligent model router
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """Quality metrics for monitoring."""
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    RESPONSE_TIME = "response_time"


@dataclass
class QualityEntry:
    """Individual quality entry for tracking."""
    timestamp: datetime
    operation_type: str
    model: str
    agent_id: str
    quality_score: float
    metrics: Dict[QualityMetric, float]
    expected_quality: float
    actual_quality: float
    response_time: float


class QualityMonitor:
    """
    Comprehensive quality monitoring system for FlipSync AI operations.
    
    Monitors quality across all AI operations and provides quality assurance
    with real-time scoring and threshold enforcement.
    """

    def __init__(self, quality_threshold: float = 0.8):
        """Initialize quality monitor with threshold."""
        self.quality_threshold = quality_threshold
        
        # Quality storage
        self.quality_entries: List[QualityEntry] = []
        self.quality_scores: Dict[str, List[float]] = {}  # model -> scores
        
        # Performance tracking
        self.model_performance: Dict[str, Dict[str, Any]] = {}
        self.operation_performance: Dict[str, Dict[str, Any]] = {}
        
        # Quality trends
        self.quality_trends: Dict[str, List[Dict[str, Any]]] = {}
        
        logger.info(f"QualityMonitor initialized with threshold: {quality_threshold}")

    async def record_quality(
        self,
        operation_type: str,
        model: str,
        agent_id: str,
        quality_score: float,
        expected_quality: float,
        actual_quality: float,
        response_time: float,
        metrics: Optional[Dict[QualityMetric, float]] = None
    ):
        """Record a quality entry and update tracking."""
        
        if metrics is None:
            metrics = {}
        
        # Create quality entry
        entry = QualityEntry(
            timestamp=datetime.now(),
            operation_type=operation_type,
            model=model,
            agent_id=agent_id,
            quality_score=quality_score,
            metrics=metrics,
            expected_quality=expected_quality,
            actual_quality=actual_quality,
            response_time=response_time
        )
        
        # Store entry
        self.quality_entries.append(entry)
        
        # Update model scores
        if model not in self.quality_scores:
            self.quality_scores[model] = []
        self.quality_scores[model].append(quality_score)
        
        # Update performance tracking
        await self._update_performance_tracking(entry)
        
        # Check quality thresholds
        await self._check_quality_thresholds(entry)
        
        logger.debug(f"Quality recorded: {operation_type} {quality_score:.3f} (model: {model})")

    async def get_quality_stats(self) -> Dict[str, Any]:
        """Get comprehensive quality statistics."""
        
        return {
            "overall_quality_score": self._calculate_overall_quality(),
            "quality_threshold": self.quality_threshold,
            "total_operations": len(self.quality_entries),
            "model_performance": self.model_performance,
            "operation_performance": self.operation_performance,
            "quality_trends": self._get_quality_trends(),
            "threshold_violations": self._get_threshold_violations(),
            "quality_distribution": self._get_quality_distribution()
        }

    async def validate_quality(
        self,
        operation_type: str,
        model: str,
        quality_score: float
    ) -> bool:
        """Validate if quality meets threshold requirements."""
        
        # Check against global threshold
        if quality_score < self.quality_threshold:
            logger.warning(f"Quality below threshold: {quality_score:.3f} < {self.quality_threshold}")
            return False
        
        # Check against model-specific performance
        if model in self.model_performance:
            model_avg = self.model_performance[model]["average_quality"]
            if quality_score < model_avg * 0.8:  # 20% below model average
                logger.warning(f"Quality significantly below model average: {quality_score:.3f} < {model_avg * 0.8:.3f}")
                return False
        
        return True

    def _calculate_overall_quality(self) -> float:
        """Calculate overall quality score."""
        
        if not self.quality_entries:
            return 0.0
        
        # Weight recent entries more heavily
        now = datetime.now()
        weighted_scores = []
        
        for entry in self.quality_entries[-100:]:  # Last 100 entries
            age_hours = (now - entry.timestamp).total_seconds() / 3600
            weight = max(0.1, 1.0 - (age_hours / 24))  # Decay over 24 hours
            weighted_scores.append(entry.quality_score * weight)
        
        return sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0.0

    def _get_quality_trends(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get quality trends over time."""
        
        # Daily trends (last 7 days)
        daily_trends = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            day_entries = [
                e for e in self.quality_entries
                if e.timestamp.strftime("%Y-%m-%d") == date
            ]
            
            if day_entries:
                avg_quality = sum(e.quality_score for e in day_entries) / len(day_entries)
                daily_trends.append({
                    "date": date,
                    "average_quality": avg_quality,
                    "operation_count": len(day_entries)
                })
        
        # Model trends
        model_trends = {}
        for model in self.quality_scores:
            recent_scores = self.quality_scores[model][-20:]  # Last 20 scores
            if recent_scores:
                model_trends[model] = {
                    "average_quality": statistics.mean(recent_scores),
                    "quality_std": statistics.stdev(recent_scores) if len(recent_scores) > 1 else 0.0,
                    "trend_direction": self._calculate_trend_direction(recent_scores)
                }
        
        return {
            "daily": daily_trends,
            "models": model_trends
        }

    def _get_threshold_violations(self) -> List[Dict[str, Any]]:
        """Get recent quality threshold violations."""
        
        violations = []
        for entry in self.quality_entries[-50:]:  # Last 50 entries
            if entry.quality_score < self.quality_threshold:
                violations.append({
                    "timestamp": entry.timestamp.isoformat(),
                    "operation_type": entry.operation_type,
                    "model": entry.model,
                    "agent_id": entry.agent_id,
                    "quality_score": entry.quality_score,
                    "threshold": self.quality_threshold,
                    "deviation": self.quality_threshold - entry.quality_score
                })
        
        return violations

    def _get_quality_distribution(self) -> Dict[str, int]:
        """Get quality score distribution."""
        
        if not self.quality_entries:
            return {}
        
        distribution = {
            "excellent": 0,  # 0.9+
            "good": 0,       # 0.8-0.9
            "fair": 0,       # 0.7-0.8
            "poor": 0        # <0.7
        }
        
        for entry in self.quality_entries:
            score = entry.quality_score
            if score >= 0.9:
                distribution["excellent"] += 1
            elif score >= 0.8:
                distribution["good"] += 1
            elif score >= 0.7:
                distribution["fair"] += 1
            else:
                distribution["poor"] += 1
        
        return distribution

    async def _update_performance_tracking(self, entry: QualityEntry):
        """Update performance tracking with new quality entry."""
        
        # Update model performance
        model = entry.model
        if model not in self.model_performance:
            self.model_performance[model] = {
                "operation_count": 0,
                "total_quality": 0.0,
                "average_quality": 0.0,
                "quality_scores": [],
                "response_times": []
            }
        
        perf = self.model_performance[model]
        perf["operation_count"] += 1
        perf["total_quality"] += entry.quality_score
        perf["average_quality"] = perf["total_quality"] / perf["operation_count"]
        perf["quality_scores"].append(entry.quality_score)
        perf["response_times"].append(entry.response_time)
        
        # Keep only recent scores (last 100)
        if len(perf["quality_scores"]) > 100:
            perf["quality_scores"] = perf["quality_scores"][-100:]
            perf["response_times"] = perf["response_times"][-100:]
        
        # Update operation performance
        op_type = entry.operation_type
        if op_type not in self.operation_performance:
            self.operation_performance[op_type] = {
                "operation_count": 0,
                "total_quality": 0.0,
                "average_quality": 0.0,
                "models_used": set()
            }
        
        op_perf = self.operation_performance[op_type]
        op_perf["operation_count"] += 1
        op_perf["total_quality"] += entry.quality_score
        op_perf["average_quality"] = op_perf["total_quality"] / op_perf["operation_count"]
        op_perf["models_used"].add(model)

    async def _check_quality_thresholds(self, entry: QualityEntry):
        """Check quality thresholds and generate alerts."""
        
        if entry.quality_score < self.quality_threshold:
            logger.warning(
                f"Quality threshold violation: {entry.operation_type} "
                f"scored {entry.quality_score:.3f} (threshold: {self.quality_threshold})"
            )
        
        # Check for significant quality degradation
        if entry.model in self.model_performance:
            model_avg = self.model_performance[entry.model]["average_quality"]
            if entry.quality_score < model_avg * 0.7:  # 30% below average
                logger.error(
                    f"Significant quality degradation: {entry.model} "
                    f"scored {entry.quality_score:.3f} (avg: {model_avg:.3f})"
                )

    def _calculate_trend_direction(self, scores: List[float]) -> str:
        """Calculate trend direction for quality scores."""
        
        if len(scores) < 3:
            return "insufficient_data"
        
        # Simple linear trend calculation
        x = list(range(len(scores)))
        y = scores
        
        # Calculate slope
        n = len(scores)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"


# Global quality monitor instance
_quality_monitor_instance = None


def get_quality_monitor(quality_threshold: float = 0.8) -> QualityMonitor:
    """Get global quality monitor instance."""
    global _quality_monitor_instance
    if _quality_monitor_instance is None:
        _quality_monitor_instance = QualityMonitor(quality_threshold)
    return _quality_monitor_instance
