"""
FlipSync Monitoring Manager

This module provides the core implementation of the monitoring system,
coordinating metrics, health checks, and alerts.

This is part of the Phase 6 Monitoring Systems Consolidation effort.
"""

import logging
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Type, Union

from fs_agt_clean.core.config import ConfigManager
from fs_agt_clean.core.monitoring.protocols import (
    Alert,
    AlertingProtocol,
    AlertRule,
    AlertSeverity,
    AlertSource,
    AlertStatus,
    ComponentType,
    HealthCheck,
    HealthCheckResult,
    HealthDependency,
    HealthProtocol,
    HealthStatus,
    MetricAggregation,
    MetricCollector,
    MetricProtocol,
    MetricType,
    MetricUnit,
    MetricValue,
    MonitorableComponent,
    MonitoringBackend,
    MonitoringPlugin,
    MonitoringProtocol,
    MonitoringStatus,
)

from .protocols.alerting_protocol import AlertChannel
from .protocols.health_protocol import HealthImpact

logger = logging.getLogger(__name__)


class MonitoringManager(
    MonitoringProtocol, MetricProtocol, AlertingProtocol, HealthProtocol
):
    """
    Central manager for the FlipSync monitoring system.

    This class coordinates all monitoring activities including:
    - Component registration and monitoring
    - Metrics collection and storage
    - Health checking and reporting
    - Alert detection and notification
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the monitoring manager.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self._components: Dict[str, MonitorableComponent] = {}
        self._backends: Dict[str, MonitoringBackend] = {}
        self._plugins: Dict[str, MonitoringPlugin] = {}
        self._collectors: Dict[str, MetricCollector] = {}
        self._collection_interval = timedelta(
            seconds=self.config.get("collection_interval_seconds", 10)
        )
        self.metrics_cache: Dict[str, List[MetricValue]] = {}
        self._health_checks: Dict[str, HealthCheck] = {}
        self._alert_rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._dependencies: Dict[str, Dict[str, HealthDependency]] = {}
        self._dependents: Dict[str, Dict[str, HealthDependency]] = {}
        self._collection_thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.RLock()

        # Initialize default metrics collectors
        self._init_default_collectors()

        logger.info("MonitoringManager initialized")

    def _init_default_collectors(self) -> None:
        """Initialize default metrics collectors."""
        # Implement based on the system's needs
        pass

    #
    # MonitoringProtocol Implementation
    #

    def register_component(self, component: MonitorableComponent) -> None:
        """Register a component for monitoring."""
        with self._lock:
            self._components[component.component_id] = component
            logger.info(
                "Component registered: %s (%s)",
                component.component_name,
                component.component_id,
            )

    def unregister_component(self, component_id: str) -> None:
        """
        Unregister a component from the monitoring system.

        Args:
            component_id: The unique identifier of the component to unregister.
        """
        with self._lock:
            if component_id in self._components:
                component = self._components.pop(component_id)
                logger.info(
                    "Component unregistered: %s (%s)",
                    component.component_name,
                    component_id,
                )
            else:
                logger.warning(
                    "Attempted to unregister unknown component: %s", component_id
                )

    def get_component(self, component_id: str) -> Optional[MonitorableComponent]:
        """Get a registered component by ID."""
        return self._components.get(component_id)

    def get_all_components(self) -> List[MonitorableComponent]:
        """Get all registered components."""
        return list(self._components.values())

    def get_components_by_type(
        self, component_type: ComponentType
    ) -> List[MonitorableComponent]:
        """Get all components of a specific type."""
        return [
            c for c in self._components.values() if c.component_type == component_type
        ]

    def get_component_metrics(self, component_id: str) -> Dict[str, Any]:
        """Get metrics for a specific component."""
        component = self.get_component(component_id)
        if not component:
            logger.warning(
                "Attempted to get metrics for unknown component: %s", component_id
            )
            return {}

        try:
            return component.get_metrics()
        except Exception as e:
            logger.error("Error getting metrics for component %s: %s", component_id, e)
            return {}

    def get_component_health(self, component_id: str) -> Dict[str, Any]:
        """Get health information for a specific component."""
        component = self.get_component(component_id)
        if not component:
            logger.warning(
                "Attempted to get health for unknown component: %s", component_id
            )
            return {"status": HealthStatus.UNKNOWN.value}

        try:
            return component.get_health()
        except Exception as e:
            logger.error("Error getting health for component %s: %s", component_id, e)
            return {"status": HealthStatus.UNKNOWN.value, "error": str(e)}

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        components_health = {}
        system_status = HealthStatus.HEALTHY

        for component_id, component in self._components.items():
            try:
                health = component.get_health()
                components_health[component_id] = health

                # Update system status based on component status
                component_status = health.get("status")
                if component_status == HealthStatus.CRITICAL.value:
                    system_status = HealthStatus.CRITICAL
                elif (
                    component_status == HealthStatus.UNHEALTHY.value
                    and system_status != HealthStatus.CRITICAL
                ):
                    system_status = HealthStatus.UNHEALTHY
                elif (
                    component_status == HealthStatus.DEGRADED.value
                    and system_status
                    not in (
                        HealthStatus.CRITICAL,
                        HealthStatus.UNHEALTHY,
                    )
                ):
                    system_status = HealthStatus.DEGRADED
            except Exception as e:
                logger.error(
                    "Error getting health for component %s: %s", component_id, e
                )
                components_health[component_id] = {
                    "status": HealthStatus.UNKNOWN.value,
                    "error": str(e),
                }

        return {
            "status": system_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "components": components_health,
        }

    def get_component_dependencies(self, component_id: str) -> Dict[str, Any]:
        """Get dependency information for a component."""
        if component_id not in self._components:
            logger.warning(
                "Attempted to get dependencies for unknown component: %s", component_id
            )
            return {"dependencies": [], "dependents": []}

        # Get direct dependencies
        dependencies = self.get_dependencies(component_id)

        # Get components that depend on this component
        dependents = self.get_dependents(component_id)

        return {
            "dependencies": [d.to_dict() for d in dependencies],
            "dependents": [d.to_dict() for d in dependents],
        }

    def register_backend(self, backend: MonitoringBackend) -> None:
        """Register a monitoring backend."""
        with self._lock:
            self._backends[backend.backend_id] = backend
            logger.info(
                "Backend registered: %s (%s)", backend.backend_name, backend.backend_id
            )

    def unregister_backend(self, backend_id: str) -> None:
        """Unregister a monitoring backend."""
        with self._lock:
            if backend_id in self._backends:
                backend = self._backends.pop(backend_id)
                logger.info(
                    "Backend unregistered: %s (%s)", backend.backend_name, backend_id
                )
            else:
                logger.warning(
                    "Attempted to unregister unknown backend: %s", backend_id
                )

    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the monitoring system."""
        with self._lock:
            self.config.update(config)

            # Update collection interval if specified
            if "collection_interval_seconds" in config:
                self._collection_interval = timedelta(
                    seconds=config["collection_interval_seconds"]
                )

            logger.info("MonitoringManager configuration updated")

    #
    # MetricProtocol Implementation
    #

    def register_metric(
        self,
        name: str,
        metric_type: MetricType,
        description: Optional[str] = None,
        unit: MetricUnit = MetricUnit.COUNT,
        default_labels: Optional[Dict[str, str]] = None,
    ) -> str:
        """Register a new metric."""
        # Implementation will be added in a subsequent phase
        metric_id = f"{name}-{uuid.uuid4()}"
        logger.info("Metric registered: %s (%s)", name, metric_id)
        return metric_id

    def unregister_metric(self, metric_id: str) -> None:
        """Unregister a metric."""
        # Implementation will be added in a subsequent phase
        logger.info("Metric unregistered: %s", metric_id)

    def collect_metric(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Collect a metric value."""
        # Simplified implementation - will be enhanced in metrics module
        metric = MetricValue(
            name=name,
            value=value,
            metric_type=MetricType.GAUGE,  # Default for now
            labels=labels,
            timestamp=timestamp,
        )

        # Store in cache and backends
        with self._lock:
            if name not in self.metrics_cache:
                self.metrics_cache[name] = []
            self.metrics_cache[name].append(metric)

            # Store in backends
            for backend in self._backends.values():
                try:
                    backend.store_metrics(
                        name, {"value": value, "labels": labels or {}}
                    )
                except Exception as e:
                    logger.error(
                        "Error storing metric in backend %s: %s", backend.backend_id, e
                    )

    def increment_counter(
        self, name: str, increment: int = 1, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        self.collect_metric(name, increment, labels)

    def set_gauge(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Set a gauge metric."""
        self.collect_metric(name, value, labels)

    def observe_histogram(
        self,
        name: str,
        value: Union[int, float],
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Add an observation to a histogram metric."""
        self.collect_metric(name, value, labels)

    def start_timer(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> callable:
        """Start a timer and return a function that stops the timer and records the duration."""
        start_time = time.time()

        def stop_timer() -> None:
            duration = time.time() - start_time
            self.collect_metric(name, duration, labels)

        return stop_timer

    def query_metrics(
        self,
        name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        aggregation: Optional[MetricAggregation] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query metrics based on criteria."""
        # Implementation will be added in metrics module
        return []

    def get_metric_names(self) -> List[str]:
        """Get all registered metric names."""
        return list(self.metrics_cache.keys())

    def get_label_keys(self, metric_name: Optional[str] = None) -> Set[str]:
        """Get all label keys for one or all metrics."""
        # Implementation will be added in metrics module
        return set()

    def get_label_values(
        self: str, metric_name: Optional[str] = None
    ) -> Set[str]:
        """Get all values for a specific label key."""
        # Implementation will be added in metrics module
        return set()

    #
    # AlertingProtocol Implementation
    #

    def register_alert_rule(self, rule: AlertRule) -> str:
        """Register a new alert rule."""
        with self._lock:
            self._alert_rules[rule.rule_id] = rule
            logger.info("Alert rule registered: %s (%s)", rule.name, rule.rule_id)
            return rule.rule_id

    def unregister_alert_rule(self, rule_id: str) -> None:
        """Unregister an alert rule."""
        with self._lock:
            if rule_id in self._alert_rules:
                rule = self._alert_rules.pop(rule_id)
                logger.info("Alert rule unregistered: %s (%s)", rule.name, rule_id)
            else:
                logger.warning(
                    "Attempted to unregister unknown alert rule: %s", rule_id
                )

    def get_alert_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get an alert rule by ID."""
        return self._alert_rules.get(rule_id)

    def get_alert_rules(
        self,
        enabled_only: bool = True,
        component_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None,
    ) -> List[AlertRule]:
        """Get alert rules based on criteria."""
        rules = []

        for rule in self._alert_rules.values():
            if enabled_only and not rule.enabled:
                continue

            if component_id is not None and component_id not in rule.components:
                continue

            if severity is not None and rule.severity != severity:
                continue

            rules.append(rule)

        return rules

    def trigger_alert(
        self,
        name: str,
        severity: AlertSeverity,
        message: str,
        component_id: Optional[str] = None,
        source: AlertSource = AlertSource.SYSTEM,
        details: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> str:
        """Trigger an alert manually."""
        alert = Alert(
            name=name,
            severity=severity,
            source=source,
            component_id=component_id,
            message=message,
            details=details,
            labels=labels,
            status=AlertStatus.ACTIVE,
        )

        with self._lock:
            self._active_alerts[alert.alert_id] = alert

        logger.warning(
            "Alert triggered: %s (%s) - %s", alert.name, alert.alert_id, alert.message
        )

        # TODO: Implement notification logic when notification system is implemented

        return alert.alert_id

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an active alert.

        Args:
            alert_id: The unique identifier of the alert to acknowledge.

        Returns:
            bool: True if the alert was successfully acknowledged, False otherwise.
        """
        with self._lock:
            if alert_id not in self._active_alerts:
                logger.warning("Attempted to acknowledge unknown alert: %s", alert_id)
                return False

            alert = self._active_alerts[alert_id]
            alert.acknowledge()

            # Move from active to acknowledged
            self._active_alerts.pop(alert_id)

            return True

    def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None) -> bool:
        """Resolve an alert."""
        with self._lock:
            if alert_id not in self._active_alerts:
                logger.warning("Attempted to resolve unknown alert: %s", alert_id)
                return False

            alert = self._active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_by = resolved_by
            alert.end_time = datetime.utcnow()

            logger.info("Alert resolved: %s (%s)", alert.name, alert_id)
            return True

    def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        return self._active_alerts.get(alert_id)

    def get_alerts(
        self,
        status: Optional[Union[AlertStatus, List[AlertStatus]]] = None,
        severity: Optional[Union[AlertSeverity, List[AlertSeverity]]] = None,
        component_id: Optional[str] = None,
        from_time: Optional[datetime] = None,
        to_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
    ) -> List[Alert]:
        """Get alerts based on criteria."""
        alerts = []

        # Convert single values to lists for uniform processing
        if status is not None and not isinstance(status, list):
            status = [status]

        if severity is not None and not isinstance(severity, list):
            severity = [severity]

        for alert in self._active_alerts.values():
            # Filter by status
            if status is not None and alert.status not in status:
                continue

            # Filter by severity
            if severity is not None and alert.severity not in severity:
                continue

            # Filter by component ID
            if component_id is not None and alert.component_id != component_id:
                continue

            # Filter by time range
            if from_time is not None and alert.start_time < from_time:
                continue

            if to_time is not None and alert.start_time > to_time:
                continue

            # Filter by labels
            if labels is not None:
                match = True
                for key, value in labels.items():
                    if key not in alert.labels or alert.labels[key] != value:
                        match = False
                        break

                if not match:
                    continue

            alerts.append(alert)

            # Apply limit if specified
            if limit is not None and len(alerts) >= limit:
                break

        return alerts

    def register_alert_channel(self, channel: "AlertChannel") -> str:
        """Register a notification channel."""
        # Implementation will be added in alerts module
        return channel.channel_id

    def unregister_alert_channel(self, channel_id: str) -> None:
        """Unregister a notification channel."""
        # Implementation will be added in alerts module
        pass

    def get_alert_channel(self, channel_id: str) -> Optional["AlertChannel"]:
        """Get a notification channel by ID."""
        # Implementation will be added in alerts module
        return None

    def get_alert_channels(
        self, enabled_only: bool = True, channel_type: Optional[str] = None
    ) -> List["AlertChannel"]:
        """Get notification channels based on criteria."""
        # Implementation will be added in alerts module
        return []

    def send_notification(
        self, alert: Alert, channels: Optional[List[str]] = None, force: bool = False
    ) -> bool:
        """Send a notification for an alert."""
        # Implementation will be added in alerts module
        return True

    #
    # HealthProtocol Implementation
    #

    def register_health_check(self, health_check: HealthCheck) -> str:
        """Register a new health check."""
        with self._lock:
            self._health_checks[health_check.check_id] = health_check
            logger.info(
                "Health check registered: %s (%s)",
                health_check.name,
                health_check.check_id,
            )
            return health_check.check_id

    def unregister_health_check(self, check_id: str) -> None:
        """Unregister a health check."""
        with self._lock:
            if check_id in self._health_checks:
                check = self._health_checks.pop(check_id)
                logger.info("Health check unregistered: %s (%s)", check.name, check_id)
            else:
                logger.warning(
                    "Attempted to unregister unknown health check: %s", check_id
                )

    def get_health_check(self, check_id: str) -> Optional[HealthCheck]:
        """Get a health check by ID."""
        return self._health_checks.get(check_id)

    def get_health_checks(
        self,
        component_id: Optional[str] = None,
        enabled_only: bool = True,
        critical_only: bool = False,
    ) -> List[HealthCheck]:
        """Get health checks based on criteria."""
        checks = []

        for check in self._health_checks.values():
            if enabled_only and not check.enabled:
                continue

            if component_id is not None and check.component_id != component_id:
                continue

            if critical_only and not check.critical:
                continue

            checks.append(check)

        return checks

    def execute_health_check(self, check_id: str) -> HealthCheckResult:
        """Execute a specific health check and return the result."""
        # This is a placeholder. In a real implementation, this would delegate to a HealthChecker
        if check_id not in self._health_checks:
            logger.warning("Attempted to execute unknown health check: %s", check_id)
            return HealthCheckResult(
                check_id=check_id,
                component_id="unknown",
                status=HealthStatus.UNKNOWN,
                message="Health check not found",
            )

        check = self._health_checks[check_id]
        component = self.get_component(check.component_id)

        if not component:
            logger.warning(
                "Health check %s references unknown component: %s",
                check_id,
                check.component_id,
            )
            return HealthCheckResult(
                check_id=check_id,
                component_id=check.component_id,
                status=HealthStatus.UNKNOWN,
                message="Component not found",
            )

        try:
            # In a real implementation, this would use a proper health checker
            component_health = component.get_health()
            status_str = component_health.get("status", HealthStatus.UNKNOWN.value)

            # Map string status to enum
            status = HealthStatus.UNKNOWN
            for s in HealthStatus:
                if s.value == status_str:
                    status = s
                    break

            return HealthCheckResult(
                check_id=check_id,
                component_id=check.component_id,
                status=status,
                message=component_health.get("message", ""),
                details=component_health,
            )
        except Exception as e:
            logger.error("Error executing health check %s: %s", check_id, e)
            return HealthCheckResult(
                check_id=check_id,
                component_id=check.component_id,
                status=HealthStatus.UNKNOWN,
                message=f"Error executing health check: {e}",
            )

    def get_health_status(
        self,
        component_id: Optional[str] = None,
        include_dependencies: bool = True,
        include_details: bool = False,
    ) -> Dict[str, Any]:
        """Get health status for a component or the entire system."""
        if component_id is not None:
            # Get health for a specific component
            component = self.get_component(component_id)
            if not component:
                logger.warning(
                    "Attempted to get health status for unknown component: %s",
                    component_id,
                )
                return {
                    "status": HealthStatus.UNKNOWN.value,
                    "message": "Component not found",
                    "timestamp": datetime.utcnow().isoformat(),
                }

            try:
                health = component.get_health()

                if include_dependencies:
                    # Get and include dependency health
                    dependencies = self.get_dependencies(component_id)
                    dependency_health = {}

                    for dep in dependencies:
                        dep_health = self.get_health_status(
                            dep.target_id,
                            include_dependencies=False,
                            include_details=include_details,
                        )
                        dependency_health[dep.target_id] = dep_health

                    health["dependencies"] = dependency_health

                return health
            except Exception as e:
                logger.error(
                    "Error getting health status for component %s: %s", component_id, e
                )
                return {
                    "status": HealthStatus.UNKNOWN.value,
                    "message": f"Error getting health status: {e}",
                    "timestamp": datetime.utcnow().isoformat(),
                }
        else:
            # Get system-wide health
            return self.get_system_health()

    def register_dependency(
        self,
        source_id: str,
        target_id: str,
        dependency_type: str = "required",
        impact: "HealthImpact" = None,  # Default will be set in method
        description: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """Register a dependency between components."""
        from .protocols import HealthImpact  # Import here to avoid circular imports

        if impact is None:
            impact = HealthImpact.HIGH

        dependency = HealthDependency(
            source_id=source_id,
            target_id=target_id,
            dependency_type=dependency_type,
            impact=impact,
            description=description,
            labels=labels,
        )

        with self._lock:
            # Register in dependencies dict
            if source_id not in self._dependencies:
                self._dependencies[source_id] = {}
            self._dependencies[source_id][target_id] = dependency

            # Register in dependents dict for reverse lookup
            if target_id not in self._dependents:
                self._dependents[target_id] = {}
            self._dependents[target_id][source_id] = dependency

            logger.info(
                "Dependency registered: %s -> %s (%s)",
                source_id,
                target_id,
                dependency_type,
            )

    def unregister_dependency(self, source_id: str, target_id: str) -> None:
        """Unregister a dependency between components."""
        with self._lock:
            # Remove from dependencies dict
            if (
                source_id in self._dependencies
                and target_id in self._dependencies[source_id]
            ):
                self._dependencies[source_id].pop(target_id)
                if not self._dependencies[source_id]:  # Clean up empty dict
                    self._dependencies.pop(source_id)

            # Remove from dependents dict
            if (
                target_id in self._dependents
                and source_id in self._dependents[target_id]
            ):
                self._dependents[target_id].pop(source_id)
                if not self._dependents[target_id]:  # Clean up empty dict
                    self._dependents.pop(target_id)

            logger.info("Dependency unregistered: %s -> %s", source_id, target_id)

    def get_dependencies(
        self,
        component_id: str,
        recursive: bool = False,
        dependency_type: Optional[str] = None,
    ) -> List[HealthDependency]:
        """Get dependencies for a component."""
        if component_id not in self._dependencies:
            return []

        dependencies = []
        visited = set() if recursive else None

        def collect_dependencies(
            cid: str, visited_set: Optional[Set[str]] = None
        ) -> None:
            """Recursively collect dependencies."""
            if visited_set is not None:
                if cid in visited_set:
                    return
                visited_set.add(cid)

            if cid not in self._dependencies:
                return

            for dep in self._dependencies[cid].values():
                if dependency_type is None or dep.dependency_type == dependency_type:
                    dependencies.append(dep)

                if visited_set is not None:
                    collect_dependencies(dep.target_id, visited_set)

        collect_dependencies(component_id, visited)
        return dependencies

    def get_dependents(
        self,
        component_id: str,
        recursive: bool = False,
        dependency_type: Optional[str] = None,
    ) -> List[HealthDependency]:
        """Get components that depend on the specified component."""
        if component_id not in self._dependents:
            return []

        dependents = []
        visited = set() if recursive else None

        def collect_dependents(
            cid: str, visited_set: Optional[Set[str]] = None
        ) -> None:
            """Recursively collect dependents."""
            if visited_set is not None:
                if cid in visited_set:
                    return
                visited_set.add(cid)

            if cid not in self._dependents:
                return

            for dep in self._dependents[cid].values():
                if dependency_type is None or dep.dependency_type == dependency_type:
                    dependents.append(dep)

                if visited_set is not None:
                    collect_dependents(dep.source_id, visited_set)

        collect_dependents(component_id, visited)
        return dependents

    #
    # Collection and Maintenance
    #

    def start(self) -> None:
        """Start the monitoring system."""
        with self._lock:
            if self._running:
                logger.warning("MonitoringManager is already running")
                return

            self._running = True
            self._collection_thread = threading.Thread(
                target=self._collection_loop, daemon=True, name="monitoring-collection"
            )
            self._collection_thread.start()

            logger.info("MonitoringManager started")

    def stop(self) -> None:
        """Stop the monitoring system."""
        with self._lock:
            if not self._running:
                logger.warning("MonitoringManager is not running")
                return

            self._running = False
            if self._collection_thread and self._collection_thread.is_alive():
                self._collection_thread.join(timeout=5.0)

            logger.info("MonitoringManager stopped")

    def _collection_loop(self) -> None:
        """Background thread for periodic metrics collection and health checks."""
        logger.info("Metrics collection thread started")

        while self._running:
            try:
                # Collect metrics
                self._collect_metrics()

                # Run health checks
                self._run_health_checks()

                # Evaluate alert rules
                self._evaluate_alert_rules()

                # Prune old data
                self._prune_old_data()

            except Exception as e:
                logger.error("Error in metrics collection loop: %s", e)

            # Sleep for the collection interval
            time.sleep(self._collection_interval.total_seconds())

    def _collect_metrics(self) -> None:
        """Collect metrics from registered components and collectors."""
        for collector_id, collector in self._collectors.items():
            try:
                metrics = collector.collect_metrics()
                for metric in metrics:
                    try:
                        if metric.name not in self.metrics_cache:
                            self.metrics_cache[metric.name] = []
                        self.metrics_cache[metric.name].append(metric)
                    except Exception as e:
                        logger.error(
                            "Error storing metric %s from collector %s: %s",
                            metric.name,
                            collector_id,
                            e,
                        )
            except Exception as e:
                logger.error(
                    "Error collecting metrics from collector %s: %s", collector_id, e
                )

    def _run_health_checks(self) -> None:
        """Run registered health checks."""
        for check_id, check in self._health_checks.items():
            if not check.enabled:
                continue

            try:
                result = self.execute_health_check(check_id)

                # Check if we need to trigger an alert
                if result.status in (HealthStatus.UNHEALTHY, HealthStatus.CRITICAL):
                    self.trigger_alert(
                        name=f"Health check failed: {check.name}",
                        severity=(
                            AlertSeverity.CRITICAL
                            if result.status == HealthStatus.CRITICAL
                            else AlertSeverity.ERROR
                        ),
                        message=result.message
                        or f"Health check {check.name} failed with status {result.status.value}",
                        component_id=check.component_id,
                        source=AlertSource.HEALTH,
                        details=result.to_dict(),
                    )
            except Exception as e:
                logger.error("Error running health check %s: %s", check_id, e)

    def _evaluate_alert_rules(self) -> None:
        """Evaluate registered alert rules."""
        # This is a placeholder. Actual implementation would be in the alerts module
        pass

    def _prune_old_data(self) -> None:
        """Prune old metrics and alerts to prevent memory issues."""
        # This is a placeholder. Actual implementation would depend on retention policies
        pass

    def parse_health_status(self, status_str: str) -> HealthStatus:
        """
        Parse a string representation of health status into the enum.

        Args:
            status_str: The string representation of the health status.

        Returns:
            HealthStatus: The corresponding health status enum value.
        """
        status = HealthStatus.UNKNOWN
        for s in HealthStatus:
            if s.value == status_str:
                status = s
                break
        return status
