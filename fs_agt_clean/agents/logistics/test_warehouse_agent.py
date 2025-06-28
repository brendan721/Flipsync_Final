"""
Tests for WarehouseUnifiedAgent.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from fs_agt_clean.agents.logistics.warehouse_agent import (
    PickingTask,
    WarehouseUnifiedAgent,
    WarehouseLocation,
    WarehouseMetrics,
)


@pytest.fixture
def warehouse_agent():
    """Create a WarehouseUnifiedAgent instance for testing."""
    return WarehouseUnifiedAgent(agent_id="test_warehouse_agent")


@pytest.fixture
def sample_location():
    """Create a sample warehouse location."""
    return WarehouseLocation(
        location_id="A1-01-01",
        zone="A",
        aisle="1",
        shelf="01",
        bin="01",
        capacity=100,
        current_stock=50,
        accessibility_score=0.8,
    )


class TestWarehouseUnifiedAgent:
    """Test cases for WarehouseUnifiedAgent."""

    def test_initialization(self, warehouse_agent):
        """Test agent initialization."""
        assert warehouse_agent.agent_id == "test_warehouse_agent"
        assert isinstance(warehouse_agent.warehouse_locations, dict)
        assert isinstance(warehouse_agent.picking_tasks, dict)
        assert isinstance(warehouse_agent.metrics, WarehouseMetrics)

    @pytest.mark.asyncio
    async def test_add_warehouse_location(self, warehouse_agent):
        """Test adding a warehouse location."""
        location = await warehouse_agent.add_warehouse_location(
            location_id="A1-01-01",
            zone="A",
            aisle="1",
            shelf="01",
            bin="01",
            capacity=100,
        )

        assert location.location_id == "A1-01-01"
        assert location.zone == "A"
        assert location.capacity == 100
        assert "A1-01-01" in warehouse_agent.warehouse_locations

    @pytest.mark.asyncio
    async def test_create_picking_task(self, warehouse_agent):
        """Test creating a picking task."""
        items = [{"sku": "TEST001", "quantity": 2}, {"sku": "TEST002", "quantity": 1}]

        task = await warehouse_agent.create_picking_task(
            order_id="ORDER123", items=items, priority="high"
        )

        assert task.order_id == "ORDER123"
        assert len(task.items) == 2
        assert task.priority == "high"
        assert task.status == "pending"
        assert str(task.task_id) in warehouse_agent.picking_tasks

    @pytest.mark.asyncio
    async def test_optimize_storage_layout(self, warehouse_agent):
        """Test storage layout optimization."""
        # Add some test locations
        await warehouse_agent.add_warehouse_location(
            "A1-01-01", "A", "1", "01", "01", 100
        )
        await warehouse_agent.add_warehouse_location(
            "B1-01-01", "B", "1", "01", "01", 100
        )

        result = await warehouse_agent.optimize_storage_layout()

        assert "recommendations" in result
        assert "current_efficiency" in result
        assert "potential_improvement" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_optimize_picking_route(self, warehouse_agent):
        """Test picking route optimization."""
        # Create a picking task first
        items = [{"sku": "TEST001", "quantity": 1}]
        task = await warehouse_agent.create_picking_task("ORDER123", items)

        # Add a location for the item
        await warehouse_agent.add_warehouse_location(
            "A1-01-01", "A", "1", "01", "01", 100
        )

        result = await warehouse_agent.optimize_picking_route(str(task.task_id))

        assert "task_id" in result
        assert "optimized_route" in result
        assert "estimated_time" in result

    def test_get_status(self, warehouse_agent):
        """Test getting agent status."""
        status = warehouse_agent.get_status()

        assert status["agent_id"] == "test_warehouse_agent"
        assert status["agent_type"] == "WarehouseUnifiedAgent"
        assert "total_locations" in status
        assert "utilization_rate" in status
        assert "status" in status

    @pytest.mark.asyncio
    async def test_process_message(self, warehouse_agent):
        """Test message processing."""
        message = {
            "type": "create_picking_task",
            "order_id": "ORDER123",
            "items": [{"sku": "TEST001", "quantity": 1}],
            "priority": "normal",
        }

        await warehouse_agent.process_message(message)

        # Check that task was created
        tasks = [
            task
            for task in warehouse_agent.picking_tasks.values()
            if task.order_id == "ORDER123"
        ]
        assert len(tasks) == 1

    @pytest.mark.asyncio
    async def test_take_action(self, warehouse_agent):
        """Test taking actions."""
        action = {"type": "optimize_storage", "parameters": {}}

        # Should not raise an exception
        await warehouse_agent.take_action(action)

    def test_metrics_update(self, warehouse_agent):
        """Test metrics updating."""
        initial_total = warehouse_agent.metrics.total_locations

        # Add a location
        location = WarehouseLocation(
            location_id="TEST001",
            zone="A",
            aisle="1",
            shelf="01",
            bin="01",
            capacity=100,
            current_stock=50,
        )
        warehouse_agent.warehouse_locations["TEST001"] = location
        warehouse_agent._update_metrics()

        assert warehouse_agent.metrics.total_locations == initial_total + 1
        assert warehouse_agent.metrics.occupied_locations == 1
        assert warehouse_agent.metrics.utilization_rate == 1.0


class TestWarehouseLocation:
    """Test cases for WarehouseLocation."""

    def test_warehouse_location_creation(self, sample_location):
        """Test warehouse location creation."""
        assert sample_location.location_id == "A1-01-01"
        assert sample_location.zone == "A"
        assert sample_location.capacity == 100
        assert sample_location.current_stock == 50
        assert sample_location.accessibility_score == 0.8


class TestPickingTask:
    """Test cases for PickingTask."""

    def test_picking_task_creation(self):
        """Test picking task creation."""
        items = [{"sku": "TEST001", "quantity": 2}]
        task = PickingTask(order_id="ORDER123", items=items, priority="high")

        assert task.order_id == "ORDER123"
        assert len(task.items) == 1
        assert task.priority == "high"
        assert task.status == "pending"
        assert isinstance(task.created_at, datetime)


class TestWarehouseMetrics:
    """Test cases for WarehouseMetrics."""

    def test_warehouse_metrics_creation(self):
        """Test warehouse metrics creation."""
        metrics = WarehouseMetrics()

        assert metrics.total_locations == 0
        assert metrics.occupied_locations == 0
        assert metrics.utilization_rate == 0.0
        assert metrics.avg_picking_time == 0.0
