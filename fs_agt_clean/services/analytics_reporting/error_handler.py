import asyncio
import logging
import os
import time
from typing import Any, Dict, List, Optional

from fs_agt_clean.core.config.manager import ConfigManager
from fs_agt_clean.core.monitoring.log_manager import LogManager


class MetricsError:
    """Represents a metrics service error."""

    def __init__(self, message: str, error: Optional[Exception] = None):
        self.message = message
        self.error = error
        self.timestamp = logging.Formatter().converter(time.time())
        self.resolved = False
        self.recovery_attempts = 0

    def __str__(self):
        if self.error:
            return f"{self.message}: {str(self.error)}"
        return self.message


class MetricsErrorHandler:
    """Handle errors in the metrics service."""

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize error handler.

        Args:
            config_manager: Optional configuration manager instance
        """
        default_config_path = os.path.join(
            os.path.dirname(__file__), "config", "error_handler.json"
        )
        self.config = config_manager or ConfigManager(config_path=default_config_path)
        log_level = getattr(logging, self.config.get("logging.level", "INFO"))
        self.log_manager = LogManager(log_level=log_level)
        self.errors: List[MetricsError] = []
        self.max_errors = self.config.get("error_handler.max_errors", 1000)
        self.max_recovery_attempts = self.config.get(
            "error_handler.max_recovery_attempts", 3
        )
        self.recovery_delay = self.config.get("error_handler.recovery_delay", 1.0)
        self._component_states: Dict[str, bool] = {}

        # Component references
        self._collector = None
        self._monitor = None
        self._optimizer = None
        self._exporter = None

    def register_component(self, component_type: str, component: Any):
        """Register a component for monitoring.

        Args:
            component_type: Type of component ("collector", "monitor", etc.)
            component: The component instance to monitor
        """
        if component_type == "collector":
            self._collector = component
        elif component_type == "monitor":
            self._monitor = component
        elif component_type == "optimizer":
            self._optimizer = component
        elif component_type == "exporter":
            self._exporter = component
        self._component_states[component_type] = True

    async def handle_error(
        self,
        message: str,
        error: Optional[Exception] = None,
        component: Optional[str] = None,
    ):
        """Handle a metrics service error.

        Args:
            message: Error message
            error: Optional exception object
            component: Optional component name that had the error
        """
        metrics_error = MetricsError(message, error)
        self.errors.append(metrics_error)
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors :]

        if component:
            self._component_states[component] = False

        if error:
            self.log_manager.error(f"{message}: {str(error)}")
        else:
            self.log_manager.error(message)

        # Attempt recovery if component is specified
        if component:
            await self.attempt_recovery(component, metrics_error)

    async def attempt_recovery(self, component: str, error: MetricsError) -> bool:
        """Attempt to recover a failed component.

        Args:
            component: Name of the failed component
            error: The error that occurred

        Returns:
            bool: True if recovery was successful
        """
        while error.recovery_attempts < self.max_recovery_attempts:
            try:
                error.recovery_attempts += 1
                # Exponential backoff between recovery attempts
                backoff_time = self.recovery_delay * (
                    2 ** (error.recovery_attempts - 1)
                )
                await asyncio.sleep(backoff_time)

                # Implement recovery logic based on component type
                if component == "collector":
                    # For collector, verify it can collect metrics
                    if hasattr(self, "_collector") and self._collector:
                        try:
                            metrics = await self._collector.collect_metrics()
                            if metrics and isinstance(metrics, dict):
                                # Verify metrics structure
                                if all(
                                    key in metrics
                                    for key in [
                                        "throughput",
                                        "latency_ms",
                                        "error_rate",
                                        "metrics",
                                    ]
                                ):
                                    self._component_states[component] = True
                                    error.resolved = True
                                    self.log_manager.info(
                                        f"Successfully recovered {component} after {error.recovery_attempts} attempts"
                                    )
                                    return bool(True)
                                else:
                                    self.log_manager.error("Invalid metrics structure")
                                    continue
                        except Exception as e:
                            self.log_manager.error(
                                f"Metrics collection error: {str(e)}"
                            )
                            self._component_states[component] = False
                            continue

                elif component == "monitor":
                    # For monitor, verify it can check health
                    if hasattr(self, "_monitor") and self._monitor:
                        try:
                            health = await self._monitor.check_node_health()
                            if health and isinstance(health, dict):
                                # Verify health structure
                                if all(
                                    key in health
                                    for key in [
                                        "status",
                                        "metrics",
                                        "cpu_usage",
                                        "memory_usage",
                                        "disk_usage",
                                    ]
                                ):
                                    self._component_states[component] = True
                                    error.resolved = True
                                    self.log_manager.info(
                                        f"Successfully recovered {component} after {error.recovery_attempts} attempts"
                                    )
                                    return True
                                else:
                                    self.log_manager.error("Invalid health structure")
                                    continue
                        except Exception as e:
                            self.log_manager.error(f"Health check error: {str(e)}")
                            self._component_states[component] = False
                            continue

                else:
                    # For other components, verify basic functionality
                    try:
                        if component == "optimizer":
                            if hasattr(self, "_optimizer") and self._optimizer:
                                result = await self._optimizer.optimize_resources({})
                                if not result:
                                    self.log_manager.error(
                                        "Optimizer returned no result"
                                    )
                                    continue
                        elif component == "exporter":
                            if hasattr(self, "_exporter") and self._exporter:
                                result = await self._exporter.export_metrics({})
                                if not result:
                                    self.log_manager.error(
                                        "Exporter returned no result"
                                    )
                                    continue

                        self._component_states[component] = True
                        error.resolved = True
                        self.log_manager.info(
                            f"Successfully recovered {component} after {error.recovery_attempts} attempts"
                        )
                        return True
                    except Exception as e:
                        self.log_manager.error(
                            f"{component.capitalize()} error: {str(e)}"
                        )
                        self._component_states[component] = False
                        continue

            except Exception as e:
                self.log_manager.error(
                    f"Recovery attempt {error.recovery_attempts} failed for {component}: {str(e)}"
                )
                # Mark component as unhealthy after failed recovery
                self._component_states[component] = False

        self.log_manager.error(
            f"Failed to recover {component} after {self.max_recovery_attempts} attempts"
        )
        return False

    def clear_errors(self):
        """Clear all stored errors."""
        self.errors.clear()
        self._component_states.clear()

    def get_error_count(self) -> int:
        """Get the number of stored errors.

        Returns:
            Number of errors
        """
        return len(self.errors)

    def get_latest_error(self) -> Optional[MetricsError]:
        """Get the most recent error.

        Returns:
            Most recent error or None if no errors
        """
        if self.errors:
            return self.errors[-1]
        return None

    def is_component_healthy(self, component: str) -> bool:
        """Check if a component is healthy.

        Args:
            component: Name of the component to check

        Returns:
            bool: True if component is healthy
        """
        return self._component_states.get(component, True)

    def get_component_states(self) -> Dict[str, bool]:
        """Get the health states of all components.

        Returns:
            Dict mapping component names to their health states
        """
        return self._component_states.copy()
