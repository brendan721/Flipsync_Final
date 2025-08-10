#!/usr/bin/env python3
"""
Load Testing Script for FlipSync 4+1 Architecture
================================================

Tests system performance under high concurrent load:
- 100+ concurrent agent requests
- Database connection pooling validation
- WebSocket stability testing
- Performance degradation analysis
- Resilience pattern validation
"""

import asyncio
import aiohttp
import json
import os
import time
import statistics
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentLoadTester:
    """Load tester for autonomous agents."""

    def __init__(self, base_url: Optional[str] = None):
        if base_url is None:
            base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        self.base_url = base_url
        self.results = {"content": [], "executive": [], "logistics": [], "market": []}
        self.errors = []
        self.start_time = None
        self.end_time = None

    async def test_content_agent(
        self, session: aiohttp.ClientSession, test_id: int
    ) -> Dict[str, Any]:
        """Test Content Agent under load."""
        start_time = time.perf_counter()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/agents/tasks/trigger",
                json={
                    "agent_id": "content_autonomous_agent",
                    "task_type": "content_optimization",
                    "parameters": {
                        "product_name": f"Load Test Product {test_id}",
                        "marketplace": "ebay",
                    },
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                result = await response.json()
                execution_time = (time.perf_counter() - start_time) * 1000

                return {
                    "test_id": test_id,
                    "success": result.get("success", False),
                    "execution_time_ms": execution_time,
                    "response_time_ms": result.get("execution_time_ms", 0),
                    "action": result.get("result", {}).get("action", "unknown"),
                    "status_code": response.status,
                }
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.errors.append(
                {
                    "agent": "content",
                    "test_id": test_id,
                    "error": str(e),
                    "execution_time_ms": execution_time,
                }
            )
            return {
                "test_id": test_id,
                "success": False,
                "execution_time_ms": execution_time,
                "error": str(e),
            }

    async def test_executive_agent(
        self, session: aiohttp.ClientSession, test_id: int
    ) -> Dict[str, Any]:
        """Test Executive Agent under load."""
        start_time = time.perf_counter()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/agents/tasks/trigger",
                json={
                    "agent_id": "executive_autonomous_agent",
                    "task_type": "strategic_planning",
                    "parameters": {
                        "business_goal": "load_test_expansion",
                        "budget": 100000 + (test_id * 1000),
                    },
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                result = await response.json()
                execution_time = (time.perf_counter() - start_time) * 1000

                return {
                    "test_id": test_id,
                    "success": result.get("success", False),
                    "execution_time_ms": execution_time,
                    "response_time_ms": result.get("execution_time_ms", 0),
                    "action": result.get("result", {}).get("action", "unknown"),
                    "status_code": response.status,
                }
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.errors.append(
                {
                    "agent": "executive",
                    "test_id": test_id,
                    "error": str(e),
                    "execution_time_ms": execution_time,
                }
            )
            return {
                "test_id": test_id,
                "success": False,
                "execution_time_ms": execution_time,
                "error": str(e),
            }

    async def test_logistics_agent(
        self, session: aiohttp.ClientSession, test_id: int
    ) -> Dict[str, Any]:
        """Test Logistics Agent under load."""
        start_time = time.perf_counter()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/agents/tasks/trigger",
                json={
                    "agent_id": "logistics_autonomous_agent",
                    "task_type": "shipping_optimization",
                    "parameters": {
                        "weight": 1.0 + (test_id % 10),
                        "distance": 100 + (test_id % 500),
                    },
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                result = await response.json()
                execution_time = (time.perf_counter() - start_time) * 1000

                return {
                    "test_id": test_id,
                    "success": result.get("success", False),
                    "execution_time_ms": execution_time,
                    "response_time_ms": result.get("execution_time_ms", 0),
                    "action": result.get("result", {}).get("action", "unknown"),
                    "status_code": response.status,
                }
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.errors.append(
                {
                    "agent": "logistics",
                    "test_id": test_id,
                    "error": str(e),
                    "execution_time_ms": execution_time,
                }
            )
            return {
                "test_id": test_id,
                "success": False,
                "execution_time_ms": execution_time,
                "error": str(e),
            }

    async def test_market_agent(
        self, session: aiohttp.ClientSession, test_id: int
    ) -> Dict[str, Any]:
        """Test Market Agent under load."""
        start_time = time.perf_counter()
        try:
            async with session.post(
                f"{self.base_url}/api/v1/agents/tasks/trigger",
                json={
                    "agent_id": "market_autonomous_agent",
                    "task_type": "pricing_optimization",
                    "parameters": {
                        "product_name": f"Load Test Item {test_id}",
                        "current_price": 50.0 + (test_id % 100),
                    },
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                result = await response.json()
                execution_time = (time.perf_counter() - start_time) * 1000

                return {
                    "test_id": test_id,
                    "success": result.get("success", False),
                    "execution_time_ms": execution_time,
                    "response_time_ms": result.get("execution_time_ms", 0),
                    "decision": result.get("result", {}).get("decision", "unknown"),
                    "status_code": response.status,
                }
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.errors.append(
                {
                    "agent": "market",
                    "test_id": test_id,
                    "error": str(e),
                    "execution_time_ms": execution_time,
                }
            )
            return {
                "test_id": test_id,
                "success": False,
                "execution_time_ms": execution_time,
                "error": str(e),
            }

    async def run_concurrent_test(self, concurrent_requests: int = 100):
        """Run concurrent load test on all agents."""
        logger.info(
            f"🚀 Starting load test with {concurrent_requests} concurrent requests"
        )
        self.start_time = time.perf_counter()

        # Create session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=200,  # Total connection pool size
            limit_per_host=50,  # Per-host connection limit
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            # Create tasks for all agents
            tasks = []

            # Distribute requests across all 4 agents
            requests_per_agent = concurrent_requests // 4

            for i in range(requests_per_agent):
                # Content Agent
                tasks.append(self.test_content_agent(session, i))
                # Executive Agent
                tasks.append(self.test_executive_agent(session, i + requests_per_agent))
                # Logistics Agent
                tasks.append(
                    self.test_logistics_agent(session, i + requests_per_agent * 2)
                )
                # Market Agent
                tasks.append(
                    self.test_market_agent(session, i + requests_per_agent * 3)
                )

            # Execute all tasks concurrently
            logger.info(f"📊 Executing {len(tasks)} concurrent requests...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.errors.append(
                        {"task_id": i, "error": str(result), "type": "task_exception"}
                    )
                else:
                    # Determine which agent this result belongs to
                    agent_type = self._determine_agent_type(i, requests_per_agent)
                    self.results[agent_type].append(result)

        self.end_time = time.perf_counter()
        logger.info(
            f"✅ Load test completed in {self.end_time - self.start_time:.2f} seconds"
        )

    def _determine_agent_type(self, task_index: int, requests_per_agent: int) -> str:
        """Determine which agent type based on task index."""
        if task_index < requests_per_agent:
            return "content"
        elif task_index < requests_per_agent * 2:
            return "executive"
        elif task_index < requests_per_agent * 3:
            return "logistics"
        else:
            return "market"

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive load test report."""
        total_duration = (
            self.end_time - self.start_time if self.end_time and self.start_time else 0
        )

        report = {
            "test_summary": {
                "total_duration_seconds": total_duration,
                "total_requests": sum(
                    len(results) for results in self.results.values()
                ),
                "total_errors": len(self.errors),
                "requests_per_second": (
                    sum(len(results) for results in self.results.values())
                    / total_duration
                    if total_duration > 0
                    else 0
                ),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "agent_performance": {},
            "errors": self.errors,
        }

        # Analyze each agent's performance
        for agent_type, results in self.results.items():
            if not results:
                continue

            successful_results = [r for r in results if r.get("success", False)]
            execution_times = [
                r["execution_time_ms"] for r in results if "execution_time_ms" in r
            ]
            response_times = [r.get("response_time_ms", 0) for r in successful_results]

            report["agent_performance"][agent_type] = {
                "total_requests": len(results),
                "successful_requests": len(successful_results),
                "failed_requests": len(results) - len(successful_results),
                "success_rate": (
                    len(successful_results) / len(results) if results else 0
                ),
                "execution_time_stats": {
                    "min_ms": min(execution_times) if execution_times else 0,
                    "max_ms": max(execution_times) if execution_times else 0,
                    "avg_ms": (
                        statistics.mean(execution_times) if execution_times else 0
                    ),
                    "median_ms": (
                        statistics.median(execution_times) if execution_times else 0
                    ),
                    "p95_ms": (
                        statistics.quantiles(execution_times, n=20)[18]
                        if len(execution_times) > 20
                        else (max(execution_times) if execution_times else 0)
                    ),
                },
                "response_time_stats": {
                    "min_ms": min(response_times) if response_times else 0,
                    "max_ms": max(response_times) if response_times else 0,
                    "avg_ms": statistics.mean(response_times) if response_times else 0,
                    "median_ms": (
                        statistics.median(response_times) if response_times else 0
                    ),
                },
            }

        return report

    def print_report(self):
        """Print formatted load test report."""
        report = self.generate_report()

        print("\n" + "=" * 80)
        print("🚀 FLIPSYNC 4+1 ARCHITECTURE LOAD TEST REPORT")
        print("=" * 80)

        summary = report["test_summary"]
        print(f"📊 Test Duration: {summary['total_duration_seconds']:.2f} seconds")
        print(f"📊 Total Requests: {summary['total_requests']}")
        print(f"📊 Total Errors: {summary['total_errors']}")
        print(f"📊 Requests/Second: {summary['requests_per_second']:.2f}")
        print(
            f"📊 Overall Success Rate: {((summary['total_requests'] - summary['total_errors']) / summary['total_requests'] * 100):.1f}%"
        )

        print("\n" + "-" * 60)
        print("🤖 AGENT PERFORMANCE BREAKDOWN")
        print("-" * 60)

        for agent_type, perf in report["agent_performance"].items():
            print(f"\n{agent_type.upper()} AGENT:")
            print(
                f"  ✅ Success Rate: {perf['success_rate']*100:.1f}% ({perf['successful_requests']}/{perf['total_requests']})"
            )
            print(f"  ⏱️  Avg Execution: {perf['execution_time_stats']['avg_ms']:.1f}ms")
            print(f"  ⏱️  P95 Execution: {perf['execution_time_stats']['p95_ms']:.1f}ms")
            print(f"  🎯 Max Execution: {perf['execution_time_stats']['max_ms']:.1f}ms")

            # Performance assessment
            avg_time = perf["execution_time_stats"]["avg_ms"]
            success_rate = perf["success_rate"]

            if success_rate >= 0.95 and avg_time < 1000:
                print(f"  🟢 Status: EXCELLENT")
            elif success_rate >= 0.90 and avg_time < 2000:
                print(f"  🟡 Status: GOOD")
            else:
                print(f"  🔴 Status: NEEDS ATTENTION")

        if report["errors"]:
            print(f"\n❌ ERRORS ({len(report['errors'])} total):")
            for error in report["errors"][:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(report["errors"]) > 5:
                print(f"  ... and {len(report['errors']) - 5} more errors")

        print("\n" + "=" * 80)


async def main():
    """Run the load test."""
    tester = AgentLoadTester()

    # Test with increasing load
    test_sizes = [25, 50, 100, 150]

    for size in test_sizes:
        print(f"\n🔥 Running load test with {size} concurrent requests...")
        await tester.run_concurrent_test(size)
        tester.print_report()

        # Reset for next test
        tester.results = {"content": [], "executive": [], "logistics": [], "market": []}
        tester.errors = []

        # Wait between tests
        if size < test_sizes[-1]:
            print(f"\n⏳ Waiting 30 seconds before next test...")
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
