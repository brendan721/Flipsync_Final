"""
FlipSync UnifiedAgent Monitoring System

This module provides a centralized monitoring system for all agents in the FlipSync system.
It tracks agent operations, performance metrics, and health status in real-time.
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import psutil

# Configure monitoring logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("agent_monitoring.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("agent_monitor")


class UnifiedAgentMetric:
    """Represents a single agent metric."""

    def __init__(
        self,
        name: str,
        value: Any,
        agent_id: str,
        timestamp: Optional[float] = None,
    ):
        self.name = name
        self.value = value
        self.agent_id = agent_id
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        timestamp_fmt = datetime.fromtimestamp(self.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return {
            "name": self.name,
            "value": self.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "timestamp_formatted": timestamp_fmt,
        }


class UnifiedAgentEvent:
    """Represents a significant agent event."""

    LEVEL_INFO = "INFO"
    LEVEL_WARNING = "WARNING"
    LEVEL_ERROR = "ERROR"
    LEVEL_CRITICAL = "CRITICAL"

    def __init__(
        self,
        event_type: str,
        message: str,
        agent_id: str,
        level: str = LEVEL_INFO,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ):
        self.event_type = event_type
        self.message = message
        self.agent_id = agent_id
        self.level = level
        self.details = details or {}
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        timestamp_fmt = datetime.fromtimestamp(self.timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return {
            "event_type": self.event_type,
            "message": self.message,
            "agent_id": self.agent_id,
            "level": self.level,
            "details": self.details,
            "timestamp": self.timestamp,
            "timestamp_formatted": timestamp_fmt,
        }


class UnifiedAgentHealthStatus:
    """Tracks the health status of an agent."""

    STATUS_HEALTHY = "HEALTHY"
    STATUS_DEGRADED = "DEGRADED"
    STATUS_UNHEALTHY = "UNHEALTHY"
    STATUS_UNKNOWN = "UNKNOWN"

    def __init__(
        self,
        agent_id: str,
        status: str = STATUS_UNKNOWN,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.status = status
        self.details = details or {}
        self.last_update = time.time()
        self.history: List[Dict[str, Any]] = []

    def update_status(
        self, status: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update the health status."""
        # Save the current status to history
        self.history.append(
            {
                "status": self.status,
                "details": self.details.copy(),
                "timestamp": self.last_update,
            }
        )

        # Trim history if it gets too large
        if len(self.history) > 100:
            self.history = self.history[-100:]

        # Update current status
        self.status = status
        self.details = details or {}
        self.last_update = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a dictionary for serialization."""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "details": self.details,
            "last_update": self.last_update,
            "last_update_formatted": datetime.fromtimestamp(self.last_update).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "history": self.history[-10:],  # Only include the last 10 entries
        }


class UnifiedAgentMonitor:
    """Central monitoring system for all agents."""

    def __init__(self, output_dir: str = "monitoring_data"):
        self.output_dir = output_dir
        self.metrics: Dict[str, List[UnifiedAgentMetric]] = {}  # agent_id -> metrics
        self.events: Dict[str, List[UnifiedAgentEvent]] = {}  # agent_id -> events
        self.health_status: Dict[str, UnifiedAgentHealthStatus] = (
            {}
        )  # agent_id -> health status
        self.resource_monitor_running = False
        self.resource_monitor_thread = None
        self.metric_retention_days = 7
        self.event_retention_days = 30

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

    def register_agent(self, agent_id: str) -> None:
        """Register a new agent for monitoring."""
        if agent_id not in self.metrics:
            self.metrics[agent_id] = []
        if agent_id not in self.events:
            self.events[agent_id] = []
        if agent_id not in self.health_status:
            self.health_status[agent_id] = UnifiedAgentHealthStatus(agent_id)

        logger.info(f"Registered agent {agent_id} for monitoring")

    def record_metric(self, name: str, value: Any, agent_id: str) -> None:
        """Record a metric for an agent."""
        # Make sure agent is registered
        if agent_id not in self.metrics:
            self.register_agent(agent_id)

        # Create and store the metric
        metric = UnifiedAgentMetric(name, value, agent_id)
        self.metrics[agent_id].append(metric)

        # If we have a lot of metrics, consider writing to disk
        if len(self.metrics[agent_id]) > 1000:
            self._save_metrics_to_disk(agent_id)

        # Log significant metrics
        if isinstance(value, (int, float)) and value > 0:
            logger.debug(f"UnifiedAgent {agent_id}: {name} = {value}")

    def record_event(
        self,
        event_type: str,
        message: str,
        agent_id: str,
        level: str = UnifiedAgentEvent.LEVEL_INFO,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an event for an agent."""
        # Make sure agent is registered
        if agent_id not in self.events:
            self.register_agent(agent_id)

        # Create and store the event
        event = UnifiedAgentEvent(event_type, message, agent_id, level, details)
        self.events[agent_id].append(event)

        # If we have a lot of events, consider writing to disk
        if len(self.events[agent_id]) > 1000:
            self._save_events_to_disk(agent_id)

        # Log the event
        log_func = logger.info
        if level == UnifiedAgentEvent.LEVEL_WARNING:
            log_func = logger.warning
        elif level == UnifiedAgentEvent.LEVEL_ERROR:
            log_func = logger.error
        elif level == UnifiedAgentEvent.LEVEL_CRITICAL:
            log_func = logger.critical

        log_func(f"UnifiedAgent {agent_id} {event_type}: {message}")

    def update_health_status(
        self, agent_id: str, status: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update the health status of an agent."""
        # Make sure agent is registered
        if agent_id not in self.health_status:
            self.register_agent(agent_id)

        # Update the health status
        self.health_status[agent_id].update_status(status, details)

        # Log health status changes
        if status != UnifiedAgentHealthStatus.STATUS_HEALTHY:
            logger.warning(f"UnifiedAgent {agent_id} health status changed to {status}")
        else:
            logger.info(f"UnifiedAgent {agent_id} health status: {status}")

    def get_metrics(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all metrics for an agent."""
        if agent_id not in self.metrics:
            return []

        return [metric.to_dict() for metric in self.metrics[agent_id]]

    def get_events(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all events for an agent."""
        if agent_id not in self.events:
            return []

        return [event.to_dict() for event in self.events[agent_id]]

    def get_health_status(self, agent_id: str) -> Dict[str, Any]:
        """Get the current health status for an agent."""
        if agent_id not in self.health_status:
            return {
                "agent_id": agent_id,
                "status": UnifiedAgentHealthStatus.STATUS_UNKNOWN,
                "details": {},
                "last_update": time.time(),
                "last_update_formatted": datetime.fromtimestamp(time.time()).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "history": [],
            }

        return self.health_status[agent_id].to_dict()

    def start_resource_monitoring(self, agent_id: str, interval: float = 5.0) -> None:
        """Start monitoring system resources for an agent."""
        if self.resource_monitor_running:
            return

        def monitor_resources() -> None:
            process = psutil.Process(os.getpid())
            while self.resource_monitor_running:
                try:
                    # CPU usage
                    cpu_percent = process.cpu_percent(interval=0.1)
                    self.record_metric("cpu_percent", cpu_percent, agent_id)

                    # Memory usage
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)
                    self.record_metric("memory_mb", memory_mb, agent_id)

                    # Disk I/O
                    if hasattr(process, "io_counters"):
                        io_counters = process.io_counters()
                        self.record_metric(
                            "disk_read_bytes", io_counters.read_bytes, agent_id
                        )
                        self.record_metric(
                            "disk_write_bytes", io_counters.write_bytes, agent_id
                        )

                    # Network I/O (system-wide)
                    net_io = psutil.net_io_counters()
                    self.record_metric("net_bytes_sent", net_io.bytes_sent, agent_id)
                    self.record_metric("net_bytes_recv", net_io.bytes_recv, agent_id)

                    # Check health based on resource usage
                    self._check_health_from_resources(agent_id, cpu_percent, memory_mb)

                except Exception as e:
                    logger.error(f"Error in resource monitoring: {str(e)}")

                time.sleep(interval)

        self.resource_monitor_running = True
        self.resource_monitor_thread = threading.Thread(target=monitor_resources)
        self.resource_monitor_thread.daemon = True
        self.resource_monitor_thread.start()

        logger.info(f"Started resource monitoring for agent {agent_id}")

    def stop_resource_monitoring(self) -> None:
        """Stop resource monitoring."""
        self.resource_monitor_running = False
        if self.resource_monitor_thread:
            self.resource_monitor_thread.join(timeout=2.0)
            self.resource_monitor_thread = None

        logger.info("Stopped resource monitoring")

    def generate_report(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate a monitoring report for one or all agents."""
        report = {
            "timestamp": time.time(),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "agent_count": len(self.health_status),
            "agents": [],
        }

        # Filter agents if agent_id is specified
        agent_ids = [agent_id] if agent_id else self.health_status.keys()

        for aid in agent_ids:
            if aid in self.health_status:
                agent_report = {
                    "agent_id": aid,
                    "health_status": self.health_status[aid].to_dict(),
                    "recent_metrics": self._get_recent_metrics(aid, limit=100),
                    "recent_events": self._get_recent_events(aid, limit=100),
                }
                report["agents"].append(agent_report)

        # Save the report to disk
        report_file = (
            f"{self.output_dir}/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def _get_recent_metrics(
        self, agent_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get the most recent metrics for an agent."""
        if agent_id not in self.metrics:
            return []

        # Sort metrics by timestamp, most recent first
        sorted_metrics = sorted(
            self.metrics[agent_id], key=lambda m: m.timestamp, reverse=True
        )

        # Return the most recent up to the limit
        return [metric.to_dict() for metric in sorted_metrics[:limit]]

    def _get_recent_events(
        self, agent_id: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get the most recent events for an agent."""
        if agent_id not in self.events:
            return []

        # Sort events by timestamp, most recent first
        sorted_events = sorted(
            self.events[agent_id], key=lambda e: e.timestamp, reverse=True
        )

        # Return the most recent up to the limit
        return [event.to_dict() for event in sorted_events[:limit]]

    def _save_metrics_to_disk(self, agent_id: str) -> None:
        """Save metrics to disk and clear from memory."""
        if agent_id not in self.metrics or not self.metrics[agent_id]:
            return

        # Create agent directory if it doesn't exist
        agent_dir = f"{self.output_dir}/{agent_id}"
        os.makedirs(agent_dir, exist_ok=True)

        # Save metrics to file
        metrics_file = (
            f"{agent_dir}/metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(metrics_file, "w") as f:
            json.dump(
                [metric.to_dict() for metric in self.metrics[agent_id]], f, indent=2
            )

        # Clear metrics from memory
        self.metrics[agent_id] = []

        logger.info(f"Saved {agent_id} metrics to {metrics_file}")

    def _save_events_to_disk(self, agent_id: str) -> None:
        """Save events to disk and clear from memory."""
        if agent_id not in self.events or not self.events[agent_id]:
            return

        # Create agent directory if it doesn't exist
        agent_dir = f"{self.output_dir}/{agent_id}"
        os.makedirs(agent_dir, exist_ok=True)

        # Save events to file
        events_file = (
            f"{agent_dir}/events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(events_file, "w") as f:
            json.dump([event.to_dict() for event in self.events[agent_id]], f, indent=2)

        # Clear events from memory
        self.events[agent_id] = []

        logger.info(f"Saved {agent_id} events to {events_file}")

    def _check_health_from_resources(
        self, agent_id: str, cpu_percent: float, memory_mb: float
    ) -> None:
        """Check agent health based on resource usage."""
        details = {"cpu_percent": cpu_percent, "memory_mb": memory_mb}

        # Define thresholds
        CPU_WARNING_THRESHOLD = 70.0
        CPU_CRITICAL_THRESHOLD = 90.0
        MEMORY_WARNING_THRESHOLD = 200.0  # MB
        MEMORY_CRITICAL_THRESHOLD = 400.0  # MB

        # Determine health status
        if (
            cpu_percent > CPU_CRITICAL_THRESHOLD
            or memory_mb > MEMORY_CRITICAL_THRESHOLD
        ):
            status = UnifiedAgentHealthStatus.STATUS_UNHEALTHY
        elif (
            cpu_percent > CPU_WARNING_THRESHOLD or memory_mb > MEMORY_WARNING_THRESHOLD
        ):
            status = UnifiedAgentHealthStatus.STATUS_DEGRADED
        else:
            status = UnifiedAgentHealthStatus.STATUS_HEALTHY

        # Only update if the status changed
        if (
            agent_id in self.health_status
            and self.health_status[agent_id].status != status
        ):
            self.update_health_status(agent_id, status, details)

            # Record an event for non-healthy statuses
            if status != UnifiedAgentHealthStatus.STATUS_HEALTHY:
                level = (
                    UnifiedAgentEvent.LEVEL_WARNING
                    if status == UnifiedAgentHealthStatus.STATUS_DEGRADED
                    else UnifiedAgentEvent.LEVEL_ERROR
                )
                self.record_event(
                    "HEALTH_STATUS_CHANGE",
                    f"Health status changed to {status}",
                    agent_id,
                    level,
                    details,
                )


class UnifiedAgentMonitoringMixin:
    """A mixin to add monitoring capabilities to any agent class."""

    def __init__(self, agent_id: str, monitor: UnifiedAgentMonitor):
        self.agent_id = agent_id
        self.monitor = monitor
        self.monitor.register_agent(agent_id)

    def record_metric(self, name: str, value: Any) -> None:
        """Record a metric."""
        self.monitor.record_metric(name, value, self.agent_id)

    def record_event(
        self,
        event_type: str,
        message: str,
        level: str = UnifiedAgentEvent.LEVEL_INFO,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an event."""
        self.monitor.record_event(event_type, message, self.agent_id, level, details)

    def update_health_status(
        self, status: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update the health status."""
        self.monitor.update_health_status(self.agent_id, status, details)

    def start_resource_monitoring(self, interval: float = 5.0) -> None:
        """Start monitoring resources."""
        self.monitor.start_resource_monitoring(self.agent_id, interval)

    def generate_report(self) -> Dict[str, Any]:
        """Generate a monitoring report for this agent."""
        return self.monitor.generate_report(self.agent_id)
