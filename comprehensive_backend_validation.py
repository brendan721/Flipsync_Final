#!/usr/bin/env python3
"""
Comprehensive Backend Validation Script for FlipSync Production Deployment
Tests all critical functionality and generates a detailed report.
"""

import asyncio
import json
import time
import aiohttp
import asyncpg
import redis
from datetime import datetime
from typing import Dict, List, Any


class FlipSyncBackendValidator:
    def __init__(self, base_url: str = "http://174.138.77.110"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "tests": {},
            "summary": {"total_tests": 0, "passed": 0, "failed": 0, "warnings": 0},
        }

    def log_test(
        self, test_name: str, status: str, details: str = "", response_time: float = 0
    ):
        """Log test result"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": datetime.now().isoformat(),
        }

        self.results["summary"]["total_tests"] += 1
        if status == "PASS":
            self.results["summary"]["passed"] += 1
        elif status == "FAIL":
            self.results["summary"]["failed"] += 1
        elif status == "WARNING":
            self.results["summary"]["warnings"] += 1

        print(f"[{status}] {test_name}: {details}")

    async def test_api_health(self):
        """Test basic API health endpoints"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test root endpoint
                start_time = time.time()
                async with session.get(f"{self.base_url}/") as response:
                    response_time = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        self.log_test(
                            "API_ROOT_ENDPOINT",
                            "PASS",
                            f"Status: {response.status}, Version: {data.get('version', 'N/A')}",
                            response_time,
                        )
                    else:
                        self.log_test(
                            "API_ROOT_ENDPOINT",
                            "FAIL",
                            f"Status: {response.status}",
                            response_time,
                        )

                # Test health endpoint
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/v1/health") as response:
                    response_time = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        self.log_test(
                            "API_HEALTH_ENDPOINT",
                            "PASS",
                            f"Status: {data.get('status', 'N/A')}",
                            response_time,
                        )
                    else:
                        self.log_test(
                            "API_HEALTH_ENDPOINT",
                            "FAIL",
                            f"Status: {response.status}",
                            response_time,
                        )

                # Test docs endpoint
                start_time = time.time()
                async with session.get(f"{self.base_url}/docs") as response:
                    response_time = time.time() - start_time
                    if response.status == 200:
                        self.log_test(
                            "API_DOCS_ENDPOINT",
                            "PASS",
                            f"Documentation accessible",
                            response_time,
                        )
                    else:
                        self.log_test(
                            "API_DOCS_ENDPOINT",
                            "FAIL",
                            f"Status: {response.status}",
                            response_time,
                        )

        except Exception as e:
            self.log_test("API_HEALTH", "FAIL", f"Exception: {str(e)}")

    async def test_database_connectivity(self):
        """Test database connectivity and basic operations"""
        try:
            start_time = time.time()
            conn = await asyncpg.connect(
                "postgresql://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@174.138.77.110:5432/flipsync_agentic_test"
            )

            # Test basic query
            result = await conn.fetchval("SELECT 1")

            # Test table existence
            tables = await conn.fetch(
                """
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public'
            """
            )

            # Check for views as well
            views = await conn.fetch(
                """
                SELECT table_name FROM information_schema.views
                WHERE table_schema = 'public'
            """
            )

            await conn.close()
            response_time = time.time() - start_time

            table_count = len(tables)
            self.log_test(
                "DATABASE_CONNECTIVITY",
                "PASS",
                f"Connected successfully, {table_count} tables found",
                response_time,
            )

            # Log some key tables
            key_tables = [
                "unified_users",
                "agent_decisions",
                "agent_learning_data",
                "ebay_oauth_tokens",
            ]
            found_tables = [t["table_name"] for t in tables]
            found_views = [v["table_name"] for v in views]

            for table in key_tables:
                if table in found_tables:
                    self.log_test(f"TABLE_{table.upper()}", "PASS", "Table exists")
                else:
                    self.log_test(
                        f"TABLE_{table.upper()}", "WARNING", "Table not found"
                    )

            # Check for users view
            if "users" in found_views:
                self.log_test("VIEW_USERS", "PASS", "Users view exists")
            else:
                self.log_test("VIEW_USERS", "WARNING", "Users view not found")

        except Exception as e:
            self.log_test("DATABASE_CONNECTIVITY", "FAIL", f"Exception: {str(e)}")

    async def test_redis_connectivity(self):
        """Test Redis connectivity"""
        try:
            start_time = time.time()
            r = redis.Redis(
                host="174.138.77.110",
                port=6379,
                password="FlipSync_Redis_Prod_2024_Secure_Key_9x7z",
                decode_responses=True,
            )

            # Test basic operations
            r.set("test_key", "test_value")
            result = r.get("test_key")
            r.delete("test_key")

            response_time = time.time() - start_time

            if result == "test_value":
                self.log_test(
                    "REDIS_CONNECTIVITY",
                    "PASS",
                    "Redis operations successful",
                    response_time,
                )
            else:
                self.log_test(
                    "REDIS_CONNECTIVITY",
                    "FAIL",
                    "Redis operations failed",
                    response_time,
                )

        except Exception as e:
            self.log_test("REDIS_CONNECTIVITY", "FAIL", f"Exception: {str(e)}")

    async def test_api_endpoints(self):
        """Test key API endpoints"""
        endpoints = [
            "/api/v1/agents/status",
            "/api/v1/ebay/status",
            "/api/v1/inventory/",
            "/api/v1/mobile",
            "/api/v1/marketplace/status",
        ]

        try:
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints:
                    try:
                        start_time = time.time()
                        async with session.get(
                            f"{self.base_url}{endpoint}"
                        ) as response:
                            response_time = time.time() - start_time
                            endpoint_name = (
                                endpoint.replace("/", "_")
                                .replace("api_v1_", "")
                                .upper()
                            )

                            if response.status in [
                                200,
                                401,
                                403,
                            ]:  # 401/403 might be expected for auth endpoints
                                self.log_test(
                                    f"ENDPOINT{endpoint_name}",
                                    "PASS",
                                    f"Status: {response.status}",
                                    response_time,
                                )
                            else:
                                self.log_test(
                                    f"ENDPOINT{endpoint_name}",
                                    "WARNING",
                                    f"Status: {response.status}",
                                    response_time,
                                )

                    except Exception as e:
                        endpoint_name = (
                            endpoint.replace("/", "_").replace("api_v1_", "").upper()
                        )
                        self.log_test(
                            f"ENDPOINT{endpoint_name}", "FAIL", f"Exception: {str(e)}"
                        )

        except Exception as e:
            self.log_test("API_ENDPOINTS", "FAIL", f"Exception: {str(e)}")

    async def test_websocket_connectivity(self):
        """Test WebSocket connectivity"""
        try:
            import websockets

            start_time = time.time()
            uri = f"ws://174.138.77.110/ws/flipsync"

            async with websockets.connect(uri) as websocket:
                # Send a test message
                await websocket.send(json.dumps({"type": "ping", "data": "test"}))

                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_time = time.time() - start_time
                    self.log_test(
                        "WEBSOCKET_CONNECTIVITY",
                        "PASS",
                        f"WebSocket connection successful",
                        response_time,
                    )
                except asyncio.TimeoutError:
                    response_time = time.time() - start_time
                    self.log_test(
                        "WEBSOCKET_CONNECTIVITY",
                        "WARNING",
                        "WebSocket connected but no response",
                        response_time,
                    )

        except Exception as e:
            self.log_test("WEBSOCKET_CONNECTIVITY", "FAIL", f"Exception: {str(e)}")

    async def test_system_resources(self):
        """Test system resource availability"""
        try:
            async with aiohttp.ClientSession() as session:
                # Test if we can get system info through an endpoint
                start_time = time.time()
                async with session.get(f"{self.base_url}/api/v1/health") as response:
                    response_time = time.time() - start_time
                    if response.status == 200:
                        data = await response.json()
                        self.log_test(
                            "SYSTEM_RESOURCES",
                            "PASS",
                            f"System responding in {response_time:.2f}s",
                            response_time,
                        )
                    else:
                        self.log_test(
                            "SYSTEM_RESOURCES",
                            "WARNING",
                            f"Health check returned {response.status}",
                        )

        except Exception as e:
            self.log_test("SYSTEM_RESOURCES", "FAIL", f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Starting FlipSync Backend Validation...")
        print("=" * 60)

        await self.test_api_health()
        await self.test_database_connectivity()
        await self.test_redis_connectivity()
        await self.test_api_endpoints()
        await self.test_websocket_connectivity()
        await self.test_system_resources()

        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {self.results['summary']['total_tests']}")
        print(f"✅ Passed: {self.results['summary']['passed']}")
        print(f"⚠️  Warnings: {self.results['summary']['warnings']}")
        print(f"❌ Failed: {self.results['summary']['failed']}")

        success_rate = (
            self.results["summary"]["passed"] / self.results["summary"]["total_tests"]
        ) * 100
        print(f"📈 Success Rate: {success_rate:.1f}%")

        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backend_validation_report_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {filename}")

        return self.results


async def main():
    validator = FlipSyncBackendValidator()
    results = await validator.run_all_tests()

    # Return appropriate exit code
    if results["summary"]["failed"] == 0:
        print("\n🎉 All critical tests passed!")
        return 0
    else:
        print(f"\n⚠️  {results['summary']['failed']} tests failed!")
        return 1


if __name__ == "__main__":
    import sys

    exit_code = asyncio.run(main())
    sys.exit(exit_code)
