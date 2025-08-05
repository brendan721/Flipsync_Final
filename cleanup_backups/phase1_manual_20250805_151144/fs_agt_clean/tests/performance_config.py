"""
Docker-Aware Performance Configuration for FlipSync Agentic System
================================================================

Realistic performance targets accounting for Docker overhead and production environment.
"""

import os
from typing import Dict, Any


class DockerAwarePerformanceTargets:
    """Realistic performance targets accounting for Docker overhead."""

    # Docker environment adds 500ms overhead as specified
    DOCKER_OVERHEAD_MS = 500

    # Base performance targets (without Docker)
    BASE_DECISION_TIME_TARGET = 500  # Original target

    # Adjusted targets for Docker environment
    DECISION_TIME_TARGET = BASE_DECISION_TIME_TARGET + DOCKER_OVERHEAD_MS  # 1000ms
    ACCEPTABLE_RANGE = 1500  # 1500ms maximum (allowing some buffer)

    # Production targets (when deployed without Docker)
    PRODUCTION_DECISION_TARGET = BASE_DECISION_TIME_TARGET  # 500ms

    # Performance improvement expectations
    EXPECTED_IMPROVEMENTS = {
        "decision_caching": 0.60,  # 60% improvement
        "database_optimization": 0.30,  # 30% improvement
        "analysis_streamlining": 0.20,  # 20% improvement
    }

    @classmethod
    def get_target_for_environment(cls) -> int:
        """Get performance target based on current environment."""
        # Check if running in Docker
        if cls.is_docker_environment():
            return cls.DECISION_TIME_TARGET
        else:
            return cls.PRODUCTION_DECISION_TARGET

    @classmethod
    def is_docker_environment(cls) -> bool:
        """Check if running in Docker environment."""
        return (
            os.path.exists("/.dockerenv")
            or os.environ.get("DOCKER_CONTAINER") == "true"
            or "docker" in os.environ.get("HOSTNAME", "").lower()
        )

    @classmethod
    def get_performance_expectations(cls, baseline_ms: float) -> Dict[str, Any]:
        """Calculate expected performance improvements from baseline."""
        target = cls.get_target_for_environment()

        return {
            "baseline_ms": baseline_ms,
            "target_ms": target,
            "acceptable_max_ms": cls.ACCEPTABLE_RANGE,
            "improvement_needed": max(0, baseline_ms - target),
            "improvement_percentage": max(
                0, (baseline_ms - target) / baseline_ms * 100
            ),
            "environment": "docker" if cls.is_docker_environment() else "native",
            "docker_overhead_accounted": (
                cls.DOCKER_OVERHEAD_MS if cls.is_docker_environment() else 0
            ),
        }


class PerformanceValidator:
    """Validate performance against realistic targets."""

    def __init__(self):
        self.targets = DockerAwarePerformanceTargets()

    def validate_decision_time(self, decision_time_ms: float) -> Dict[str, Any]:
        """Validate decision time against targets."""
        target = self.targets.get_target_for_environment()
        acceptable = self.targets.ACCEPTABLE_RANGE

        result = {
            "decision_time_ms": decision_time_ms,
            "target_ms": target,
            "acceptable_max_ms": acceptable,
            "meets_target": decision_time_ms <= target,
            "acceptable": decision_time_ms <= acceptable,
            "environment": (
                "docker" if self.targets.is_docker_environment() else "native"
            ),
        }

        if decision_time_ms <= target:
            result["status"] = "EXCELLENT"
            result["message"] = (
                f"✅ Decision time {decision_time_ms:.0f}ms meets target {target}ms"
            )
        elif decision_time_ms <= acceptable:
            result["status"] = "ACCEPTABLE"
            result["message"] = (
                f"⚠️ Decision time {decision_time_ms:.0f}ms acceptable but exceeds target {target}ms"
            )
        else:
            result["status"] = "NEEDS_OPTIMIZATION"
            result["message"] = (
                f"❌ Decision time {decision_time_ms:.0f}ms exceeds acceptable limit {acceptable}ms"
            )

        return result

    def calculate_improvement_progress(
        self, baseline_ms: float, current_ms: float
    ) -> Dict[str, Any]:
        """Calculate improvement progress from baseline."""
        target = self.targets.get_target_for_environment()

        baseline_improvement_needed = max(0, baseline_ms - target)
        current_improvement_needed = max(0, current_ms - target)

        if baseline_improvement_needed == 0:
            progress_percentage = 100.0  # Already at target
        else:
            improvement_achieved = (
                baseline_improvement_needed - current_improvement_needed
            )
            progress_percentage = (
                improvement_achieved / baseline_improvement_needed
            ) * 100

        return {
            "baseline_ms": baseline_ms,
            "current_ms": current_ms,
            "target_ms": target,
            "improvement_needed_baseline": baseline_improvement_needed,
            "improvement_needed_current": current_improvement_needed,
            "improvement_achieved_ms": max(0, baseline_ms - current_ms),
            "progress_percentage": max(0, min(100, progress_percentage)),
            "target_reached": current_ms <= target,
        }


# Performance test configuration
PERFORMANCE_TEST_CONFIG = {
    "decision_time_samples": 5,  # Number of decisions to test
    "warmup_decisions": 2,  # Warmup decisions to ignore
    "timeout_seconds": 30,  # Maximum time per decision test
    "cache_test_enabled": True,  # Test caching effectiveness
    "database_optimization_test": True,  # Test database optimizations
}
