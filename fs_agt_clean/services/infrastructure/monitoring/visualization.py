"""
FlipSync UnifiedAgent Monitoring Visualization

This module provides visualization tools for agent monitoring data.
It generates monitoring dashboards and visualizations for metrics,
alerts, and agent health status.
"""

import json
import logging
import os
import time

import matplotlib
import numpy as np

matplotlib.use("Agg")  # Use non-interactive backend
import base64
from datetime import datetime, timedelta
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple, Union

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

# Import monitoring components
from fs_agt_clean.core.monitoring.agent_monitor import UnifiedAgentHealthStatus, UnifiedAgentMonitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("monitoring_visualization.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("monitoring_visualization")


class MonitoringDashboard:
    """Generates monitoring dashboards for agent performance."""

    def __init__(
        self, monitor: UnifiedAgentMonitor, output_dir: str = "monitoring_dashboards"
    ):
        self.monitor = monitor
        self.output_dir = output_dir

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/images", exist_ok=True)

    def generate_agent_dashboard(self, agent_id: str, hours: int = 24) -> str:
        """Generate a monitoring dashboard for a specific agent."""
        try:
            # Get agent data
            metrics = self.monitor.get_metrics(agent_id)
            events = self.monitor.get_events(agent_id)
            health_status = self.monitor.get_health_status(agent_id)

            # Filter by time
            cutoff_time = time.time() - (hours * 3600)
            recent_metrics = [m for m in metrics if m["timestamp"] >= cutoff_time]
            recent_events = [e for e in events if e["timestamp"] >= cutoff_time]

            # Generate resource usage charts
            cpu_chart = self._generate_cpu_chart(agent_id, recent_metrics)
            memory_chart = self._generate_memory_chart(agent_id, recent_metrics)

            # Generate dashboard HTML
            dashboard_html = self._generate_dashboard_html(
                agent_id=agent_id,
                health_status=health_status,
                metrics=recent_metrics,
                events=recent_events,
                cpu_chart=cpu_chart,
                memory_chart=memory_chart,
                time_period=f"Last {hours} hours",
            )

            # Save dashboard to file
            dashboard_file = f"{self.output_dir}/{agent_id}_dashboard.html"
            with open(dashboard_file, "w") as f:
                f.write(dashboard_html)

            logger.info(f"Generated dashboard for agent {agent_id}: {dashboard_file}")
            return dashboard_file

        except Exception as e:
            logger.error(f"Failed to generate dashboard for agent {agent_id}: {str(e)}")
            return ""

    def generate_system_dashboard(self, hours: int = 24) -> str:
        """Generate a system-wide monitoring dashboard."""
        try:
            # Get list of all agents
            agent_ids = set()

            # Add agents from metrics
            for agent_id in self.monitor.metrics.keys():
                agent_ids.add(agent_id)

            # Add agents from events
            for agent_id in self.monitor.events.keys():
                agent_ids.add(agent_id)

            # Add agents from health status
            for agent_id in self.monitor.health_status.keys():
                agent_ids.add(agent_id)

            # Generate agent health table
            health_table = self._generate_health_table(agent_ids)

            # Generate recent alerts list
            alerts_list = self._generate_alerts_list(agent_ids, hours)

            # Generate system metrics chart
            system_chart = self._generate_system_chart(agent_ids, hours)

            # Generate dashboard HTML
            dashboard_html = self._generate_system_dashboard_html(
                agent_ids=list(agent_ids),
                health_table=health_table,
                alerts_list=alerts_list,
                system_chart=system_chart,
                time_period=f"Last {hours} hours",
            )

            # Save dashboard to file
            dashboard_file = f"{self.output_dir}/system_dashboard.html"
            with open(dashboard_file, "w") as f:
                f.write(dashboard_html)

            logger.info(f"Generated system dashboard: {dashboard_file}")
            return dashboard_file

        except Exception as e:
            logger.error(f"Failed to generate system dashboard: {str(e)}")
            return ""

    def _generate_cpu_chart(self, agent_id: str, metrics: List[Dict[str, Any]]) -> str:
        """Generate a CPU usage chart for an agent."""
        # Filter CPU metrics
        cpu_metrics = [m for m in metrics if m["name"] == "cpu_percent"]

        if not cpu_metrics:
            return ""

        # Prepare data
        timestamps = [datetime.fromtimestamp(m["timestamp"]) for m in cpu_metrics]
        cpu_values = [float(m["value"]) for m in cpu_metrics]

        # Create figure
        plt.figure(figsize=(10, 4))
        plt.plot(timestamps, cpu_values, "b-")
        plt.title(f"CPU Usage - UnifiedAgent {agent_id}")
        plt.xlabel("Time")
        plt.ylabel("CPU (%)")
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 100)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.gcf().autofmt_xdate()

        # Add warning and critical thresholds
        plt.axhline(
            y=70, color="orange", linestyle="--", alpha=0.7, label="Warning Threshold"
        )
        plt.axhline(
            y=90, color="red", linestyle="--", alpha=0.7, label="Critical Threshold"
        )
        plt.legend()

        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=80)
        plt.close()

        # Save to file
        img_path = f"{self.output_dir}/images/{agent_id}_cpu_{int(time.time())}.png"
        with open(img_path, "wb") as f:
            f.write(buffer.getvalue())

        # Convert to base64 for embedding in HTML
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"

    def _generate_memory_chart(
        self, agent_id: str, metrics: List[Dict[str, Any]]
    ) -> str:
        """Generate a memory usage chart for an agent."""
        # Filter memory metrics
        memory_metrics = [m for m in metrics if m["name"] == "memory_mb"]

        if not memory_metrics:
            return ""

        # Prepare data
        timestamps = [datetime.fromtimestamp(m["timestamp"]) for m in memory_metrics]
        memory_values = [float(m["value"]) for m in memory_metrics]

        # Create figure
        plt.figure(figsize=(10, 4))
        plt.plot(timestamps, memory_values, "g-")
        plt.title(f"Memory Usage - UnifiedAgent {agent_id}")
        plt.xlabel("Time")
        plt.ylabel("Memory (MB)")
        plt.grid(True, alpha=0.3)

        # Format x-axis
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.gcf().autofmt_xdate()

        # Add warning and critical thresholds
        plt.axhline(
            y=200, color="orange", linestyle="--", alpha=0.7, label="Warning Threshold"
        )
        plt.axhline(
            y=400, color="red", linestyle="--", alpha=0.7, label="Critical Threshold"
        )
        plt.legend()

        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=80)
        plt.close()

        # Save to file
        img_path = f"{self.output_dir}/images/{agent_id}_memory_{int(time.time())}.png"
        with open(img_path, "wb") as f:
            f.write(buffer.getvalue())

        # Convert to base64 for embedding in HTML
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"

    def _generate_health_table(self, agent_ids: set) -> str:
        """Generate an HTML table of agent health status."""
        table_html = """
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>UnifiedAgent ID</th>
                    <th>Health Status</th>
                    <th>Last Updated</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody>
        """

        for agent_id in agent_ids:
            health = self.monitor.get_health_status(agent_id)

            # Determine status color
            status_class = "text-success"
            if health["status"] == UnifiedAgentHealthStatus.STATUS_DEGRADED:
                status_class = "text-warning"
            elif health["status"] == UnifiedAgentHealthStatus.STATUS_UNHEALTHY:
                status_class = "text-danger"
            elif health["status"] == UnifiedAgentHealthStatus.STATUS_UNKNOWN:
                status_class = "text-secondary"

            # Format details
            details_str = (
                ", ".join([f"{k}: {v}" for k, v in health["details"].items()])
                if health["details"]
                else "No details"
            )

            table_html += f"""
                <tr>
                    <td>{agent_id}</td>
                    <td><span class="{status_class}">{health["status"]}</span></td>
                    <td>{health["last_update_formatted"]}</td>
                    <td>{details_str}</td>
                </tr>
            """

        table_html += """
            </tbody>
        </table>
        """

        return table_html

    def _generate_alerts_list(self, agent_ids: set, hours: int) -> str:
        """Generate HTML list of recent alerts."""
        # For now, we'll just create a placeholder
        # In a real implementation, this would need to fetch from an AlertManager

        alerts_html = """
        <div class="alert-list">
            <h4>Recent Alerts</h4>
            <p>Alert data would be displayed here, from the AlertManager component.</p>
            <ul class="list-group">
        """

        # This is just example data - replace with real alerts
        example_alerts = [
            {
                "agent_id": list(agent_ids)[0] if agent_ids else "unknown",
                "severity": "WARNING",
                "message": "High CPU usage detected",
                "timestamp_formatted": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            {
                "agent_id": list(agent_ids)[0] if agent_ids else "unknown",
                "severity": "ERROR",
                "message": "Memory threshold exceeded",
                "timestamp_formatted": (datetime.now() - timedelta(hours=2)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            },
        ]

        for alert in example_alerts:
            severity_class = "list-group-item-warning"
            if alert["severity"] == "ERROR":
                severity_class = "list-group-item-danger"
            elif alert["severity"] == "CRITICAL":
                severity_class = "list-group-item-danger"

            alerts_html += f"""
                <li class="list-group-item {severity_class}">
                    <strong>{alert["timestamp_formatted"]}</strong> -
                    UnifiedAgent {alert["agent_id"]}: {alert["message"]}
                </li>
            """

        alerts_html += """
            </ul>
        </div>
        """

        return alerts_html

    def _generate_system_chart(self, agent_ids: set, hours: int) -> str:
        """Generate a system-wide resource usage chart."""
        # Create a plot showing average CPU and memory across all agents
        agent_cpu_data = {}
        agent_memory_data = {}

        cutoff_time = time.time() - (hours * 3600)

        # Collect data for each agent
        for agent_id in agent_ids:
            metrics = self.monitor.get_metrics(agent_id)
            recent_metrics = [m for m in metrics if m["timestamp"] >= cutoff_time]

            cpu_metrics = [m for m in recent_metrics if m["name"] == "cpu_percent"]
            memory_metrics = [m for m in recent_metrics if m["name"] == "memory_mb"]

            if cpu_metrics:
                agent_cpu_data[agent_id] = {
                    "timestamps": [m["timestamp"] for m in cpu_metrics],
                    "values": [float(m["value"]) for m in cpu_metrics],
                }

            if memory_metrics:
                agent_memory_data[agent_id] = {
                    "timestamps": [m["timestamp"] for m in memory_metrics],
                    "values": [float(m["value"]) for m in memory_metrics],
                }

        if not agent_cpu_data and not agent_memory_data:
            return ""

        # Create a figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

        # Plot CPU data
        for agent_id, data in agent_cpu_data.items():
            timestamps = [datetime.fromtimestamp(ts) for ts in data["timestamps"]]
            ax1.plot(timestamps, data["values"], label=agent_id)

        ax1.set_title("CPU Usage by UnifiedAgent")
        ax1.set_ylabel("CPU (%)")
        ax1.grid(True, alpha=0.3)
        ax1.legend()

        # Plot memory data
        for agent_id, data in agent_memory_data.items():
            timestamps = [datetime.fromtimestamp(ts) for ts in data["timestamps"]]
            ax2.plot(timestamps, data["values"], label=agent_id)

        ax2.set_title("Memory Usage by UnifiedAgent")
        ax2.set_xlabel("Time")
        ax2.set_ylabel("Memory (MB)")
        ax2.grid(True, alpha=0.3)
        ax2.legend()

        # Format x-axis
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        fig.autofmt_xdate()

        # Adjust layout
        plt.tight_layout()

        # Save to buffer
        buffer = BytesIO()
        plt.savefig(buffer, format="png", dpi=80)
        plt.close()

        # Save to file
        img_path = f"{self.output_dir}/images/system_overview_{int(time.time())}.png"
        with open(img_path, "wb") as f:
            f.write(buffer.getvalue())

        # Convert to base64 for embedding in HTML
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"

    def _generate_dashboard_html(
        self,
        agent_id: str,
        health_status: Dict[str, Any],
        metrics: List[Dict[str, Any]],
        events: List[Dict[str, Any]],
        cpu_chart: str,
        memory_chart: str,
        time_period: str,
    ) -> str:
        """Generate HTML for agent dashboard."""
        # Generate status badge
        status_class = "badge bg-success"
        if health_status["status"] == UnifiedAgentHealthStatus.STATUS_DEGRADED:
            status_class = "badge bg-warning"
        elif health_status["status"] == UnifiedAgentHealthStatus.STATUS_UNHEALTHY:
            status_class = "badge bg-danger"
        elif health_status["status"] == UnifiedAgentHealthStatus.STATUS_UNKNOWN:
            status_class = "badge bg-secondary"

        # Generate recent events table
        events_html = """
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Type</th>
                    <th>Level</th>
                    <th>Message</th>
                </tr>
            </thead>
            <tbody>
        """

        # Sort events by timestamp, most recent first
        sorted_events = sorted(events, key=lambda e: e["timestamp"], reverse=True)

        # Take only the 10 most recent events
        for event in sorted_events[:10]:
            # Determine event level style
            level_class = ""
            if event["level"] == "WARNING":
                level_class = "text-warning"
            elif event["level"] == "ERROR":
                level_class = "text-danger"
            elif event["level"] == "CRITICAL":
                level_class = "text-danger"

            events_html += f"""
                <tr>
                    <td>{event["timestamp_formatted"]}</td>
                    <td>{event["event_type"]}</td>
                    <td class="{level_class}">{event["level"]}</td>
                    <td>{event["message"]}</td>
                </tr>
            """

        events_html += """
            </tbody>
        </table>
        """

        # Generate key metrics
        cpu_avg = "N/A"
        cpu_max = "N/A"
        memory_avg = "N/A"
        memory_max = "N/A"

        cpu_metrics = [float(m["value"]) for m in metrics if m["name"] == "cpu_percent"]
        memory_metrics = [
            float(m["value"]) for m in metrics if m["name"] == "memory_mb"
        ]

        if cpu_metrics:
            cpu_avg = f"{np.mean(cpu_metrics):.1f}%"
            cpu_max = f"{np.max(cpu_metrics):.1f}%"

        if memory_metrics:
            memory_avg = f"{np.mean(memory_metrics):.1f} MB"
            memory_max = f"{np.max(memory_metrics):.1f} MB"

        # Create HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UnifiedAgent {agent_id} Dashboard - FlipSync</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ padding: 20px; }}
        .chart-container {{ margin-bottom: 20px; }}
        .metrics-card {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="row mb-4">
            <div class="col">
                <h1>UnifiedAgent Dashboard: {agent_id}</h1>
                <p class="lead">
                    Status: <span class="{status_class}">{health_status["status"]}</span>
                    <span class="ms-3">Last Updated: {health_status["last_update_formatted"]}</span>
                    <span class="ms-3">Time Period: {time_period}</span>
                </p>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card metrics-card">
                    <div class="card-header">
                        CPU Usage
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">{cpu_avg}</h5>
                        <p class="card-text">Average</p>
                        <h5 class="card-title">{cpu_max}</h5>
                        <p class="card-text">Maximum</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card metrics-card">
                    <div class="card-header">
                        Memory Usage
                    </div>
                    <div class="card-body">
                        <h5 class="card-title">{memory_avg}</h5>
                        <p class="card-text">Average</p>
                        <h5 class="card-title">{memory_max}</h5>
                        <p class="card-text">Maximum</p>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card metrics-card">
                    <div class="card-header">
                        Health Status Details
                    </div>
                    <div class="card-body">
                        <pre>{json.dumps(health_status["details"], indent=2)}</pre>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col">
                <div class="card chart-container">
                    <div class="card-header">
                        CPU Usage Over Time
                    </div>
                    <div class="card-body">
                        <img src="{cpu_chart}" class="img-fluid" alt="CPU Usage Chart">
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col">
                <div class="card chart-container">
                    <div class="card-header">
                        Memory Usage Over Time
                    </div>
                    <div class="card-body">
                        <img src="{memory_chart}" class="img-fluid" alt="Memory Usage Chart">
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        Recent Events
                    </div>
                    <div class="card-body">
                        {events_html}
                    </div>
                </div>
            </div>
        </div>

        <footer class="mt-5">
            <p class="text-center text-muted">FlipSync UnifiedAgent Monitoring System</p>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
        return html

    def _generate_system_dashboard_html(
        self,
        agent_ids: List[str],
        health_table: str,
        alerts_list: str,
        system_chart: str,
        time_period: str,
    ) -> str:
        """Generate HTML for system dashboard."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Dashboard - FlipSync</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ padding: 20px; }}
        .chart-container {{ margin-bottom: 20px; }}
        .metrics-card {{ margin-bottom: 20px; }}
        .alert-list {{ margin-bottom: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="row mb-4">
            <div class="col">
                <h1>FlipSync System Dashboard</h1>
                <p class="lead">
                    <span>UnifiedAgent Count: {len(agent_ids)}</span>
                    <span class="ms-3">Time Period: {time_period}</span>
                    <span class="ms-3">Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>
                </p>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        UnifiedAgent Health Status
                    </div>
                    <div class="card-body">
                        {health_table}
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col">
                <div class="card chart-container">
                    <div class="card-header">
                        System Resource Usage
                    </div>
                    <div class="card-body">
                        <img src="{system_chart}" class="img-fluid" alt="System Resource Usage Chart">
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        Recent Alerts
                    </div>
                    <div class="card-body">
                        {alerts_list}
                    </div>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col">
                <div class="card">
                    <div class="card-header">
                        UnifiedAgent Links
                    </div>
                    <div class="card-body">
                        <ul class="list-group">
"""

        # Add links to individual agent dashboards
        for agent_id in agent_ids:
            html += f"""
                            <li class="list-group-item">
                                <a href="{agent_id}_dashboard.html">UnifiedAgent {agent_id} Dashboard</a>
                            </li>
"""

        html += """
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <footer class="mt-5">
            <p class="text-center text-muted">FlipSync UnifiedAgent Monitoring System</p>
        </footer>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""
        return html
