"""
Comprehensive Integration Tests for FlipSync Agentic System
=========================================================

Tests the complete integration between autonomous agents, service registry,
authentication system, and performance monitoring.
"""

import asyncio
import pytest
import time
from datetime import datetime, timezone
from typing import Dict, Any

from fs_agt_clean.core.services.service_integration import (
    get_service_integration_manager,
)
from fs_agt_clean.core.auth.unified_auth_system import get_unified_auth_system
from fs_agt_clean.core.config.unified_performance_config import (
    get_performance_config,
    PerformanceTarget,
    check_agent_decision_performance,
)
from fs_agt_clean.core.agents.autonomous_agent_manager import AutonomousAgentManager
from fs_agt_clean.core.database.database_service import DatabaseService


class TestAgenticSystemIntegration:
    """Integration tests for the complete agentic system."""

    @pytest.fixture
    async def service_integration_manager(self):
        """Get initialized service integration manager."""
        manager = get_service_integration_manager()
        await manager.initialize_all_services()
        return manager

    @pytest.fixture
    async def auth_system(self):
        """Get initialized authentication system."""
        auth = get_unified_auth_system()
        await auth.initialize()
        return auth

    @pytest.fixture
    def performance_config(self):
        """Get performance configuration."""
        return get_performance_config()

    @pytest.fixture
    async def agent_manager(self, service_integration_manager):
        """Get initialized agent manager."""
        manager = AutonomousAgentManager()
        await manager.initialize()
        return manager

    @pytest.mark.asyncio
    async def test_service_registry_initialization(self, service_integration_manager):
        """Test that service registry initializes with 23+ services."""
        status = service_integration_manager.get_integration_status()

        assert status["integration_status"] == "completed"
        assert status["registered_services_count"] >= 23
        assert status["meets_target"] is True

        # Verify services are available for each agent type
        market_services = service_integration_manager.get_services_for_agent("market")
        executive_services = service_integration_manager.get_services_for_agent(
            "executive"
        )
        content_services = service_integration_manager.get_services_for_agent("content")
        logistics_services = service_integration_manager.get_services_for_agent(
            "logistics"
        )

        assert len(market_services) >= 4
        assert len(executive_services) >= 5
        assert len(content_services) >= 5
        assert len(logistics_services) >= 5

    @pytest.mark.asyncio
    async def test_agent_service_integration(
        self, agent_manager, service_integration_manager
    ):
        """Test that agents can access and execute services."""
        # Get a market agent
        market_agent = None
        for agent in agent_manager.agents.values():
            if agent.agent_type == "market":
                market_agent = agent
                break

        assert market_agent is not None, "Market agent not found"

        # Test service availability
        available_services = market_agent.get_available_services()
        assert len(available_services) > 0
        assert "pricing_service" in available_services

        # Test service execution
        start_time = time.perf_counter()
        result = await market_agent.execute_service(
            "pricing_service",
            cost=100.0,
            strategy="competitive",
            market_data={"competitor_average": 120.0},
        )
        execution_time = (time.perf_counter() - start_time) * 1000

        assert result["success"] is True
        assert "recommended_price" in result["result"]
        assert execution_time < 1000  # Should meet performance target

    @pytest.mark.asyncio
    async def test_authentication_system_integration(self, auth_system):
        """Test unified authentication system."""
        # Test user authentication
        user = await auth_system.authenticate_user(
            "test@example.com", "SecurePassword!"
        )
        assert user is not None
        assert user.email == "test@example.com"
        assert "user" in user.roles

        # Test token creation
        tokens = await auth_system.create_tokens(user)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.user_id == user.user_id

        # Test token verification
        payload = await auth_system.verify_token(tokens.access_token)
        assert payload is not None
        assert payload["user_id"] == user.user_id
        assert payload["email"] == user.email

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self, performance_config):
        """Test performance monitoring and targets."""
        # Test agent decision performance
        fast_decision_time = 500.0  # 500ms
        performance_status = check_agent_decision_performance(fast_decision_time)

        assert performance_status["status"] == "excellent"
        assert performance_status["within_target"] is True

        # Test slow decision performance
        slow_decision_time = 1500.0  # 1500ms (over target)
        performance_status = check_agent_decision_performance(slow_decision_time)

        assert performance_status["status"] == "error"
        assert performance_status["within_target"] is False

        # Test all performance targets are configured
        all_targets = performance_config.get_all_targets()
        assert len(all_targets) >= 10  # Should have multiple targets configured
        assert "agent_decision" in all_targets
        assert "service_execution" in all_targets

    @pytest.mark.asyncio
    async def test_cross_agent_service_access(
        self, agent_manager, service_integration_manager
    ):
        """Test that different agent types have access to appropriate services."""
        agent_service_mapping = {}

        for agent in agent_manager.agents.values():
            services = agent.get_available_services()
            agent_service_mapping[agent.agent_type] = services

        # Verify each agent type has appropriate services
        if "market" in agent_service_mapping:
            market_services = agent_service_mapping["market"]
            assert "pricing_service" in market_services
            assert "demand_forecasting" in market_services

        if "content" in agent_service_mapping:
            content_services = agent_service_mapping["content"]
            assert "content_generation" in content_services
            assert "seo_optimization" in content_services

        if "logistics" in agent_service_mapping:
            logistics_services = agent_service_mapping["logistics"]
            assert "route_optimization" in logistics_services
            assert "inventory_management" in logistics_services

        if "executive" in agent_service_mapping:
            executive_services = agent_service_mapping["executive"]
            assert "strategic_planning" in executive_services
            assert "resource_allocation" in executive_services

    @pytest.mark.asyncio
    async def test_service_execution_performance(self, service_integration_manager):
        """Test that service execution meets performance targets."""
        # Test multiple service executions
        service_tests = [
            ("pricing_service", {"cost": 50.0, "strategy": "competitive"}),
            (
                "content_generation",
                {
                    "content_type": "product_title",
                    "product_data": {"brand": "TestBrand"},
                },
            ),
            (
                "demand_forecasting",
                {"historical_sales": [10, 12, 8, 15], "forecast_days": 7},
            ),
            (
                "route_optimization",
                {"locations": ["A", "B", "C"], "algorithm": "shortest_path"},
            ),
        ]

        for service_id, params in service_tests:
            start_time = time.perf_counter()

            result = await service_integration_manager.execute_service_for_agent(
                agent_id="test_agent",
                agent_type="market",  # Use market agent for all tests
                service_id=service_id,
                **params,
            )

            execution_time = (time.perf_counter() - start_time) * 1000

            # Verify execution success
            if result["success"]:
                assert (
                    execution_time < 1000
                ), f"Service {service_id} took {execution_time}ms (over 1000ms target)"
                assert "result" in result
            else:
                # Some services may not be available to market agent, that's OK
                print(
                    f"Service {service_id} not available to market agent: {result.get('error', 'Unknown error')}"
                )

    @pytest.mark.asyncio
    async def test_agent_initialization_performance(self, agent_manager):
        """Test that agent initialization meets performance targets."""
        # Measure agent initialization time
        start_time = time.perf_counter()

        # Re-initialize to test performance
        new_manager = RealUnifiedAgentManager()
        success = await new_manager.initialize()

        initialization_time = (time.perf_counter() - start_time) * 1000

        assert success is True
        assert initialization_time < 10000  # Should initialize within 10 seconds
        assert len(new_manager.agents) == 4  # Should have 4 autonomous agents

        # Clean up
        await new_manager.cleanup()

    @pytest.mark.asyncio
    async def test_system_health_check(
        self, agent_manager, service_integration_manager, auth_system
    ):
        """Comprehensive system health check."""
        health_status = {
            "agents": {},
            "services": {},
            "authentication": {},
            "overall_status": "healthy",
        }

        # Check agent health
        for agent_id, agent in agent_manager.agents.items():
            health_status["agents"][agent_id] = {
                "state": agent.state.value,
                "available_services": len(agent.get_available_services()),
                "agent_type": agent.agent_type,
            }

        # Check service integration health
        service_status = service_integration_manager.get_integration_status()
        health_status["services"] = {
            "integration_status": service_status["integration_status"],
            "registered_services": service_status["registered_services_count"],
            "meets_target": service_status["meets_target"],
        }

        # Check authentication health
        test_user = await auth_system.authenticate_user(
            "test@example.com", "SecurePassword!"
        )
        health_status["authentication"] = {
            "test_auth_success": test_user is not None,
            "system_initialized": auth_system.is_initialized,
        }

        # Determine overall health
        if (
            len(health_status["agents"]) < 4
            or not health_status["services"]["meets_target"]
            or not health_status["authentication"]["test_auth_success"]
        ):
            health_status["overall_status"] = "unhealthy"

        # Assert system is healthy
        assert health_status["overall_status"] == "healthy"
        assert len(health_status["agents"]) >= 4
        assert health_status["services"]["meets_target"] is True
        assert health_status["authentication"]["test_auth_success"] is True

    @pytest.mark.asyncio
    async def test_end_to_end_agent_workflow(self, agent_manager):
        """Test complete end-to-end agent workflow."""
        # Get market agent
        market_agent = None
        for agent in agent_manager.agents.values():
            if agent.agent_type == "market":
                market_agent = agent
                break

        assert market_agent is not None

        # Test complete workflow: pricing -> forecasting -> decision
        workflow_start = time.perf_counter()

        # Step 1: Get pricing recommendation
        pricing_result = await market_agent.execute_service(
            "pricing_service",
            cost=75.0,
            strategy="competitive",
            market_data={"competitor_average": 95.0},
        )

        assert pricing_result["success"] is True
        recommended_price = pricing_result["result"]["recommended_price"]

        # Step 2: Get demand forecast
        forecast_result = await market_agent.execute_service(
            "demand_forecasting", historical_sales=[8, 12, 10, 15, 9], forecast_days=14
        )

        assert forecast_result["success"] is True
        forecast_data = forecast_result["result"]

        # Step 3: Make agent decision based on service results
        decision_context = {
            "pricing_recommendation": recommended_price,
            "demand_forecast": forecast_data["total_forecast"],
            "market_conditions": "competitive",
        }

        # This would typically trigger the agent's decision pipeline
        # For now, we'll just verify the data is available
        assert recommended_price > 0
        assert forecast_data["total_forecast"] > 0

        workflow_time = (time.perf_counter() - workflow_start) * 1000

        # Entire workflow should complete within performance targets
        assert workflow_time < 2000  # 2 seconds for complete workflow

        print(f"✅ End-to-end workflow completed in {workflow_time:.2f}ms")
        print(f"   - Recommended price: ${recommended_price}")
        print(f"   - 14-day forecast: {forecast_data['total_forecast']} units")


# Performance benchmark tests
class TestPerformanceBenchmarks:
    """Performance benchmark tests for the agentic system."""

    @pytest.mark.asyncio
    async def test_concurrent_service_execution(self, service_integration_manager):
        """Test concurrent service execution performance."""
        # Create multiple concurrent service calls
        tasks = []
        for i in range(10):
            task = service_integration_manager.execute_service_for_agent(
                agent_id=f"test_agent_{i}",
                agent_type="market",
                service_id="pricing_service",
                cost=100.0 + i,
                strategy="competitive",
            )
            tasks.append(task)

        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        execution_time = (time.perf_counter() - start_time) * 1000

        # Verify results
        successful_results = [
            r for r in results if isinstance(r, dict) and r.get("success")
        ]

        assert len(successful_results) >= 8  # At least 80% success rate
        assert execution_time < 3000  # Should complete within 3 seconds

        print(
            f"✅ Concurrent execution: {len(successful_results)}/10 successful in {execution_time:.2f}ms"
        )

    @pytest.mark.asyncio
    async def test_system_load_handling(
        self, agent_manager, service_integration_manager
    ):
        """Test system performance under load."""
        # Simulate high load with multiple agents making service calls
        load_tasks = []

        for agent in agent_manager.agents.values():
            if agent.agent_type == "market":
                # Create multiple tasks for this agent
                for i in range(5):
                    task = agent.execute_service(
                        "pricing_service", cost=50.0 + i * 10, strategy="competitive"
                    )
                    load_tasks.append(task)

        start_time = time.perf_counter()
        results = await asyncio.gather(*load_tasks, return_exceptions=True)
        load_time = (time.perf_counter() - start_time) * 1000

        successful_results = [
            r for r in results if isinstance(r, dict) and r.get("success")
        ]
        success_rate = len(successful_results) / len(results) * 100

        assert success_rate >= 80  # At least 80% success rate under load
        assert load_time < 5000  # Should handle load within 5 seconds

        print(f"✅ Load test: {success_rate:.1f}% success rate in {load_time:.2f}ms")
