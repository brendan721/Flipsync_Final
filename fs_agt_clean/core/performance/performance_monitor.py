"""
FlipSync Performance Monitor
===========================

Comprehensive performance monitoring and optimization for the 4+1 architecture.
Ensures all agents meet performance targets with production database integration.

Performance Targets:
- Autonomous agents: <500ms decision times
- Docker-aware: <1000ms total response times
- Communication: <200ms message routing
- Database operations: <300ms query times
"""

import logging
import time
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from enum import Enum

from fs_agt_clean.core.architecture.boundaries import ArchitecturalBoundaries

logger = logging.getLogger(__name__)


class PerformanceMetricType(str, Enum):
    """Types of performance metrics."""
    
    DECISION_TIME = "decision_time"
    COMMUNICATION_TIME = "communication_time"
    DATABASE_TIME = "database_time"
    TOTAL_RESPONSE_TIME = "total_response_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


@dataclass
class PerformanceMetric:
    """Individual performance metric measurement."""
    
    agent_id: str
    metric_type: PerformanceMetricType
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    context: Dict[str, Any] = field(default_factory=dict)
    target_met: bool = False
    
    def __post_init__(self):
        """Calculate if target was met based on metric type."""
        targets = {
            PerformanceMetricType.DECISION_TIME: 500.0,  # ms
            PerformanceMetricType.COMMUNICATION_TIME: 200.0,  # ms
            PerformanceMetricType.DATABASE_TIME: 300.0,  # ms
            PerformanceMetricType.TOTAL_RESPONSE_TIME: 1000.0,  # ms (Docker-aware)
        }
        
        target = targets.get(self.metric_type, float('inf'))
        self.target_met = self.value <= target


@dataclass
class AgentPerformanceProfile:
    """Performance profile for a single agent."""
    
    agent_id: str
    agent_type: str
    metrics: List[PerformanceMetric] = field(default_factory=list)
    
    def add_metric(self, metric: PerformanceMetric):
        """Add a performance metric."""
        self.metrics.append(metric)
    
    def get_average_time(self, metric_type: PerformanceMetricType) -> float:
        """Get average time for a specific metric type."""
        values = [m.value for m in self.metrics if m.metric_type == metric_type]
        return statistics.mean(values) if values else 0.0
    
    def get_success_rate(self, metric_type: PerformanceMetricType) -> float:
        """Get success rate (% of metrics meeting targets) for a metric type."""
        relevant_metrics = [m for m in self.metrics if m.metric_type == metric_type]
        if not relevant_metrics:
            return 0.0
        
        successful = sum(1 for m in relevant_metrics if m.target_met)
        return (successful / len(relevant_metrics)) * 100.0
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary."""
        summary = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "total_metrics": len(self.metrics),
            "metric_types": {}
        }
        
        for metric_type in PerformanceMetricType:
            relevant_metrics = [m for m in self.metrics if m.metric_type == metric_type]
            if relevant_metrics:
                summary["metric_types"][metric_type.value] = {
                    "count": len(relevant_metrics),
                    "average": self.get_average_time(metric_type),
                    "min": min(m.value for m in relevant_metrics),
                    "max": max(m.value for m in relevant_metrics),
                    "success_rate": self.get_success_rate(metric_type)
                }
        
        return summary


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for FlipSync 4+1 architecture.
    
    Tracks performance metrics, validates targets, and provides optimization insights.
    """
    
    def __init__(self):
        self.agent_profiles: Dict[str, AgentPerformanceProfile] = {}
        self.boundaries = ArchitecturalBoundaries()
        self.monitoring_active = True
        
    def get_or_create_profile(self, agent_id: str) -> AgentPerformanceProfile:
        """Get or create performance profile for an agent."""
        if agent_id not in self.agent_profiles:
            agent_layer = self.boundaries.validate_agent_type(agent_id)
            self.agent_profiles[agent_id] = AgentPerformanceProfile(
                agent_id=agent_id,
                agent_type=agent_layer.value
            )
        return self.agent_profiles[agent_id]
    
    def record_metric(self, agent_id: str, metric_type: PerformanceMetricType, 
                     value: float, context: Dict[str, Any] = None):
        """Record a performance metric for an agent."""
        if not self.monitoring_active:
            return
            
        profile = self.get_or_create_profile(agent_id)
        metric = PerformanceMetric(
            agent_id=agent_id,
            metric_type=metric_type,
            value=value,
            context=context or {}
        )
        profile.add_metric(metric)
        
        # Log performance issues
        if not metric.target_met:
            logger.warning(f"Performance target missed: {agent_id} {metric_type.value} = {value:.1f}ms")
    
    async def measure_decision_time(self, agent_id: str, decision_func: Callable, 
                                  context: Dict[str, Any]) -> Any:
        """Measure decision time for an agent and record the metric."""
        start_time = time.perf_counter()
        
        try:
            result = await decision_func(context)
            end_time = time.perf_counter()
            
            decision_time_ms = (end_time - start_time) * 1000
            
            self.record_metric(
                agent_id=agent_id,
                metric_type=PerformanceMetricType.DECISION_TIME,
                value=decision_time_ms,
                context={"decision_type": context.get("decision_type", "unknown")}
            )
            
            return result
            
        except Exception as e:
            end_time = time.perf_counter()
            decision_time_ms = (end_time - start_time) * 1000
            
            self.record_metric(
                agent_id=agent_id,
                metric_type=PerformanceMetricType.DECISION_TIME,
                value=decision_time_ms,
                context={"error": str(e), "decision_type": context.get("decision_type", "unknown")}
            )
            
            raise
    
    async def measure_communication_time(self, sender_id: str, recipient_id: str, 
                                       comm_func: Callable) -> Any:
        """Measure communication time between agents."""
        start_time = time.perf_counter()
        
        try:
            result = await comm_func()
            end_time = time.perf_counter()
            
            comm_time_ms = (end_time - start_time) * 1000
            
            self.record_metric(
                agent_id=sender_id,
                metric_type=PerformanceMetricType.COMMUNICATION_TIME,
                value=comm_time_ms,
                context={"recipient": recipient_id}
            )
            
            return result
            
        except Exception as e:
            end_time = time.perf_counter()
            comm_time_ms = (end_time - start_time) * 1000
            
            self.record_metric(
                agent_id=sender_id,
                metric_type=PerformanceMetricType.COMMUNICATION_TIME,
                value=comm_time_ms,
                context={"recipient": recipient_id, "error": str(e)}
            )
            
            raise
    
    def get_system_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive system performance report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_agents": len(self.agent_profiles),
            "agents": {},
            "system_summary": {
                "autonomous_agents": 0,
                "conversational_agents": 0,
                "performance_issues": 0,
                "total_metrics": 0
            }
        }
        
        performance_issues = 0
        total_metrics = 0
        
        for agent_id, profile in self.agent_profiles.items():
            agent_summary = profile.get_performance_summary()
            report["agents"][agent_id] = agent_summary
            
            # Count agent types
            if profile.agent_type == "autonomous":
                report["system_summary"]["autonomous_agents"] += 1
            elif profile.agent_type == "conversational":
                report["system_summary"]["conversational_agents"] += 1
            
            # Count performance issues
            total_metrics += len(profile.metrics)
            performance_issues += sum(1 for m in profile.metrics if not m.target_met)
        
        report["system_summary"]["performance_issues"] = performance_issues
        report["system_summary"]["total_metrics"] = total_metrics
        report["system_summary"]["success_rate"] = (
            ((total_metrics - performance_issues) / total_metrics * 100) 
            if total_metrics > 0 else 0.0
        )
        
        return report
    
    def validate_performance_targets(self) -> Dict[str, Any]:
        """Validate that all agents meet performance targets."""
        validation_report = {
            "overall_compliant": True,
            "agents": {},
            "violations": [],
            "summary": {
                "total_agents": len(self.agent_profiles),
                "compliant_agents": 0,
                "non_compliant_agents": 0
            }
        }
        
        for agent_id, profile in self.agent_profiles.items():
            agent_compliant = True
            agent_issues = []
            
            # Check decision time targets for autonomous agents
            if profile.agent_type == "autonomous":
                decision_success_rate = profile.get_success_rate(PerformanceMetricType.DECISION_TIME)
                if decision_success_rate < 95.0:  # 95% success rate required
                    agent_compliant = False
                    agent_issues.append(f"Decision time success rate: {decision_success_rate:.1f}% < 95%")
            
            # Check communication time targets
            comm_success_rate = profile.get_success_rate(PerformanceMetricType.COMMUNICATION_TIME)
            if comm_success_rate < 95.0 and comm_success_rate > 0:  # Only if communication metrics exist
                agent_compliant = False
                agent_issues.append(f"Communication time success rate: {comm_success_rate:.1f}% < 95%")
            
            validation_report["agents"][agent_id] = {
                "compliant": agent_compliant,
                "issues": agent_issues,
                "agent_type": profile.agent_type
            }
            
            if agent_compliant:
                validation_report["summary"]["compliant_agents"] += 1
            else:
                validation_report["summary"]["non_compliant_agents"] += 1
                validation_report["violations"].extend([f"{agent_id}: {issue}" for issue in agent_issues])
                validation_report["overall_compliant"] = False
        
        return validation_report
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        for agent_id, profile in self.agent_profiles.items():
            # Check for slow decision times
            avg_decision_time = profile.get_average_time(PerformanceMetricType.DECISION_TIME)
            if avg_decision_time > 400:  # Close to 500ms limit
                recommendations.append(
                    f"Optimize {agent_id} decision pipeline - average {avg_decision_time:.1f}ms"
                )
            
            # Check for slow communication
            avg_comm_time = profile.get_average_time(PerformanceMetricType.COMMUNICATION_TIME)
            if avg_comm_time > 150:  # Close to 200ms limit
                recommendations.append(
                    f"Optimize {agent_id} communication - average {avg_comm_time:.1f}ms"
                )
        
        return recommendations
    
    def clear_metrics(self, agent_id: Optional[str] = None):
        """Clear metrics for a specific agent or all agents."""
        if agent_id:
            if agent_id in self.agent_profiles:
                self.agent_profiles[agent_id].metrics.clear()
        else:
            for profile in self.agent_profiles.values():
                profile.metrics.clear()


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


# Convenience functions
def record_performance_metric(agent_id: str, metric_type: PerformanceMetricType, 
                            value: float, context: Dict[str, Any] = None):
    """Record a performance metric."""
    monitor = get_performance_monitor()
    monitor.record_metric(agent_id, metric_type, value, context)


async def measure_agent_decision(agent_id: str, decision_func: Callable, context: Dict[str, Any]) -> Any:
    """Measure and record agent decision time."""
    monitor = get_performance_monitor()
    return await monitor.measure_decision_time(agent_id, decision_func, context)
