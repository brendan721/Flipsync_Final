#!/usr/bin/env python3
"""
Thermal Monitoring and GPU Throttling System for FlipSync
AGENT_CONTEXT: Critical system protection for development environment
AGENT_PRIORITY: Prevent thermal damage during intensive operations
AGENT_PATTERN: Real-time monitoring with automatic throttling
"""

import asyncio
import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

# AGENT_INSTRUCTION: Configure logging for thermal monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ThermalReading:
    """Thermal sensor reading data structure"""

    timestamp: datetime
    cpu_temp: float
    gpu_temp: Optional[float]
    cpu_usage: float
    gpu_usage: Optional[float]
    throttling_active: bool


class ThermalMonitor:
    """
    AGENT_CONTEXT: Comprehensive thermal monitoring and protection system
    AGENT_CAPABILITY: CPU/GPU temperature monitoring with automatic throttling
    AGENT_SAFETY: Prevents thermal damage during development operations
    """

    def __init__(
        self,
        cpu_warning_temp: float = 80.0,
        cpu_critical_temp: float = 85.0,
        gpu_warning_temp: float = 75.0,
        gpu_critical_temp: float = 80.0,
        monitoring_interval: int = 5,
    ):
        """
        Initialize thermal monitoring system

        Args:
            cpu_warning_temp: CPU temperature warning threshold (°C)
            cpu_critical_temp: CPU temperature critical threshold (°C)
            gpu_warning_temp: GPU temperature warning threshold (°C)
            gpu_critical_temp: GPU temperature critical threshold (°C)
            monitoring_interval: Monitoring interval in seconds
        """
        self.cpu_warning_temp = cpu_warning_temp
        self.cpu_critical_temp = cpu_critical_temp
        self.gpu_warning_temp = gpu_warning_temp
        self.gpu_critical_temp = gpu_critical_temp
        self.monitoring_interval = monitoring_interval

        self.throttling_active = False
        self.readings_history: List[ThermalReading] = []
        self.max_history_size = 1000

        # AGENT_PATTERN: Initialize monitoring state
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None

        logger.info(
            f"Thermal monitor initialized - CPU: {cpu_warning_temp}°C/{cpu_critical_temp}°C, GPU: {gpu_warning_temp}°C/{gpu_critical_temp}°C"
        )

    def get_cpu_temperature(self) -> Optional[float]:
        """Get current CPU temperature"""
        try:
            # Try multiple methods to get CPU temperature
            temps = psutil.sensors_temperatures()

            # Check for common sensor names
            for sensor_name in ["coretemp", "cpu_thermal", "acpi"]:
                if sensor_name in temps:
                    for sensor in temps[sensor_name]:
                        if "Package" in sensor.label or "Core" in sensor.label:
                            return sensor.current
                    # If no specific core found, use first sensor
                    if temps[sensor_name]:
                        return temps[sensor_name][0].current

            # Fallback: use any available temperature sensor
            for sensor_group in temps.values():
                if sensor_group:
                    return sensor_group[0].current

        except Exception as e:
            logger.warning(f"Failed to get CPU temperature: {e}")

        return None

    def get_gpu_temperature(self) -> Optional[float]:
        """Get current GPU temperature using nvidia-smi"""
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=temperature.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                temp_str = result.stdout.strip()
                if temp_str and temp_str.isdigit():
                    return float(temp_str)
        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.SubprocessError,
        ) as e:
            logger.debug(f"GPU temperature unavailable: {e}")

        return None

    def get_system_usage(self) -> Tuple[float, Optional[float]]:
        """Get current CPU and GPU usage percentages"""
        cpu_usage = psutil.cpu_percent(interval=1)
        gpu_usage = None

        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                usage_str = result.stdout.strip()
                if usage_str and usage_str.isdigit():
                    gpu_usage = float(usage_str)
        except Exception:
            pass

        return cpu_usage, gpu_usage

    def apply_gpu_throttling(self, throttle_level: float = 0.7) -> bool:
        """
        Apply GPU throttling to reduce temperature

        Args:
            throttle_level: Throttling level (0.0 to 1.0, where 1.0 is no throttling)

        Returns:
            bool: True if throttling was applied successfully
        """
        try:
            # Calculate power limit based on throttle level
            # Typical GPU power limits: 150W-300W, throttle to 70% for safety
            power_limit = int(200 * throttle_level)  # Conservative 200W base

            result = subprocess.run(
                ["nvidia-smi", "-pl", str(power_limit)],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.warning(f"GPU throttling applied: {power_limit}W power limit")
                self.throttling_active = True
                return True
            else:
                logger.error(f"Failed to apply GPU throttling: {result.stderr}")

        except Exception as e:
            logger.error(f"Error applying GPU throttling: {e}")

        return False

    def remove_gpu_throttling(self) -> bool:
        """Remove GPU throttling and restore normal operation"""
        try:
            # Reset to default power limit (usually maximum)
            result = subprocess.run(
                ["nvidia-smi", "-pl", "300"],  # Conservative maximum
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logger.info("GPU throttling removed - normal operation restored")
                self.throttling_active = False
                return True
            else:
                logger.error(f"Failed to remove GPU throttling: {result.stderr}")

        except Exception as e:
            logger.error(f"Error removing GPU throttling: {e}")

        return False

    async def take_reading(self) -> ThermalReading:
        """Take a complete thermal reading"""
        cpu_temp = self.get_cpu_temperature()
        gpu_temp = self.get_gpu_temperature()
        cpu_usage, gpu_usage = self.get_system_usage()

        reading = ThermalReading(
            timestamp=datetime.now(),
            cpu_temp=cpu_temp or 0.0,
            gpu_temp=gpu_temp,
            cpu_usage=cpu_usage,
            gpu_usage=gpu_usage,
            throttling_active=self.throttling_active,
        )

        # Store reading in history
        self.readings_history.append(reading)
        if len(self.readings_history) > self.max_history_size:
            self.readings_history.pop(0)

        return reading

    async def check_thermal_status(self, reading: ThermalReading) -> None:
        """Check thermal status and apply throttling if needed"""
        # Check CPU temperature
        if reading.cpu_temp >= self.cpu_critical_temp:
            logger.critical(
                f"CRITICAL CPU TEMPERATURE: {reading.cpu_temp}°C - System protection needed!"
            )
            # In critical situations, we might need to throttle CPU as well

        elif reading.cpu_temp >= self.cpu_warning_temp:
            logger.warning(f"High CPU temperature: {reading.cpu_temp}°C")

        # Check GPU temperature and apply throttling
        if reading.gpu_temp is not None:
            if reading.gpu_temp >= self.gpu_critical_temp:
                if not self.throttling_active:
                    logger.critical(
                        f"CRITICAL GPU TEMPERATURE: {reading.gpu_temp}°C - Applying emergency throttling!"
                    )
                    self.apply_gpu_throttling(0.5)  # Aggressive throttling

            elif reading.gpu_temp >= self.gpu_warning_temp:
                if not self.throttling_active:
                    logger.warning(
                        f"High GPU temperature: {reading.gpu_temp}°C - Applying preventive throttling"
                    )
                    self.apply_gpu_throttling(0.7)  # Moderate throttling

            elif reading.gpu_temp < self.gpu_warning_temp - 5:  # 5°C hysteresis
                if self.throttling_active:
                    logger.info(
                        f"GPU temperature normalized: {reading.gpu_temp}°C - Removing throttling"
                    )
                    self.remove_gpu_throttling()

    async def monitoring_loop(self) -> None:
        """Main monitoring loop"""
        logger.info("Thermal monitoring started")

        while self.is_monitoring:
            try:
                reading = await self.take_reading()
                await self.check_thermal_status(reading)

                # Log status every 10 readings (50 seconds by default)
                if len(self.readings_history) % 10 == 0:
                    gpu_info = (
                        f", GPU: {reading.gpu_temp}°C" if reading.gpu_temp else ""
                    )
                    throttle_info = " [THROTTLED]" if reading.throttling_active else ""
                    logger.info(
                        f"Thermal status - CPU: {reading.cpu_temp}°C{gpu_info}{throttle_info}"
                    )

                await asyncio.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.monitoring_interval)

    async def start_monitoring(self) -> None:
        """Start thermal monitoring"""
        if self.is_monitoring:
            logger.warning("Thermal monitoring already active")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self.monitoring_loop())
        logger.info("Thermal monitoring task started")

    async def stop_monitoring(self) -> None:
        """Stop thermal monitoring"""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass

        # Remove any active throttling
        if self.throttling_active:
            self.remove_gpu_throttling()

        logger.info("Thermal monitoring stopped")

    def get_status_report(self) -> Dict:
        """Get current thermal status report"""
        if not self.readings_history:
            return {"status": "no_data", "message": "No thermal readings available"}

        latest = self.readings_history[-1]

        return {
            "timestamp": latest.timestamp.isoformat(),
            "cpu_temperature": latest.cpu_temp,
            "gpu_temperature": latest.gpu_temp,
            "cpu_usage": latest.cpu_usage,
            "gpu_usage": latest.gpu_usage,
            "throttling_active": latest.throttling_active,
            "status": (
                "critical"
                if (
                    latest.cpu_temp >= self.cpu_critical_temp
                    or (latest.gpu_temp and latest.gpu_temp >= self.gpu_critical_temp)
                )
                else (
                    "warning"
                    if (
                        latest.cpu_temp >= self.cpu_warning_temp
                        or (
                            latest.gpu_temp and latest.gpu_temp >= self.gpu_warning_temp
                        )
                    )
                    else "normal"
                )
            ),
            "readings_count": len(self.readings_history),
        }


# AGENT_INSTRUCTION: Global thermal monitor instance for system-wide use
thermal_monitor = ThermalMonitor()


async def initialize_thermal_monitoring():
    """Initialize and start thermal monitoring system"""
    await thermal_monitor.start_monitoring()
    logger.info("Thermal monitoring system initialized and active")


async def shutdown_thermal_monitoring():
    """Shutdown thermal monitoring system"""
    await thermal_monitor.stop_monitoring()
    logger.info("Thermal monitoring system shutdown complete")


if __name__ == "__main__":
    # AGENT_CONTEXT: Standalone thermal monitoring execution
    async def main():
        await initialize_thermal_monitoring()
        try:
            # Run for demonstration
            await asyncio.sleep(60)
        except KeyboardInterrupt:
            logger.info("Thermal monitoring interrupted by user")
        finally:
            await shutdown_thermal_monitoring()

    asyncio.run(main())
