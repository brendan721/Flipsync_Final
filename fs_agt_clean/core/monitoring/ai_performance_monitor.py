"""
AI Performance Monitoring for FlipSync
=====================================

Monitors AI response times, model performance, and resource utilization.
Provides alerting for performance degradation and tracks metrics over time.
"""

import asyncio
import json
import logging
import time
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AIPerformanceMetrics:
    """AI performance metrics data structure."""

    timestamp: str
    model_name: str
    response_time: float
    prompt_length: int
    response_length: int
    success: bool
    error_message: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class AIPerformanceMonitor:
    """Monitor AI performance and track metrics."""

    def __init__(self, max_history: int = 1000):
        """Initialize AI performance monitor."""
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.alert_thresholds = {
            "response_time_warning": 180.0,  # seconds - 3 minutes (updated for gemma3:4b)
            "response_time_critical": 300.0,  # seconds - 5 minutes (updated for gemma3:4b)
            "error_rate_warning": 0.1,  # 10%
            "error_rate_critical": 0.25,  # 25%
            "memory_warning": 80.0,  # 80% of available memory
            "memory_critical": 95.0,  # 95% of available memory
        }
        self.alerts_enabled = True

        logger.info("AI Performance Monitor initialized")

    def record_ai_request(
        self,
        model_name: str,
        response_time: float,
        prompt_length: int,
        response_length: int,
        success: bool,
        error_message: Optional[str] = None,
        memory_usage_mb: Optional[float] = None,
        cpu_usage_percent: Optional[float] = None,
    ) -> None:
        """Record an AI request for monitoring."""
        metrics = AIPerformanceMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_name=model_name,
            response_time=response_time,
            prompt_length=prompt_length,
            response_length=response_length,
            success=success,
            error_message=error_message,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
        )

        self.metrics_history.append(metrics)

        # Check for alerts
        if self.alerts_enabled:
            self._check_alerts(metrics)

        logger.debug(f"Recorded AI metrics: {model_name} - {response_time:.2f}s")

    def get_performance_summary(self, last_n_requests: int = 100) -> Dict[str, Any]:
        """Get performance summary for the last N requests."""
        if not self.metrics_history:
            return {"error": "No metrics available"}

        # Get last N requests
        recent_metrics = list(self.metrics_history)[-last_n_requests:]

        if not recent_metrics:
            return {"error": "No recent metrics available"}

        # Calculate statistics
        response_times = [m.response_time for m in recent_metrics if m.success]
        error_count = sum(1 for m in recent_metrics if not m.success)
        total_requests = len(recent_metrics)

        summary = {
            "total_requests": total_requests,
            "successful_requests": total_requests - error_count,
            "error_count": error_count,
            "error_rate": error_count / total_requests if total_requests > 0 else 0,
            "response_times": {
                "min": min(response_times) if response_times else 0,
                "max": max(response_times) if response_times else 0,
                "avg": (
                    sum(response_times) / len(response_times) if response_times else 0
                ),
                "count": len(response_times),
            },
            "time_range": {
                "start": recent_metrics[0].timestamp,
                "end": recent_metrics[-1].timestamp,
            },
        }

        # Add model breakdown
        model_stats = {}
        for metrics in recent_metrics:
            model = metrics.model_name
            if model not in model_stats:
                model_stats[model] = {"requests": 0, "errors": 0, "response_times": []}

            model_stats[model]["requests"] += 1
            if not metrics.success:
                model_stats[model]["errors"] += 1
            else:
                model_stats[model]["response_times"].append(metrics.response_time)

        # Calculate model averages
        for model, stats in model_stats.items():
            if stats["response_times"]:
                stats["avg_response_time"] = sum(stats["response_times"]) / len(
                    stats["response_times"]
                )
                stats["error_rate"] = stats["errors"] / stats["requests"]
            else:
                stats["avg_response_time"] = 0
                stats["error_rate"] = 1.0
            del stats["response_times"]  # Remove raw data

        summary["models"] = model_stats

        return summary

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of AI system."""
        if not self.metrics_history:
            return {
                "status": "unknown",
                "message": "No metrics available",
                "last_check": datetime.now(timezone.utc).isoformat(),
            }

        # Get recent performance
        recent_summary = self.get_performance_summary(last_n_requests=20)

        # Determine health status
        status = "healthy"
        issues = []

        # Check error rate
        error_rate = recent_summary.get("error_rate", 0)
        if error_rate >= self.alert_thresholds["error_rate_critical"]:
            status = "critical"
            issues.append(f"High error rate: {error_rate:.1%}")
        elif error_rate >= self.alert_thresholds["error_rate_warning"]:
            status = "warning"
            issues.append(f"Elevated error rate: {error_rate:.1%}")

        # Check response time
        avg_response_time = recent_summary.get("response_times", {}).get("avg", 0)
        if avg_response_time >= self.alert_thresholds["response_time_critical"]:
            status = "critical"
            issues.append(f"Slow response time: {avg_response_time:.1f}s")
        elif avg_response_time >= self.alert_thresholds["response_time_warning"]:
            if status != "critical":
                status = "warning"
            issues.append(f"Elevated response time: {avg_response_time:.1f}s")

        return {
            "status": status,
            "message": "; ".join(issues) if issues else "AI system performing normally",
            "metrics": recent_summary,
            "last_check": datetime.now(timezone.utc).isoformat(),
        }

    def _check_alerts(self, metrics: AIPerformanceMetrics) -> None:
        """Check if metrics trigger any alerts."""
        alerts = []

        # Response time alerts
        if (
            metrics.success
            and metrics.response_time >= self.alert_thresholds["response_time_critical"]
        ):
            alerts.append(
                f"CRITICAL: AI response time {metrics.response_time:.1f}s exceeds critical threshold"
            )
        elif (
            metrics.success
            and metrics.response_time >= self.alert_thresholds["response_time_warning"]
        ):
            alerts.append(
                f"WARNING: AI response time {metrics.response_time:.1f}s exceeds warning threshold"
            )

        # Error alerts
        if not metrics.success:
            alerts.append(f"ERROR: AI request failed - {metrics.error_message}")

        # Memory alerts
        if (
            metrics.memory_usage_mb
            and metrics.memory_usage_mb >= self.alert_thresholds["memory_critical"]
        ):
            alerts.append(
                f"CRITICAL: Memory usage {metrics.memory_usage_mb:.1f}MB exceeds critical threshold"
            )
        elif (
            metrics.memory_usage_mb
            and metrics.memory_usage_mb >= self.alert_thresholds["memory_warning"]
        ):
            alerts.append(
                f"WARNING: Memory usage {metrics.memory_usage_mb:.1f}MB exceeds warning threshold"
            )

        # Log alerts
        for alert in alerts:
            if "CRITICAL" in alert:
                logger.critical(alert)
            elif "WARNING" in alert:
                logger.warning(alert)
            else:
                logger.error(alert)

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format."""
        if format == "json":
            metrics_data = [asdict(m) for m in self.metrics_history]
            return json.dumps(metrics_data, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def clear_metrics(self) -> None:
        """Clear all stored metrics."""
        self.metrics_history.clear()
        logger.info("AI performance metrics cleared")


# Global monitor instance
_ai_monitor = None


def get_ai_performance_monitor() -> AIPerformanceMonitor:
    """Get the global AI performance monitor instance."""
    global _ai_monitor
    if _ai_monitor is None:
        _ai_monitor = AIPerformanceMonitor()
    return _ai_monitor


# Convenience functions
def record_ai_performance(
    model_name: str,
    response_time: float,
    prompt_length: int,
    response_length: int,
    success: bool,
    error_message: Optional[str] = None,
) -> None:
    """Record AI performance metrics."""
    monitor = get_ai_performance_monitor()
    monitor.record_ai_request(
        model_name=model_name,
        response_time=response_time,
        prompt_length=prompt_length,
        response_length=response_length,
        success=success,
        error_message=error_message,
    )


def get_ai_health_status() -> Dict[str, Any]:
    """Get current AI system health status."""
    monitor = get_ai_performance_monitor()
    return monitor.get_health_status()


def get_ai_performance_summary(last_n_requests: int = 100) -> Dict[str, Any]:
    """Get AI performance summary."""
    monitor = get_ai_performance_monitor()
    return monitor.get_performance_summary(last_n_requests)
