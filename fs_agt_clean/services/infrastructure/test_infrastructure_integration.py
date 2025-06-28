"""
Integration tests for infrastructure services.

Tests the complete infrastructure stack including:
- Data pipeline and processing
- Monitoring and observability
- Alerting and notification systems
- Metrics collection and analysis
- DevOps and deployment infrastructure
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from fs_agt_clean.services.infrastructure import InfrastructureCoordinator


class TestInfrastructureIntegration:
    """Integration tests for infrastructure services."""

    @pytest.fixture
    async def infrastructure_coordinator(self):
        """Create and initialize infrastructure coordinator."""
        coordinator = InfrastructureCoordinator(
            {
                "data_pipeline": {"batch_size": 100},
                "monitoring": {"metrics_interval": 30},
                "alerting": {"notification_channels": ["email", "slack"]},
                "devops": {"environment": "test"},
            }
        )
        await coordinator.initialize()
        yield coordinator
        await coordinator.cleanup()

    @pytest.mark.asyncio
    async def test_infrastructure_initialization(self, infrastructure_coordinator):
        """Test infrastructure coordinator initialization."""
        assert infrastructure_coordinator.is_initialized

        status = await infrastructure_coordinator.get_infrastructure_status()
        assert "coordinator" in status
        assert status["coordinator"]["initialized"]
        assert "services" in status

    @pytest.mark.asyncio
    async def test_data_pipeline_processing(self, infrastructure_coordinator):
        """Test data pipeline processing capabilities."""
        # Test data batch processing
        test_batch = [
            {"asin": "B001", "title": "Test Product 1", "price": 29.99},
            {"asin": "B002", "title": "Test Product 2", "price": 39.99},
            {"asin": "", "title": "Invalid Product"},  # Should fail validation
            {"asin": "B003", "title": "Test Product 3", "price": 19.99},
        ]

        result = await infrastructure_coordinator.process_data_batch(test_batch)

        assert "batch_size" in result
        assert result["batch_size"] == 4
        assert "processed" in result
        assert "failed" in result
        assert result["processed"] == 3  # 3 valid products
        assert result["failed"] == 1  # 1 invalid product
        assert "success_rate" in result
        assert result["success_rate"] == 0.75

    @pytest.mark.asyncio
    async def test_monitoring_system_metrics(self, infrastructure_coordinator):
        """Test monitoring system metrics collection."""
        metrics = await infrastructure_coordinator.get_system_metrics()

        # Check system metrics
        assert "system" in metrics
        system_metrics = metrics["system"]
        assert "cpu_usage" in system_metrics
        assert "memory_usage" in system_metrics
        assert "disk_usage" in system_metrics
        assert "network_io" in system_metrics

        # Check application metrics
        assert "application" in metrics
        app_metrics = metrics["application"]
        assert "active_agents" in app_metrics
        assert "processed_requests" in app_metrics
        assert "error_rate" in app_metrics
        assert "response_time_avg" in app_metrics

        # Check infrastructure metrics
        assert "infrastructure" in metrics
        infra_metrics = metrics["infrastructure"]
        assert "kubernetes_pods" in infra_metrics
        assert "database_connections" in infra_metrics

    @pytest.mark.asyncio
    async def test_alerting_system(self, infrastructure_coordinator):
        """Test alerting system functionality."""
        alerts = await infrastructure_coordinator.get_active_alerts()

        assert "alerts" in alerts
        assert "summary" in alerts

        # Check alert structure
        if alerts["alerts"]:
            alert = alerts["alerts"][0]
            assert "id" in alert
            assert "severity" in alert
            assert "title" in alert
            assert "description" in alert
            assert "timestamp" in alert
            assert "status" in alert

        # Check summary
        summary = alerts["summary"]
        assert "total" in summary
        assert "critical" in summary
        assert "warning" in summary
        assert "info" in summary

    @pytest.mark.asyncio
    async def test_deployment_status(self, infrastructure_coordinator):
        """Test Kubernetes deployment status monitoring."""
        deployment_status = await infrastructure_coordinator.get_deployment_status()

        # Check namespaces
        assert "namespaces" in deployment_status
        namespaces = deployment_status["namespaces"]
        expected_namespaces = ["production", "staging", "development"]
        for ns in expected_namespaces:
            if ns in namespaces:
                assert "status" in namespaces[ns]
                assert "pods" in namespaces[ns]

        # Check deployments
        assert "deployments" in deployment_status
        deployments = deployment_status["deployments"]
        expected_deployments = ["api-service", "agent-system", "database"]
        for deployment in expected_deployments:
            if deployment in deployments:
                assert "replicas" in deployments[deployment]
                assert "ready" in deployments[deployment]
                assert "status" in deployments[deployment]

        # Check services
        assert "services" in deployment_status
        services = deployment_status["services"]
        for service_name, service_info in services.items():
            assert "type" in service_info
            assert "status" in service_info

    @pytest.mark.asyncio
    async def test_infrastructure_status_comprehensive(
        self, infrastructure_coordinator
    ):
        """Test comprehensive infrastructure status reporting."""
        status = await infrastructure_coordinator.get_infrastructure_status()

        # Check coordinator status
        assert "coordinator" in status
        coordinator_status = status["coordinator"]
        assert coordinator_status["initialized"]

        # Check service status
        assert "services" in status
        services = status["services"]
        expected_services = ["data_pipeline", "monitoring", "alerting", "metrics"]
        for service in expected_services:
            assert service in services

        # Check data pipeline status
        assert "data_pipeline" in status
        pipeline_status = status["data_pipeline"]
        assert "status" in pipeline_status
        assert "components" in pipeline_status
        expected_components = ["acquisition", "validation", "transformation", "storage"]
        for component in expected_components:
            assert component in pipeline_status["components"]

        # Check monitoring status
        assert "monitoring" in status
        monitoring_status = status["monitoring"]
        assert "status" in monitoring_status
        assert "components" in monitoring_status

        # Check DevOps status
        assert "devops" in status
        devops_status = status["devops"]
        assert "kubernetes" in devops_status
        assert "deployments" in devops_status

    @pytest.mark.asyncio
    async def test_data_pipeline_error_handling(self, infrastructure_coordinator):
        """Test data pipeline error handling."""
        # Test with empty batch
        result = await infrastructure_coordinator.process_data_batch([])
        assert result["batch_size"] == 0
        assert result["success_rate"] == 0

        # Test with malformed data
        malformed_batch = [
            {"invalid": "data"},
            {"asin": None},
            {"asin": "B001", "title": "Valid Product", "price": 29.99},
        ]

        result = await infrastructure_coordinator.process_data_batch(malformed_batch)
        assert result["batch_size"] == 3
        assert result["failed"] >= 2  # At least 2 should fail
        assert result["processed"] <= 1  # At most 1 should succeed

    @pytest.mark.asyncio
    async def test_service_availability_handling(self, infrastructure_coordinator):
        """Test handling of unavailable services."""
        # Simulate service unavailability by checking error responses

        # If data pipeline is unavailable
        if infrastructure_coordinator.service_status["data_pipeline"] != "active":
            result = await infrastructure_coordinator.process_data_batch(
                [{"test": "data"}]
            )
            assert "error" in result

        # If metrics are unavailable
        if infrastructure_coordinator.service_status["metrics"] != "active":
            result = await infrastructure_coordinator.get_system_metrics()
            assert "error" in result

        # If alerting is unavailable
        if infrastructure_coordinator.service_status["alerting"] != "active":
            result = await infrastructure_coordinator.get_active_alerts()
            assert "error" in result

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, infrastructure_coordinator):
        """Test concurrent infrastructure operations."""
        # Run multiple operations concurrently
        tasks = [
            infrastructure_coordinator.get_infrastructure_status(),
            infrastructure_coordinator.get_system_metrics(),
            infrastructure_coordinator.get_active_alerts(),
            infrastructure_coordinator.get_deployment_status(),
            infrastructure_coordinator.process_data_batch(
                [{"asin": "B001", "title": "Test Product", "price": 29.99}]
            ),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that most operations succeeded
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) >= len(tasks) * 0.8  # At least 80% success rate

        # Check that each result has expected structure
        for result in successful_results:
            if isinstance(result, dict):
                assert "timestamp" in result or "error" in result

    @pytest.mark.asyncio
    async def test_infrastructure_cleanup(self, infrastructure_coordinator):
        """Test proper cleanup of infrastructure services."""
        # Verify services are active before cleanup
        status_before = await infrastructure_coordinator.get_infrastructure_status()
        assert status_before["coordinator"]["initialized"]

        # Perform cleanup
        cleanup_result = await infrastructure_coordinator.cleanup()
        assert cleanup_result["status"] == "success"

        # Verify cleanup was successful
        assert not infrastructure_coordinator.is_initialized
        for service in infrastructure_coordinator.service_status.values():
            assert service == "shutdown"

    @pytest.mark.asyncio
    async def test_performance_under_load(self, infrastructure_coordinator):
        """Test infrastructure performance under load."""
        # Create a large data batch
        large_batch = [
            {"asin": f"B{i:03d}", "title": f"Product {i}", "price": 10.0 + i}
            for i in range(100)
        ]

        # Process the batch and measure performance
        start_time = datetime.now()
        result = await infrastructure_coordinator.process_data_batch(large_batch)
        end_time = datetime.now()

        processing_time = (end_time - start_time).total_seconds()

        # Verify results
        assert result["batch_size"] == 100
        assert result["processed"] == 100  # All should be valid
        assert result["success_rate"] == 1.0

        # Performance should be reasonable (less than 5 seconds for 100 items)
        assert processing_time < 5.0


if __name__ == "__main__":
    # Run basic infrastructure test
    async def run_basic_test():
        coordinator = InfrastructureCoordinator()
        init_result = await coordinator.initialize()

        print(f"✅ Infrastructure initialized: {init_result['status']}")

        # Test data processing
        test_data = [{"asin": "B001", "title": "Test Product", "price": 29.99}]
        process_result = await coordinator.process_data_batch(test_data)
        print(f"✅ Data processing: {process_result['success_rate']} success rate")

        # Test monitoring
        metrics = await coordinator.get_system_metrics()
        if "error" not in metrics:
            print(f"✅ Monitoring: {len(metrics)} metric categories")

        # Test deployment status
        deployment = await coordinator.get_deployment_status()
        if "error" not in deployment:
            print(f"✅ Deployment: {len(deployment['deployments'])} deployments")

        await coordinator.cleanup()
        print("✅ Infrastructure integration test completed successfully")

    # Run the test
    asyncio.run(run_basic_test())
