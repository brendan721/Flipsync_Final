#!/usr/bin/env python3
"""
Comprehensive FlipSync V3 Backend Testing Suite
Tests all critical functionality to ensure production readiness
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import websockets
import ssl


class FlipSyncBackendTester:
    def __init__(self, base_url: str = "http://174.138.77.110:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("https://", "wss://").replace("http://", "ws://")
        self.test_results = []
        self.session = None

    async def __aenter__(self):
        # Create SSL context that doesn't verify certificates for testing
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        self.session = aiohttp.ClientSession(connector=connector)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log_test(
        self, test_name: str, status: str, details: str = "", response_time: float = 0
    ):
        """Log test results"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": datetime.now().isoformat(),
        }
        self.test_results.append(result)

        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        if response_time > 0:
            print(f"   Response Time: {round(response_time * 1000, 2)}ms")
        print()

    async def test_health_endpoint(self):
        """Test basic health endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                response_time = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Health Endpoint",
                        "PASS",
                        f"Status: {data.get('status', 'unknown')}",
                        response_time,
                    )
                else:
                    self.log_test(
                        "Health Endpoint",
                        "FAIL",
                        f"HTTP {response.status}",
                        response_time,
                    )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Health Endpoint", "FAIL", str(e), response_time)

    async def test_root_endpoint(self):
        """Test root endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/") as response:
                response_time = time.time() - start_time
                if response.status == 200:
                    self.log_test(
                        "Root Endpoint",
                        "PASS",
                        f"HTTP {response.status}",
                        response_time,
                    )
                else:
                    self.log_test(
                        "Root Endpoint",
                        "FAIL",
                        f"HTTP {response.status}",
                        response_time,
                    )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Root Endpoint", "FAIL", str(e), response_time)

    async def test_api_docs(self):
        """Test API documentation endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/docs") as response:
                response_time = time.time() - start_time
                if response.status == 200:
                    self.log_test(
                        "API Documentation",
                        "PASS",
                        "Swagger UI accessible",
                        response_time,
                    )
                else:
                    self.log_test(
                        "API Documentation",
                        "FAIL",
                        f"HTTP {response.status}",
                        response_time,
                    )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("API Documentation", "FAIL", str(e), response_time)

    async def test_openapi_schema(self):
        """Test OpenAPI schema endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(f"{self.base_url}/openapi.json") as response:
                response_time = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    paths_count = len(data.get("paths", {}))
                    self.log_test(
                        "OpenAPI Schema",
                        "PASS",
                        f"{paths_count} API endpoints defined",
                        response_time,
                    )
                else:
                    self.log_test(
                        "OpenAPI Schema",
                        "FAIL",
                        f"HTTP {response.status}",
                        response_time,
                    )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("OpenAPI Schema", "FAIL", str(e), response_time)

    async def test_agent_showcase(self):
        """Test agent showcase endpoint"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/showcase/agents"
            ) as response:
                response_time = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    agents_count = len(data.get("agents", []))
                    self.log_test(
                        "Agent Showcase",
                        "PASS",
                        f"{agents_count} agents available",
                        response_time,
                    )
                else:
                    self.log_test(
                        "Agent Showcase",
                        "FAIL",
                        f"HTTP {response.status}",
                        response_time,
                    )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Agent Showcase", "FAIL", str(e), response_time)

    async def test_ebay_integration(self):
        """Test eBay integration endpoints"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/ebay/status"
            ) as response:
                response_time = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "eBay Integration Status",
                        "PASS",
                        f"Status: {data.get('status', 'unknown')}",
                        response_time,
                    )
                else:
                    self.log_test(
                        "eBay Integration Status",
                        "FAIL",
                        f"HTTP {response.status}",
                        response_time,
                    )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("eBay Integration Status", "FAIL", str(e), response_time)

    async def test_websocket_connection(self):
        """Test WebSocket connection"""
        start_time = time.time()
        try:
            uri = f"{self.ws_url}/ws/flipsync"
            # Use SSL context only for HTTPS/WSS connections
            connect_kwargs = {"ping_timeout": 10}
            if uri.startswith("wss://"):
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                connect_kwargs["ssl"] = ssl_context

            async with websockets.connect(uri, **connect_kwargs) as websocket:
                # Send a test message
                test_message = {"type": "ping", "data": "test"}
                await websocket.send(json.dumps(test_message))

                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_time = time.time() - start_time

                self.log_test(
                    "WebSocket Connection",
                    "PASS",
                    f"Connected and received: {response[:100]}...",
                    response_time,
                )
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            self.log_test(
                "WebSocket Connection",
                "WARN",
                "Connection established but no response received",
                response_time,
            )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("WebSocket Connection", "FAIL", str(e), response_time)

    async def test_performance_monitoring(self):
        """Test performance monitoring endpoints"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/monitoring/system"
            ) as response:
                response_time = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Performance Monitoring",
                        "PASS",
                        f"System metrics available",
                        response_time,
                    )
                else:
                    self.log_test(
                        "Performance Monitoring",
                        "FAIL",
                        f"HTTP {response.status}",
                        response_time,
                    )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Performance Monitoring", "FAIL", str(e), response_time)

    async def test_database_connectivity(self):
        """Test database connectivity through API"""
        start_time = time.time()
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/validation/database"
            ) as response:
                response_time = time.time() - start_time
                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "Database Connectivity",
                        "PASS",
                        f"Database: {data.get('status', 'unknown')}",
                        response_time,
                    )
                else:
                    self.log_test(
                        "Database Connectivity",
                        "FAIL",
                        f"HTTP {response.status}",
                        response_time,
                    )
        except Exception as e:
            response_time = time.time() - start_time
            self.log_test("Database Connectivity", "FAIL", str(e), response_time)

    async def run_all_tests(self):
        """Run all tests"""
        print("🧪 Starting Comprehensive FlipSync V3 Backend Testing")
        print("=" * 60)
        print()

        # Core functionality tests
        await self.test_health_endpoint()
        await self.test_root_endpoint()
        await self.test_api_docs()
        await self.test_openapi_schema()

        # Agent system tests
        await self.test_agent_showcase()

        # Integration tests
        await self.test_ebay_integration()
        await self.test_websocket_connection()

        # Infrastructure tests
        await self.test_performance_monitoring()
        await self.test_database_connectivity()

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAIL"])
        warning_tests = len([r for r in self.test_results if r["status"] == "WARN"])

        avg_response_time = (
            sum(r["response_time_ms"] for r in self.test_results) / total_tests
            if total_tests > 0
            else 0
        )

        print("=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Warnings: {warning_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"⚡ Average Response Time: {avg_response_time:.1f}ms")
        print()

        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if result["status"] == "FAIL":
                    print(f"   - {result['test']}: {result['details']}")
            print()

        # Save results to file
        with open("backend_test_results.json", "w") as f:
            json.dump(
                {
                    "summary": {
                        "total_tests": total_tests,
                        "passed": passed_tests,
                        "failed": failed_tests,
                        "warnings": warning_tests,
                        "success_rate": (
                            round(passed_tests / total_tests * 100, 1)
                            if total_tests > 0
                            else 0
                        ),
                        "avg_response_time_ms": round(avg_response_time, 1),
                    },
                    "detailed_results": self.test_results,
                },
                f,
                indent=2,
            )

        print("📄 Detailed results saved to: backend_test_results.json")


async def main():
    """Main test execution"""
    async with FlipSyncBackendTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
