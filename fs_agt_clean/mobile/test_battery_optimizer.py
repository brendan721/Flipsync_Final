"""Tests for the battery optimizer module."""

import pytest

from fs_agt_clean.mobile.battery_optimizer import (
    BatteryMetrics,
    BatteryOptimizer,
    PowerMode,
    PowerProfile,
)


def test_battery_optimizer_initialization():
    """Test battery optimizer initialization."""
    optimizer = BatteryOptimizer()
    assert optimizer._current_mode == PowerMode.BALANCED
    assert isinstance(optimizer.get_current_profile(), PowerProfile)


@pytest.mark.asyncio
async def test_battery_metrics_update():
    """Test updating battery metrics."""
    optimizer = BatteryOptimizer()

    # Test normal battery level
    metrics = BatteryMetrics(
        level=75.0,
        charging=False,
        temperature=25.0,
        voltage=3.7,
        current_draw=100.0,
    )
    await optimizer.update_battery_metrics(metrics)
    assert optimizer._current_mode == PowerMode.BALANCED

    # Test low battery level
    metrics = BatteryMetrics(
        level=20.0,
        charging=False,
        temperature=25.0,
        voltage=3.5,
        current_draw=100.0,
    )
    await optimizer.update_battery_metrics(metrics)
    assert optimizer._current_mode == PowerMode.POWER_SAVER

    # Test critical battery level
    metrics = BatteryMetrics(
        level=5.0,
        charging=False,
        temperature=25.0,
        voltage=3.3,
        current_draw=100.0,
    )
    await optimizer.update_battery_metrics(metrics)
    assert optimizer._current_mode == PowerMode.CRITICAL

    # Test charging
    metrics = BatteryMetrics(
        level=5.0,
        charging=True,  # Charging should switch to performance mode
        temperature=25.0,
        voltage=4.2,
        current_draw=-500.0,  # Negative current indicates charging
    )
    await optimizer.update_battery_metrics(metrics)
    assert optimizer._current_mode == PowerMode.PERFORMANCE


def test_get_current_profile():
    """Test getting the current power profile."""
    optimizer = BatteryOptimizer()
    profile = optimizer.get_current_profile()
    assert isinstance(profile, PowerProfile)
    assert profile.sync_interval == 60  # Default balanced mode


def test_customize_profile():
    """Test customizing power profiles."""
    optimizer = BatteryOptimizer()

    # Customize balanced profile
    optimizer.customize_profile(
        mode=PowerMode.BALANCED,
        sync_interval=45,
        batch_size=75,
        compression_level=5,
    )

    profile = optimizer._power_profiles[PowerMode.BALANCED]
    assert profile.sync_interval == 45
    assert profile.batch_size == 75
    assert profile.compression_level == 5

    # Test bounds checking
    optimizer.customize_profile(
        mode=PowerMode.BALANCED,
        learning_rate=2.0,  # Should be clamped to 1.0
        compression_level=15,  # Should be clamped to 9
    )

    profile = optimizer._power_profiles[PowerMode.BALANCED]
    assert profile.learning_rate == 1.0
    assert profile.compression_level == 9


@pytest.mark.asyncio
async def test_optimize_operation():
    """Test operation optimization based on power mode."""
    optimizer = BatteryOptimizer()

    # Test learning operation in balanced mode
    cost = await optimizer.optimize_operation("learning", 100.0)
    assert cost == 100.0 * optimizer.get_current_profile().learning_rate

    # Test sync operation
    cost = await optimizer.optimize_operation("sync", 100.0)
    assert cost == 100.0 * (30 / optimizer.get_current_profile().sync_interval)

    # Test processing operation
    cost = await optimizer.optimize_operation("processing", 100.0)
    assert cost == 100.0 * (optimizer.get_current_profile().batch_size / 100)


def test_should_defer_operation():
    """Test operation deferral logic."""
    optimizer = BatteryOptimizer()

    # Test in balanced mode
    optimizer._current_mode = PowerMode.BALANCED
    assert not optimizer.should_defer_operation("sync", 0.3)  # Should proceed
    assert optimizer.should_defer_operation("sync", 0.1)  # Should defer

    # Test in power saver mode
    optimizer._current_mode = PowerMode.POWER_SAVER
    assert not optimizer.should_defer_operation("sync", 0.6)  # Should proceed
    assert optimizer.should_defer_operation("sync", 0.4)  # Should defer

    # Test in critical mode
    optimizer._current_mode = PowerMode.CRITICAL
    assert not optimizer.should_defer_operation("sync", 0.9)  # Should proceed
    assert optimizer.should_defer_operation("sync", 0.7)  # Should defer
