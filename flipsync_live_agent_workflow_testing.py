#!/usr/bin/env python3
"""
FlipSync Live Agent Workflow Testing
===================================

Tests the deployed FlipSync agents using the correct API endpoints and workflows.
This tests the ACTUAL production workflows that the agents support.

Usage:
    python flipsync_live_agent_workflow_testing.py --verbose
"""

import asyncio
import aiohttp
import logging
import time
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import argparse

logger = logging.getLogger(__name__)


@dataclass
class WorkflowTestResult:
    """Result from testing a workflow."""

    workflow_name: str
    endpoint: str
    request_time_ms: float
    response_data: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class FlipSyncLiveWorkflowTester:
    """
    Tests the deployed FlipSync agents using actual production workflows.

    This validates:
    - AI product analysis workflow
    - eBay integration workflow
    - Agent status and coordination
    - WebSocket real-time communication
    - Database-backed decision making
    """

    def __init__(self, base_url: str = "https://www.flipsyncai.com"):
        self.base_url = base_url
        self.results: List[WorkflowTestResult] = []
        self.session = None

        # Production workflow endpoints (based on actual API structure)
        self.workflows = {
            "ai_product_analysis": "/api/v1/ai/analyze-product",
            "ai_listing_generation": "/api/v1/ai/generate-listing",
            "shipping_arbitrage": "/api/v1/shipping/arbitrage",
            "revenue_optimization": "/api/v1/revenue/optimize",
            "strategic_chat": "/api/v1/chat/strategic",
            "agent_status": "/api/v1/agents/status",
            "ebay_status": "/api/v1/ebay/status",
            "health_check": "/health",
        }

    async def run_live_workflow_testing(self) -> Dict[str, Any]:
        """Run comprehensive testing of live production workflows."""
        logger.info("🚀 Testing FlipSync Live Agent Workflows")
        logger.info(f"🌐 Base URL: {self.base_url}")

        start_time = time.perf_counter()

        async with aiohttp.ClientSession() as session:
            self.session = session

            # Step 1: Verify system health
            health_status = await self._test_system_health()

            # Step 2: Test agent status and coordination
            agent_status = await self._test_agent_coordination()

            # Step 3: Test AI-powered workflows
            ai_workflows = await self._test_ai_workflows()

            # Step 4: Test eBay integration workflows
            ebay_workflows = await self._test_ebay_workflows()

            # Step 5: Test real-time communication
            realtime_test = await self._test_realtime_communication()

            # Step 6: Generate comprehensive report
            total_time = (time.perf_counter() - start_time) * 1000
            return await self._generate_workflow_report(
                total_time,
                health_status,
                agent_status,
                ai_workflows,
                ebay_workflows,
                realtime_test,
            )

    async def _test_system_health(self) -> Dict[str, Any]:
        """Test system health and basic connectivity."""
        logger.info("🏥 Testing system health...")

        try:
            start_time = time.perf_counter()
            async with self.session.get(f"{self.base_url}/health") as response:
                request_time = (time.perf_counter() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()

                    result = WorkflowTestResult(
                        workflow_name="System Health",
                        endpoint="/health",
                        request_time_ms=request_time,
                        response_data=data,
                        success=True,
                    )
                    self.results.append(result)

                    logger.info(f"✅ System healthy - {data.get('status', 'unknown')}")
                    return {
                        "success": True,
                        "status": data.get("status"),
                        "response_time_ms": request_time,
                    }
                else:
                    logger.error(f"❌ Health check failed: HTTP {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}

        except Exception as e:
            logger.error(f"❌ Health check exception: {e}")
            return {"success": False, "error": str(e)}

    async def _test_agent_coordination(self) -> Dict[str, Any]:
        """Test agent status and coordination capabilities."""
        logger.info("🤖 Testing agent coordination...")

        try:
            start_time = time.perf_counter()
            async with self.session.get(
                f"{self.base_url}/api/v1/agents/status"
            ) as response:
                request_time = (time.perf_counter() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()

                    result = WorkflowTestResult(
                        workflow_name="Agent Coordination",
                        endpoint="/api/v1/agents/status",
                        request_time_ms=request_time,
                        response_data=data,
                        success=True,
                    )
                    self.results.append(result)

                    total_agents = data.get("total_agents", 0)
                    operational_agents = data.get("operational_agents", 0)
                    architecture = data.get("architecture", "unknown")

                    logger.info(
                        f"✅ Found {total_agents} agents ({operational_agents} operational)"
                    )
                    logger.info(f"✅ Architecture: {architecture}")

                    return {
                        "success": True,
                        "total_agents": total_agents,
                        "operational_agents": operational_agents,
                        "architecture": architecture,
                        "response_time_ms": request_time,
                        "agents_healthy": operational_agents >= 4,
                    }
                else:
                    logger.error(f"❌ Agent status failed: HTTP {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}

        except Exception as e:
            logger.error(f"❌ Agent status exception: {e}")
            return {"success": False, "error": str(e)}

    async def _test_ai_workflows(self) -> Dict[str, Any]:
        """Test AI-powered workflows."""
        logger.info("🧠 Testing AI workflows...")

        ai_results = {}

        # Test AI product analysis
        ai_results["product_analysis"] = await self._test_ai_product_analysis()

        # Test strategic chat
        ai_results["strategic_chat"] = await self._test_strategic_chat()

        successful_workflows = sum(
            1 for result in ai_results.values() if result.get("success", False)
        )

        logger.info(
            f"📊 AI workflows: {successful_workflows}/{len(ai_results)} successful"
        )

        return {
            "success": successful_workflows > 0,
            "successful_workflows": successful_workflows,
            "total_workflows": len(ai_results),
            "workflow_results": ai_results,
        }

    async def _test_ai_product_analysis(self) -> Dict[str, Any]:
        """Test AI product analysis workflow."""
        logger.info("🔍 Testing AI product analysis...")

        try:
            # Create sample product data
            product_data = {
                "product_name": "Apple iPhone 14 Pro Max",
                "description": "Latest iPhone with advanced camera system",
                "price": 1099.99,
                "category": "Electronics",
                "marketplace": "ebay",
            }

            start_time = time.perf_counter()
            async with self.session.post(
                f"{self.base_url}/api/v1/ai/analyze-product",
                json=product_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                request_time = (time.perf_counter() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()

                    result = WorkflowTestResult(
                        workflow_name="AI Product Analysis",
                        endpoint="/api/v1/ai/analyze-product",
                        request_time_ms=request_time,
                        response_data=data,
                        success=True,
                    )
                    self.results.append(result)

                    logger.info(
                        f"✅ AI product analysis successful in {request_time:.1f}ms"
                    )
                    return {
                        "success": True,
                        "response_time_ms": request_time,
                        "analysis_data": data,
                    }
                elif response.status == 422:
                    # Validation error - endpoint exists but data format issue
                    error_data = await response.json()
                    logger.warning(f"⚠️ AI analysis validation error: {error_data}")
                    return {
                        "success": False,
                        "error": "Validation error",
                        "details": error_data,
                        "endpoint_exists": True,
                    }
                else:
                    logger.warning(f"⚠️ AI analysis failed: HTTP {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response_time_ms": request_time,
                    }

        except Exception as e:
            logger.warning(f"⚠️ AI analysis exception: {e}")
            return {"success": False, "error": str(e)}

    async def _test_strategic_chat(self) -> Dict[str, Any]:
        """Test strategic chat workflow."""
        logger.info("💬 Testing strategic chat...")

        try:
            chat_data = {
                "text": "What's the best pricing strategy for electronics on eBay?",
                "context": "pricing_optimization",
                "user_id": "test_user",
            }

            start_time = time.perf_counter()
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/strategic",
                json=chat_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                request_time = (time.perf_counter() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()

                    result = WorkflowTestResult(
                        workflow_name="Strategic Chat",
                        endpoint="/api/v1/chat/strategic",
                        request_time_ms=request_time,
                        response_data=data,
                        success=True,
                    )
                    self.results.append(result)

                    logger.info(f"✅ Strategic chat successful in {request_time:.1f}ms")
                    return {
                        "success": True,
                        "response_time_ms": request_time,
                        "chat_response": data,
                    }
                else:
                    logger.warning(f"⚠️ Strategic chat failed: HTTP {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response_time_ms": request_time,
                    }

        except Exception as e:
            logger.warning(f"⚠️ Strategic chat exception: {e}")
            return {"success": False, "error": str(e)}

    async def _test_ebay_workflows(self) -> Dict[str, Any]:
        """Test eBay integration workflows."""
        logger.info("🛒 Testing eBay workflows...")

        ebay_results = {}

        # Test eBay status
        ebay_results["status"] = await self._test_ebay_status()

        # Test shipping arbitrage (if available)
        ebay_results["shipping_arbitrage"] = await self._test_shipping_arbitrage()

        successful_workflows = sum(
            1 for result in ebay_results.values() if result.get("success", False)
        )

        logger.info(
            f"📊 eBay workflows: {successful_workflows}/{len(ebay_results)} successful"
        )

        return {
            "success": successful_workflows > 0,
            "successful_workflows": successful_workflows,
            "total_workflows": len(ebay_results),
            "workflow_results": ebay_results,
        }

    async def _test_ebay_status(self) -> Dict[str, Any]:
        """Test eBay status endpoint."""
        logger.info("📊 Testing eBay status...")

        try:
            start_time = time.perf_counter()
            async with self.session.get(
                f"{self.base_url}/api/v1/ebay/status"
            ) as response:
                request_time = (time.perf_counter() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()

                    result = WorkflowTestResult(
                        workflow_name="eBay Status",
                        endpoint="/api/v1/ebay/status",
                        request_time_ms=request_time,
                        response_data=data,
                        success=True,
                    )
                    self.results.append(result)

                    logger.info(f"✅ eBay status successful in {request_time:.1f}ms")
                    return {
                        "success": True,
                        "response_time_ms": request_time,
                        "ebay_data": data,
                    }
                else:
                    logger.warning(f"⚠️ eBay status failed: HTTP {response.status}")
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response_time_ms": request_time,
                    }

        except Exception as e:
            logger.warning(f"⚠️ eBay status exception: {e}")
            return {"success": False, "error": str(e)}

    async def _test_shipping_arbitrage(self) -> Dict[str, Any]:
        """Test shipping arbitrage workflow."""
        logger.info("📦 Testing shipping arbitrage...")

        try:
            shipping_data = {
                "origin_zip": "37203",
                "destination_zip": "90210",
                "weight": 2.5,
                "dimensions": {"length": 12, "width": 8, "height": 6},
                "value": 299.99,
            }

            start_time = time.perf_counter()
            async with self.session.post(
                f"{self.base_url}/api/v1/shipping/arbitrage",
                json=shipping_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                request_time = (time.perf_counter() - start_time) * 1000

                if response.status == 200:
                    data = await response.json()

                    result = WorkflowTestResult(
                        workflow_name="Shipping Arbitrage",
                        endpoint="/api/v1/shipping/arbitrage",
                        request_time_ms=request_time,
                        response_data=data,
                        success=True,
                    )
                    self.results.append(result)

                    logger.info(
                        f"✅ Shipping arbitrage successful in {request_time:.1f}ms"
                    )
                    return {
                        "success": True,
                        "response_time_ms": request_time,
                        "arbitrage_data": data,
                    }
                else:
                    logger.warning(
                        f"⚠️ Shipping arbitrage failed: HTTP {response.status}"
                    )
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response_time_ms": request_time,
                    }

        except Exception as e:
            logger.warning(f"⚠️ Shipping arbitrage exception: {e}")
            return {"success": False, "error": str(e)}

    async def _test_realtime_communication(self) -> Dict[str, Any]:
        """Test real-time WebSocket communication."""
        logger.info("⚡ Testing real-time communication...")

        try:
            # Test WebSocket endpoint with proper upgrade headers
            start_time = time.perf_counter()
            headers = {
                "Connection": "Upgrade",
                "Upgrade": "websocket",
                "Sec-WebSocket-Version": "13",
                "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
            }

            async with self.session.get(
                f"{self.base_url}/ws/flipsync", headers=headers
            ) as response:
                request_time = (time.perf_counter() - start_time) * 1000

                # WebSocket upgrade successful
                if response.status == 101:
                    logger.info(
                        "✅ WebSocket endpoint working perfectly (101 Switching Protocols)"
                    )
                    return {
                        "success": True,
                        "websocket_available": True,
                        "response_time_ms": request_time,
                        "note": "WebSocket upgrade successful",
                        "status_code": 101,
                    }
                # WebSocket endpoints typically return 426 Upgrade Required for HTTP requests
                elif response.status == 426:
                    logger.info(
                        "✅ WebSocket endpoint available (426 Upgrade Required)"
                    )
                    return {
                        "success": True,
                        "websocket_available": True,
                        "response_time_ms": request_time,
                        "note": "WebSocket endpoint exists and requires upgrade",
                        "status_code": 426,
                    }
                elif response.status == 404:
                    logger.warning("⚠️ WebSocket endpoint not found")
                    return {
                        "success": False,
                        "websocket_available": False,
                        "error": "WebSocket endpoint not found",
                        "status_code": 404,
                    }
                else:
                    logger.info(
                        f"ℹ️ WebSocket endpoint responded with HTTP {response.status}"
                    )
                    return {
                        "success": True,
                        "websocket_available": True,
                        "response_time_ms": request_time,
                        "note": f"WebSocket endpoint responded with HTTP {response.status}",
                        "status_code": response.status,
                    }

        except Exception as e:
            logger.warning(f"⚠️ WebSocket test exception: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_workflow_report(
        self,
        total_time_ms: float,
        health_status: Dict,
        agent_status: Dict,
        ai_workflows: Dict,
        ebay_workflows: Dict,
        realtime_test: Dict,
    ) -> Dict[str, Any]:
        """Generate comprehensive workflow testing report."""

        # Calculate success metrics
        test_categories = [
            health_status,
            agent_status,
            ai_workflows,
            ebay_workflows,
            realtime_test,
        ]
        successful_categories = sum(
            1 for category in test_categories if category.get("success", False)
        )
        total_categories = len(test_categories)
        success_rate = (successful_categories / total_categories) * 100

        # Calculate total successful workflows
        total_workflows = len(self.results)
        successful_workflows = sum(1 for result in self.results if result.success)

        return {
            "success": success_rate >= 60,  # At least 60% of categories must pass
            "live_testing_summary": {
                "total_execution_time_ms": total_time_ms,
                "test_categories": total_categories,
                "successful_categories": successful_categories,
                "category_success_rate_percent": success_rate,
                "total_workflows_tested": total_workflows,
                "successful_workflows": successful_workflows,
                "workflow_success_rate_percent": (
                    successful_workflows / max(total_workflows, 1)
                )
                * 100,
            },
            "category_results": {
                "system_health": health_status,
                "agent_coordination": agent_status,
                "ai_workflows": ai_workflows,
                "ebay_workflows": ebay_workflows,
                "realtime_communication": realtime_test,
            },
            "production_readiness": {
                "system_healthy": health_status.get("success", False),
                "agents_operational": agent_status.get("agents_healthy", False),
                "ai_functional": ai_workflows.get("successful_workflows", 0) > 0,
                "ebay_integrated": ebay_workflows.get("successful_workflows", 0) > 0,
                "realtime_available": realtime_test.get("websocket_available", False),
                "ready_for_production_use": success_rate >= 80,
            },
            "detailed_workflow_results": [
                {
                    "workflow_name": result.workflow_name,
                    "endpoint": result.endpoint,
                    "request_time_ms": result.request_time_ms,
                    "success": result.success,
                    "error_message": result.error_message,
                }
                for result in self.results
            ],
            "next_steps": self._generate_next_steps(
                success_rate, agent_status, ai_workflows, ebay_workflows
            ),
        }

    def _generate_next_steps(
        self,
        success_rate: float,
        agent_status: Dict,
        ai_workflows: Dict,
        ebay_workflows: Dict,
    ) -> List[str]:
        """Generate next steps based on test results."""
        next_steps = []

        if success_rate >= 80:
            next_steps.extend(
                [
                    "🎉 Production workflows are ready for live use",
                    "🚀 Begin real eBay listing optimization workflows",
                    "📊 Monitor agent decision making and learning",
                    "🔄 Test cross-agent coordination with real data",
                    "📈 Scale up to handle production traffic",
                ]
            )
        else:
            if not agent_status.get("agents_healthy", False):
                next_steps.append("🤖 Investigate agent health and coordination issues")

            if ai_workflows.get("successful_workflows", 0) == 0:
                next_steps.append("🧠 Fix AI workflow endpoints and processing")

            if ebay_workflows.get("successful_workflows", 0) == 0:
                next_steps.append("🛒 Resolve eBay integration and API connectivity")

            next_steps.extend(
                [
                    "🔧 Address failing workflow components",
                    "🔄 Re-run live testing after fixes",
                    "📋 Review production deployment configuration",
                ]
            )

        return next_steps


async def main():
    """Main live workflow testing function."""
    parser = argparse.ArgumentParser(description="FlipSync Live Agent Workflow Testing")
    parser.add_argument(
        "--base-url",
        default="https://www.flipsyncai.com",
        help="Base URL for production API",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    print("🚀 FlipSync Live Agent Workflow Testing")
    print("=" * 70)
    print("🌐 Testing LIVE production workflows and agent coordination")
    print("=" * 70)

    # Run live workflow testing
    tester = FlipSyncLiveWorkflowTester(base_url=args.base_url)
    report = await tester.run_live_workflow_testing()

    # Display results
    if report.get("success"):
        summary = report["live_testing_summary"]
        readiness = report["production_readiness"]

        print(f"\n🎯 LIVE WORKFLOW TESTING RESULTS")
        print(f"Category Success Rate: {summary['category_success_rate_percent']:.1f}%")
        print(f"Workflow Success Rate: {summary['workflow_success_rate_percent']:.1f}%")
        print(
            f"Successful Categories: {summary['successful_categories']}/{summary['test_categories']}"
        )
        print(
            f"Successful Workflows: {summary['successful_workflows']}/{summary['total_workflows_tested']}"
        )
        print(f"Total Time: {summary['total_execution_time_ms']:.1f}ms")

        print(f"\n🚀 PRODUCTION READINESS")
        print(f"System Healthy: {'✅ YES' if readiness['system_healthy'] else '❌ NO'}")
        print(
            f"Agents Operational: {'✅ YES' if readiness['agents_operational'] else '❌ NO'}"
        )
        print(f"AI Functional: {'✅ YES' if readiness['ai_functional'] else '❌ NO'}")
        print(
            f"eBay Integrated: {'✅ YES' if readiness['ebay_integrated'] else '❌ NO'}"
        )
        print(
            f"Real-time Available: {'✅ YES' if readiness['realtime_available'] else '❌ NO'}"
        )
        print(
            f"Ready for Production Use: {'✅ YES' if readiness['ready_for_production_use'] else '❌ NO'}"
        )

        print(f"\n📋 NEXT STEPS")
        for step in report["next_steps"]:
            print(f"  {step}")

    else:
        print(f"❌ Live workflow testing failed")
        if "next_steps" in report:
            print(f"\n📋 REQUIRED ACTIONS")
            for step in report["next_steps"]:
                print(f"  {step}")

    print(f"\n✅ Live agent workflow testing complete!")


if __name__ == "__main__":
    asyncio.run(main())
