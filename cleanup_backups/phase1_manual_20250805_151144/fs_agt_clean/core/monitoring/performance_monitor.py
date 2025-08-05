"""
Performance Monitoring System for FlipSync Agentic System
Phase 6: Real performance metrics implementation

This module provides comprehensive performance monitoring for:
- Agent decision making response times
- Database query performance
- Memory usage tracking
- Coordination system efficiency
- Learning system performance
"""

import time
import psutil
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import json

from fs_agt_clean.core.db.database import Database
from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Individual performance metric data."""
    metric_name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    agent_id: Optional[str] = None
    operation_type: Optional[str] = None


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    report_id: str
    start_time: datetime
    end_time: datetime
    metrics: List[PerformanceMetric]
    summary: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for FlipSync agents.
    
    Provides real-time monitoring of:
    - Decision making performance
    - Database operation performance
    - Memory usage and optimization
    - Agent coordination efficiency
    """

    def __init__(self, database: Database, monitor_id: str = "flipsync_performance_monitor"):
        """Initialize performance monitor with database persistence."""
        self.database = database
        self.monitor_id = monitor_id
        self.metrics: List[PerformanceMetric] = []
        self.active_operations: Dict[str, float] = {}
        self.performance_targets = {
            "decision_time": 0.272,  # Target decision time in seconds
            "database_query": 0.100,  # Target database query time
            "memory_per_agent": 500,  # Target memory usage in MB
            "coordination_latency": 0.050,  # Target coordination latency
        }
        logger.info(f"Initialized PerformanceMonitor {monitor_id}")

    async def initialize(self) -> bool:
        """Initialize performance monitoring with database tables."""
        try:
            # Create performance metrics table if not exists
            async with self.database.get_session() as session:
                await session.execute(text("""
                    CREATE TABLE IF NOT EXISTS performance_metrics (
                        id SERIAL PRIMARY KEY,
                        monitor_id VARCHAR(255) NOT NULL,
                        metric_name VARCHAR(255) NOT NULL,
                        value FLOAT NOT NULL,
                        unit VARCHAR(50) NOT NULL,
                        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
                        context JSONB,
                        agent_id VARCHAR(255),
                        operation_type VARCHAR(255),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """))
                
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp 
                    ON performance_metrics(timestamp)
                """))
                
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_performance_metrics_agent_id 
                    ON performance_metrics(agent_id)
                """))
                
                await session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_performance_metrics_metric_name 
                    ON performance_metrics(metric_name)
                """))
                
                await session.commit()
                
            logger.info(f"✅ PerformanceMonitor initialized for {self.monitor_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize PerformanceMonitor: {e}")
            return False

    @asynccontextmanager
    async def measure_operation(
        self, 
        operation_name: str, 
        agent_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for measuring operation performance.
        
        Usage:
            async with monitor.measure_operation("decision_making", agent_id="market_agent"):
                # Perform operation
                decision = await make_decision()
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"
        start_time = time.time()
        
        try:
            self.active_operations[operation_id] = start_time
            yield operation_id
            
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Remove from active operations
            self.active_operations.pop(operation_id, None)
            
            # Record performance metric
            await self.record_metric(
                metric_name=f"{operation_name}_duration",
                value=duration,
                unit="seconds",
                agent_id=agent_id,
                operation_type=operation_name,
                context=context or {}
            )

    async def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        agent_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record a performance metric with database persistence."""
        try:
            metric = PerformanceMetric(
                metric_name=metric_name,
                value=value,
                unit=unit,
                timestamp=datetime.now(timezone.utc),
                context=context or {},
                agent_id=agent_id,
                operation_type=operation_type
            )
            
            # Add to in-memory collection
            self.metrics.append(metric)
            
            # Persist to database
            async with self.database.get_session() as session:
                await session.execute(text("""
                    INSERT INTO performance_metrics 
                    (monitor_id, metric_name, value, unit, timestamp, context, agent_id, operation_type)
                    VALUES (:monitor_id, :metric_name, :value, :unit, :timestamp, :context, :agent_id, :operation_type)
                """), {
                    "monitor_id": self.monitor_id,
                    "metric_name": metric_name,
                    "value": value,
                    "unit": unit,
                    "timestamp": metric.timestamp,
                    "context": json.dumps(context or {}),
                    "agent_id": agent_id,
                    "operation_type": operation_type
                })
                await session.commit()
            
            # Check against performance targets
            await self._check_performance_target(metric_name, value)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {e}")
            return False

    async def _check_performance_target(self, metric_name: str, value: float):
        """Check if metric meets performance targets and log warnings."""
        target_key = None
        
        if "decision" in metric_name.lower() and "duration" in metric_name.lower():
            target_key = "decision_time"
        elif "database" in metric_name.lower() or "query" in metric_name.lower():
            target_key = "database_query"
        elif "coordination" in metric_name.lower():
            target_key = "coordination_latency"
        elif "memory" in metric_name.lower():
            target_key = "memory_per_agent"
        
        if target_key and target_key in self.performance_targets:
            target = self.performance_targets[target_key]
            if value > target:
                logger.warning(
                    f"Performance target exceeded: {metric_name}={value:.4f} "
                    f"(target: {target:.4f})"
                )
            else:
                logger.debug(
                    f"Performance target met: {metric_name}={value:.4f} "
                    f"(target: {target:.4f})"
                )

    async def get_memory_usage(self, agent_id: Optional[str] = None) -> Dict[str, float]:
        """Get current memory usage metrics."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        memory_metrics = {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            "percent": process.memory_percent(),
        }
        
        # Record memory metrics
        for metric_name, value in memory_metrics.items():
            await self.record_metric(
                metric_name=f"memory_{metric_name}",
                value=value,
                unit="MB" if "mb" in metric_name else "percent",
                agent_id=agent_id,
                operation_type="memory_monitoring"
            )
        
        return memory_metrics

    async def get_performance_summary(
        self, 
        time_window_minutes: int = 60,
        agent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get performance summary for the specified time window."""
        try:
            cutoff_time = datetime.now(timezone.utc).timestamp() - (time_window_minutes * 60)
            
            # Filter metrics by time window and agent
            recent_metrics = [
                m for m in self.metrics 
                if m.timestamp.timestamp() > cutoff_time
                and (agent_id is None or m.agent_id == agent_id)
            ]
            
            if not recent_metrics:
                return {"message": "No metrics available for the specified time window"}
            
            # Group metrics by name
            metrics_by_name = {}
            for metric in recent_metrics:
                if metric.metric_name not in metrics_by_name:
                    metrics_by_name[metric.metric_name] = []
                metrics_by_name[metric.metric_name].append(metric.value)
            
            # Calculate summary statistics
            summary = {}
            for metric_name, values in metrics_by_name.items():
                summary[metric_name] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1] if values else 0
                }
            
            return {
                "time_window_minutes": time_window_minutes,
                "agent_id": agent_id,
                "metrics_count": len(recent_metrics),
                "summary": summary,
                "performance_targets": self.performance_targets
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {"error": str(e)}

    async def generate_performance_report(
        self, 
        start_time: datetime,
        end_time: datetime,
        agent_ids: Optional[List[str]] = None
    ) -> PerformanceReport:
        """Generate comprehensive performance report for specified time range."""
        try:
            # Filter metrics by time range and agents
            filtered_metrics = [
                m for m in self.metrics
                if start_time <= m.timestamp <= end_time
                and (agent_ids is None or m.agent_id in agent_ids)
            ]
            
            # Generate summary
            summary = await self.get_performance_summary(
                time_window_minutes=int((end_time - start_time).total_seconds() / 60)
            )
            
            report = PerformanceReport(
                report_id=f"perf_report_{int(time.time())}",
                start_time=start_time,
                end_time=end_time,
                metrics=filtered_metrics,
                summary=summary
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {e}")
            raise

    async def cleanup_old_metrics(self, days_to_keep: int = 7) -> int:
        """Clean up old performance metrics from database."""
        try:
            cutoff_date = datetime.now(timezone.utc).timestamp() - (days_to_keep * 24 * 60 * 60)
            
            async with self.database.get_session() as session:
                result = await session.execute(text("""
                    DELETE FROM performance_metrics 
                    WHERE monitor_id = :monitor_id 
                    AND timestamp < :cutoff_date
                """), {
                    "monitor_id": self.monitor_id,
                    "cutoff_date": datetime.fromtimestamp(cutoff_date, timezone.utc)
                })
                
                deleted_count = result.rowcount
                await session.commit()
                
            # Also clean up in-memory metrics
            self.metrics = [
                m for m in self.metrics 
                if m.timestamp.timestamp() > cutoff_date
            ]
            
            logger.info(f"Cleaned up {deleted_count} old performance metrics")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0
