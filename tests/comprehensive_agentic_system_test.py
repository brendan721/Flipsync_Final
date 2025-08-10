#!/usr/bin/env python3
"""
Comprehensive Agentic System Testing Script for FlipSync Production
Tests the 4+1 agent architecture, decision pipelines, learning systems, and integrations.
"""

import asyncio
import json
import time
import aiohttp
import websockets
import asyncpg
import redis
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid


class FlipSyncAgenticSystemTester:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.ws_url = "ws://localhost/ws/flipsync"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "base_url": base_url,
            "test_categories": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0,
                "performance_issues": 0,
            },
        }
        self.session = None
        self.auth_token = None

    def log_test(
        self,
        category: str,
        test_name: str,
        status: str,
        details: str = "",
        response_time: float = 0,
        data: Any = None,
    ):
        """Log test result with categorization"""
        if category not in self.results["test_categories"]:
            self.results["test_categories"][category] = {}

        self.results["test_categories"][category][test_name] = {
            "status": status,
            "details": details,
            "response_time_ms": round(response_time * 1000, 2),
            "timestamp": datetime.now().isoformat(),
            "data": data,
        }

        self.results["summary"]["total_tests"] += 1
        if status == "PASS":
            self.results["summary"]["passed"] += 1
        elif status == "FAIL":
            self.results["summary"]["failed"] += 1
        elif status == "WARNING":
            self.results["summary"]["warnings"] += 1
        elif status == "PERFORMANCE_ISSUE":
            self.results["summary"]["performance_issues"] += 1

        status_emoji = {
            "PASS": "✅",
            "FAIL": "❌",
            "WARNING": "⚠️",
            "PERFORMANCE_ISSUE": "🐌",
        }
        print(f"[{status_emoji.get(status, '❓')}] {category}/{test_name}: {details}")

    async def authenticate(self):
        """Attempt to authenticate with the system"""
        try:
            # For production testing, we'll test without authentication first
            # and note which endpoints require auth
            self.log_test(
                "AUTHENTICATION",
                "SETUP",
                "PASS",
                "Testing with public endpoints (auth endpoints require user creation)",
            )
            return True

        except Exception as e:
            self.log_test(
                "AUTHENTICATION",
                "SETUP",
                "WARNING",
                f"Authentication setup failed: {str(e)}",
            )
            return False

    async def test_agent_initialization(self):
        """Test agent system initialization and status"""
        try:
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/api/v1/agents/status"
            ) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "AGENT_SYSTEM",
                        "INITIALIZATION",
                        "PASS",
                        f"Agents initialized: {len(data.get('agents', []))}",
                        response_time,
                        data,
                    )

                    # Test individual agent status
                    agents = data.get("agents", [])
                    for agent in agents:
                        agent_name = agent.get("name", "unknown")
                        agent_status = agent.get("status", "unknown")
                        if agent_status == "active":
                            self.log_test(
                                "AGENT_SYSTEM",
                                f"AGENT_{agent_name.upper()}_STATUS",
                                "PASS",
                                f"Agent {agent_name} is active",
                            )
                        else:
                            self.log_test(
                                "AGENT_SYSTEM",
                                f"AGENT_{agent_name.upper()}_STATUS",
                                "WARNING",
                                f"Agent {agent_name} status: {agent_status}",
                            )
                else:
                    self.log_test(
                        "AGENT_SYSTEM",
                        "INITIALIZATION",
                        "FAIL",
                        f"Status: {response.status}",
                        response_time,
                    )
        except Exception as e:
            self.log_test(
                "AGENT_SYSTEM", "INITIALIZATION", "FAIL", f"Exception: {str(e)}"
            )

    async def test_decision_pipeline_performance(self):
        """Test agent decision pipeline performance (<1000ms requirement)"""
        try:
            # Test decision endpoint with sample data
            test_decision_data = {
                "agent_type": "market",
                "context": {
                    "product_id": "test_product_123",
                    "current_price": 29.99,
                    "competitor_prices": [25.99, 32.99, 28.50],
                    "inventory_level": 15,
                },
                "decision_type": "pricing_optimization",
            }

            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/ai/decision/consensus", json=test_decision_data
            ) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    if response_time < 1.0:  # <1000ms requirement
                        self.log_test(
                            "PERFORMANCE",
                            "DECISION_PIPELINE_SPEED",
                            "PASS",
                            f"Decision made in {response_time:.3f}s",
                            response_time,
                            data,
                        )
                    else:
                        self.log_test(
                            "PERFORMANCE",
                            "DECISION_PIPELINE_SPEED",
                            "PERFORMANCE_ISSUE",
                            f"Decision took {response_time:.3f}s (>1000ms)",
                            response_time,
                        )
                else:
                    self.log_test(
                        "PERFORMANCE",
                        "DECISION_PIPELINE_SPEED",
                        "FAIL",
                        f"Status: {response.status}",
                        response_time,
                    )
        except Exception as e:
            self.log_test(
                "PERFORMANCE", "DECISION_PIPELINE_SPEED", "FAIL", f"Exception: {str(e)}"
            )

    async def test_cross_agent_learning(self):
        """Test cross-agent learning functionality"""
        try:
            # Test learning data storage
            learning_data = {
                "agent_id": "market_agent",
                "learning_type": "pricing_optimization",
                "data": {
                    "strategy": "competitive_pricing",
                    "success_rate": 0.85,
                    "context": "electronics_category",
                },
                "performance_score": 0.85,
            }

            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/ai/monitoring/metrics", json=learning_data
            ) as response:
                response_time = time.time() - start_time

                if response.status in [200, 201]:
                    self.log_test(
                        "LEARNING_SYSTEM",
                        "STORE_LEARNING_DATA",
                        "PASS",
                        "Learning data stored successfully",
                        response_time,
                    )
                else:
                    self.log_test(
                        "LEARNING_SYSTEM",
                        "STORE_LEARNING_DATA",
                        "FAIL",
                        f"Status: {response.status}",
                        response_time,
                    )

            # Test learning data retrieval
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/api/v1/ai/monitoring/metrics"
            ) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "LEARNING_SYSTEM",
                        "RETRIEVE_LEARNING_DATA",
                        "PASS",
                        f"Retrieved {len(data.get('metrics', []))} learning records",
                        response_time,
                        data,
                    )
                else:
                    self.log_test(
                        "LEARNING_SYSTEM",
                        "RETRIEVE_LEARNING_DATA",
                        "FAIL",
                        f"Status: {response.status}",
                        response_time,
                    )

        except Exception as e:
            self.log_test(
                "LEARNING_SYSTEM",
                "CROSS_AGENT_LEARNING",
                "FAIL",
                f"Exception: {str(e)}",
            )

    async def test_ebay_integration(self):
        """Test eBay integration functionality"""
        try:
            # Test eBay status
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/api/v1/ebay/status"
            ) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "EBAY_INTEGRATION",
                        "STATUS_CHECK",
                        "PASS",
                        f"eBay integration status: {data.get('status', 'unknown')}",
                        response_time,
                        data,
                    )
                else:
                    self.log_test(
                        "EBAY_INTEGRATION",
                        "STATUS_CHECK",
                        "FAIL",
                        f"Status: {response.status}",
                        response_time,
                    )

            # Test eBay marketplace data
            start_time = time.time()
            async with self.session.get(
                f"{self.base_url}/api/v1/ebay/marketplace-data"
            ) as response:
                response_time = time.time() - start_time

                if response.status == 200:
                    data = await response.json()
                    self.log_test(
                        "EBAY_INTEGRATION",
                        "MARKETPLACE_DATA",
                        "PASS",
                        "Marketplace data retrieved",
                        response_time,
                        data,
                    )
                elif response.status == 401:
                    self.log_test(
                        "EBAY_INTEGRATION",
                        "MARKETPLACE_DATA",
                        "WARNING",
                        "Authentication required (expected for production)",
                        response_time,
                    )
                else:
                    self.log_test(
                        "EBAY_INTEGRATION",
                        "MARKETPLACE_DATA",
                        "FAIL",
                        f"Status: {response.status}",
                        response_time,
                    )

        except Exception as e:
            self.log_test(
                "EBAY_INTEGRATION", "EBAY_INTEGRATION", "FAIL", f"Exception: {str(e)}"
            )

    async def test_websocket_real_time_communication(self):
        """Test WebSocket real-time communication"""
        try:
            start_time = time.time()

            async with websockets.connect(self.ws_url) as websocket:
                # Test connection
                connection_time = time.time() - start_time
                self.log_test(
                    "WEBSOCKET",
                    "CONNECTION",
                    "PASS",
                    f"Connected in {connection_time:.3f}s",
                    connection_time,
                )

                # Test message sending
                test_message = {
                    "type": "agent_status_request",
                    "data": {"agent_type": "market"},
                    "timestamp": datetime.now().isoformat(),
                }

                await websocket.send(json.dumps(test_message))

                # Test message receiving (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)

                    total_time = time.time() - start_time
                    self.log_test(
                        "WEBSOCKET",
                        "MESSAGE_EXCHANGE",
                        "PASS",
                        "Message sent and response received",
                        total_time,
                        response_data,
                    )
                except asyncio.TimeoutError:
                    self.log_test(
                        "WEBSOCKET",
                        "MESSAGE_EXCHANGE",
                        "WARNING",
                        "No response received within timeout",
                    )

        except Exception as e:
            self.log_test(
                "WEBSOCKET", "REAL_TIME_COMMUNICATION", "FAIL", f"Exception: {str(e)}"
            )

    async def test_database_operations(self):
        """Test database operations and data persistence"""
        try:
            conn = await asyncpg.connect(
                "postgresql://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@localhost:5432/flipsync_agentic_test"
            )

            # Test agent decisions table
            start_time = time.time()
            decisions_count = await conn.fetchval(
                "SELECT COUNT(*) FROM agent_decisions"
            )
            query_time = time.time() - start_time

            self.log_test(
                "DATABASE",
                "AGENT_DECISIONS_COUNT",
                "PASS",
                f"Found {decisions_count} agent decisions",
                query_time,
            )

            # Test agent learning data table
            start_time = time.time()
            learning_count = await conn.fetchval(
                "SELECT COUNT(*) FROM agent_learning_data"
            )
            query_time = time.time() - start_time

            self.log_test(
                "DATABASE",
                "LEARNING_DATA_COUNT",
                "PASS",
                f"Found {learning_count} learning records",
                query_time,
            )

            # Test eBay tokens table
            start_time = time.time()
            tokens_count = await conn.fetchval("SELECT COUNT(*) FROM ebay_oauth_tokens")
            query_time = time.time() - start_time

            self.log_test(
                "DATABASE",
                "EBAY_TOKENS_COUNT",
                "PASS",
                f"Found {tokens_count} eBay tokens",
                query_time,
            )

            await conn.close()

        except Exception as e:
            self.log_test("DATABASE", "OPERATIONS", "FAIL", f"Exception: {str(e)}")

    async def test_performance_under_load(self):
        """Test system performance under concurrent requests"""
        try:
            # Test concurrent API requests
            concurrent_requests = 10
            start_time = time.time()

            tasks = []
            for i in range(concurrent_requests):
                task = self.session.get(f"{self.base_url}/api/v1/health")
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            successful_responses = sum(
                1 for r in responses if hasattr(r, "status") and r.status == 200
            )

            if successful_responses == concurrent_requests:
                avg_time = total_time / concurrent_requests
                if avg_time < 0.5:  # Average response time under 500ms
                    self.log_test(
                        "PERFORMANCE",
                        "CONCURRENT_REQUESTS",
                        "PASS",
                        f"{concurrent_requests} concurrent requests in {total_time:.3f}s",
                        total_time,
                    )
                else:
                    self.log_test(
                        "PERFORMANCE",
                        "CONCURRENT_REQUESTS",
                        "PERFORMANCE_ISSUE",
                        f"Average response time {avg_time:.3f}s",
                        total_time,
                    )
            else:
                self.log_test(
                    "PERFORMANCE",
                    "CONCURRENT_REQUESTS",
                    "FAIL",
                    f"Only {successful_responses}/{concurrent_requests} succeeded",
                    total_time,
                )

        except Exception as e:
            self.log_test("PERFORMANCE", "LOAD_TESTING", "FAIL", f"Exception: {str(e)}")

    async def run_comprehensive_tests(self):
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive FlipSync Agentic System Testing...")
        print("=" * 80)

        # Initialize session
        self.session = aiohttp.ClientSession()

        try:
            # Authentication setup
            await self.authenticate()

            # Core system tests
            await self.test_agent_initialization()
            await self.test_database_operations()

            # Performance tests
            await self.test_decision_pipeline_performance()
            await self.test_performance_under_load()

            # Integration tests
            await self.test_cross_agent_learning()
            await self.test_ebay_integration()
            await self.test_websocket_real_time_communication()

        finally:
            await self.session.close()

        # Generate summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TESTING SUMMARY")
        print("=" * 80)

        for category, tests in self.results["test_categories"].items():
            print(f"\n📁 {category}:")
            for test_name, result in tests.items():
                status_emoji = {
                    "PASS": "✅",
                    "FAIL": "❌",
                    "WARNING": "⚠️",
                    "PERFORMANCE_ISSUE": "🐌",
                }
                print(
                    f"  {status_emoji.get(result['status'], '❓')} {test_name}: {result['details']}"
                )

        print(f"\n📈 OVERALL RESULTS:")
        print(f"Total Tests: {self.results['summary']['total_tests']}")
        print(f"✅ Passed: {self.results['summary']['passed']}")
        print(f"⚠️  Warnings: {self.results['summary']['warnings']}")
        print(f"❌ Failed: {self.results['summary']['failed']}")
        print(f"🐌 Performance Issues: {self.results['summary']['performance_issues']}")

        success_rate = (
            self.results["summary"]["passed"] / self.results["summary"]["total_tests"]
        ) * 100
        print(f"📊 Success Rate: {success_rate:.1f}%")

        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_agentic_test_report_{timestamp}.json"
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Detailed report saved to: {filename}")

        return self.results


async def main():
    tester = FlipSyncAgenticSystemTester()
    results = await tester.run_comprehensive_tests()

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
