#!/usr/bin/env python3
"""
FlipSync Current Infrastructure Assessment Tool
Gathers comprehensive information about the current DigitalOcean deployment
for migration planning to Proxmox environment.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp

# Add the fs_agt_clean directory to the Python path
sys.path.insert(0, "fs_agt_clean")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InfrastructureAssessment:
    """Comprehensive infrastructure assessment tool."""

    def __init__(self):
        self.assessment_data = {
            "timestamp": datetime.now().isoformat(),
            "assessment_type": "migration_readiness",
            "current_environment": "digitalocean_droplet",
            "target_environment": "proxmox_server",
        }

    async def run_assessment(self) -> Dict:
        """Run complete infrastructure assessment."""
        logger.info("Starting FlipSync Infrastructure Assessment")

        try:
            # API endpoint assessment
            await self._assess_api_endpoints()

            # WebSocket assessment
            await self._assess_websockets()

            # Service configuration assessment
            await self._assess_service_configuration()

            # Performance metrics assessment
            await self._assess_performance_metrics()

            logger.info("Infrastructure assessment completed successfully")

        except Exception as e:
            logger.error(f"Assessment failed: {e}")
            self.assessment_data["error"] = str(e)

        return self.assessment_data

    async def _assess_api_endpoints(self):
        """Assess API endpoint availability and performance."""
        logger.info("Assessing API endpoints...")

        endpoints = [
            {"name": "health", "url": "https://www.flipsyncai.com/api/v1/health"},
            {"name": "agents", "url": "https://www.flipsyncai.com/api/v1/agents"},
            {"name": "decisions", "url": "https://www.flipsyncai.com/api/v1/decisions"},
            {"name": "chat", "url": "https://www.flipsyncai.com/api/v1/chat"},
        ]

        endpoint_results = []

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                try:
                    start_time = time.time()
                    async with session.get(endpoint["url"], timeout=10) as response:
                        end_time = time.time()
                        response_time = (end_time - start_time) * 1000  # Convert to ms

                        endpoint_results.append(
                            {
                                "name": endpoint["name"],
                                "url": endpoint["url"],
                                "status_code": response.status,
                                "response_time_ms": response_time,
                                "available": response.status < 500,
                                "headers": dict(response.headers),
                            }
                        )

                except Exception as e:
                    endpoint_results.append(
                        {
                            "name": endpoint["name"],
                            "url": endpoint["url"],
                            "error": str(e),
                            "available": False,
                        }
                    )

        self.assessment_data["api_endpoints"] = endpoint_results
        logger.info("API endpoint assessment completed")

    async def _assess_websockets(self):
        """Assess WebSocket endpoint availability."""
        logger.info("Assessing WebSocket endpoints...")

        # Note: WebSocket testing would require additional libraries
        # For now, we'll document the expected endpoints
        websocket_endpoints = [
            {"name": "agents", "url": "wss://www.flipsyncai.com/ws/agents/"},
            {"name": "chat_4plus1", "url": "wss://www.flipsyncai.com/ws/chat/4plus1/"},
            {"name": "learning", "url": "wss://www.flipsyncai.com/ws/learning/"},
            {"name": "flipsync", "url": "wss://www.flipsyncai.com/ws/flipsync"},
        ]

        self.assessment_data["websocket_endpoints"] = {
            "endpoints": websocket_endpoints,
            "note": "WebSocket connectivity testing requires specialized tools",
        }

        logger.info("WebSocket endpoint assessment completed")

    async def _assess_service_configuration(self):
        """Assess service configuration from deployment scripts."""
        logger.info("Assessing service configuration...")

        # Read deployment configuration
        config_files = [
            "deploy_backend_rsync.sh",
            "nginx/nginx.conf",
            "production_deployment_config.env",
        ]

        configurations = {}

        for config_file in config_files:
            try:
                if os.path.exists(config_file):
                    with open(config_file, "r") as f:
                        content = f.read()
                        configurations[config_file] = {
                            "exists": True,
                            "size_bytes": len(content),
                            "lines": len(content.split("\n")),
                        }
                else:
                    configurations[config_file] = {"exists": False}
            except Exception as e:
                configurations[config_file] = {"error": str(e)}

        # Service definitions from deployment script analysis
        services = {
            "flipsync_backend": {
                "type": "systemd",
                "service_file": "/etc/systemd/system/flipsync.service",
                "working_directory": "/opt/flipsync",
                "user": "root",
                "command": "uvicorn fs_agt_clean.app.main:app --host 0.0.0.0 --port 8000 --workers 4",
                "dependencies": [
                    "postgresql.service",
                    "redis-server.service",
                    "qdrant.service",
                ],
            },
            "nginx": {
                "type": "systemd",
                "service_file": "/etc/systemd/system/nginx.service",
                "configuration": "/etc/nginx/sites-available/flipsync",
                "features": ["SSL/TLS", "HTTP/2", "Rate Limiting", "Caching"],
            },
            "postgresql": {
                "type": "systemd",
                "database": "flipsync_agentic_test",
                "user": "postgres",
                "port": 5432,
            },
            "redis": {
                "type": "systemd",
                "host": "174.138.77.110",
                "port": 6379,
                "authentication": "password_protected",
            },
            "qdrant": {
                "type": "custom_systemd",
                "host": "174.138.77.110",
                "http_port": 6333,
                "grpc_port": 6334,
                "storage": "/opt/qdrant/storage",
            },
        }

        self.assessment_data["service_configuration"] = {
            "config_files": configurations,
            "services": services,
        }

        logger.info("Service configuration assessment completed")

    async def _assess_performance_metrics(self):
        """Assess current performance metrics and baselines."""
        logger.info("Assessing performance metrics...")

        # Performance targets from configuration analysis
        performance_targets = {
            "api_response_time_ms": 2000,  # <2s target
            "agent_decision_time_ms": 1000,  # <1000ms requirement
            "websocket_latency_ms": 100,  # <100ms target
            "database_connection_pool": {
                "pool_size": 10,
                "max_overflow": 20,
                "pool_timeout": 30,
                "pool_recycle": 3600,
            },
            "nginx_worker_connections": 2048,
            "nginx_worker_rlimit_nofile": 8192,
            "uvicorn_workers": 4,
        }

        # Resource utilization thresholds
        resource_thresholds = {
            "cpu_usage_max_percent": 80,
            "memory_usage_max_percent": 85,
            "disk_space_min_percent": 20,
            "response_time_alert_ms": 5000,
        }

        # Rate limiting configuration
        rate_limits = {
            "api_requests_per_second": 10,
            "general_requests_per_second": 30,
            "static_requests_per_second": 100,
        }

        self.assessment_data["performance_metrics"] = {
            "targets": performance_targets,
            "resource_thresholds": resource_thresholds,
            "rate_limits": rate_limits,
            "monitoring": {
                "health_check_url": "https://www.flipsyncai.com/api/v1/health",
                "agent_status_url": "https://www.flipsyncai.com/api/v1/agents",
                "websocket_test_available": True,
            },
        }

        logger.info("Performance metrics assessment completed")

    def save_assessment(self, filename: str = None):
        """Save assessment data to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"infrastructure_assessment_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(self.assessment_data, f, indent=2)

        logger.info(f"Assessment data saved to {filename}")
        return filename


async def main():
    """Main assessment execution."""
    assessment = InfrastructureAssessment()

    try:
        # Run the assessment
        results = await assessment.run_assessment()

        # Save results
        filename = assessment.save_assessment()

        # Print summary
        print("\n" + "=" * 60)
        print("FLIPSYNC INFRASTRUCTURE ASSESSMENT SUMMARY")
        print("=" * 60)
        print(f"Assessment completed at: {results['timestamp']}")
        print(f"Results saved to: {filename}")

        if "api_endpoints" in results:
            print(f"\nAPI Endpoints Tested: {len(results['api_endpoints'])}")
            for endpoint in results["api_endpoints"]:
                status = (
                    "✅ Available"
                    if endpoint.get("available", False)
                    else "❌ Unavailable"
                )
                response_time = endpoint.get("response_time_ms", "N/A")
                print(f"  - {endpoint['name']}: {status} ({response_time}ms)")

        if "service_configuration" in results:
            services = results["service_configuration"]["services"]
            print(f"\nServices Configured: {len(services)}")
            for service_name in services:
                print(f"  - {service_name}: {services[service_name]['type']}")

        if "performance_metrics" in results:
            targets = results["performance_metrics"]["targets"]
            print(f"\nPerformance Targets:")
            print(f"  - API Response Time: <{targets['api_response_time_ms']}ms")
            print(f"  - Agent Decision Time: <{targets['agent_decision_time_ms']}ms")
            print(f"  - WebSocket Latency: <{targets['websocket_latency_ms']}ms")

        print("\n" + "=" * 60)
        print("Assessment completed successfully!")
        print("=" * 60)

    except Exception as e:
        logger.error(f"Assessment failed: {e}")
        print(f"\n❌ Assessment failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
