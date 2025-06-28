#!/usr/bin/env python3
"""
Test eBay Integration with FlipSync Backend (Sandbox Only)
Tests the eBay agents working through the Docker backend API
"""

import asyncio
import aiohttp
import json
import logging
import sys
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FlipSyncBackendTester:
    """Test eBay integration through FlipSync backend API."""

    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_health_check(self) -> bool:
        """Test backend health."""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Backend health check passed: {data['status']}")
                    return True
                else:
                    logger.error(f"❌ Health check failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"❌ Health check error: {e}")
            return False

    async def test_market_agent_ebay_search(self) -> bool:
        """Test eBay search through market agent."""
        try:
            # Test market agent with eBay search
            payload = {
                "message": "Search for iPhone on eBay",
                "agent_type": "market",
                "context": {
                    "marketplace": "ebay_sandbox",
                    "search_query": "iPhone",
                    "max_results": 5,
                },
            }

            logger.info("🔍 Testing eBay search through market agent...")
            async with self.session.post(
                f"{self.base_url}/api/v1/agents/market/process",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Market agent eBay search successful")

                    # Check if we got eBay results
                    if "ebay" in str(data).lower() or "listing" in str(data).lower():
                        logger.info("✅ eBay search results detected in response")
                        return True
                    else:
                        logger.warning("⚠️ No eBay-specific results detected")
                        logger.info(f"Response preview: {str(data)[:200]}...")
                        return False

                else:
                    error_text = await response.text()
                    logger.error(f"❌ Market agent request failed: {response.status}")
                    logger.error(f"Error: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Market agent test error: {e}")
            return False

    async def test_executive_agent_ebay_analysis(self) -> bool:
        """Test eBay market analysis through executive agent."""
        try:
            payload = {
                "message": "Analyze the eBay market for electronics and provide insights",
                "agent_type": "executive",
                "context": {
                    "analysis_type": "market_research",
                    "marketplace": "ebay_sandbox",
                    "category": "electronics",
                },
            }

            logger.info("📊 Testing eBay market analysis through executive agent...")
            async with self.session.post(
                f"{self.base_url}/api/v1/agents/executive/process",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=45),
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Executive agent eBay analysis successful")

                    # Check for market analysis content
                    response_str = str(data).lower()
                    if any(
                        keyword in response_str
                        for keyword in ["market", "analysis", "ebay", "price", "trend"]
                    ):
                        logger.info("✅ Market analysis content detected")
                        return True
                    else:
                        logger.warning("⚠️ No market analysis content detected")
                        return False

                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Executive agent request failed: {response.status}"
                    )
                    logger.error(f"Error: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Executive agent test error: {e}")
            return False

    async def test_chat_with_ebay_context(self) -> bool:
        """Test chat functionality with eBay context."""
        try:
            payload = {
                "message": "What are the current trends on eBay for electronics?",
                "conversation_id": "test_ebay_integration",
                "context": {"marketplace_focus": "ebay_sandbox"},
            }

            logger.info("💬 Testing chat with eBay context...")
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/message",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Chat with eBay context successful")

                    # Check for eBay-related response
                    if "response" in data and data["response"]:
                        response_text = str(data["response"]).lower()
                        if "ebay" in response_text or "electronics" in response_text:
                            logger.info("✅ eBay-related chat response detected")
                            return True
                        else:
                            logger.warning(
                                "⚠️ No eBay-specific content in chat response"
                            )
                            return False
                    else:
                        logger.warning("⚠️ No response content in chat")
                        return False

                else:
                    error_text = await response.text()
                    logger.error(f"❌ Chat request failed: {response.status}")
                    logger.error(f"Error: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Chat test error: {e}")
            return False

    async def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run all eBay backend integration tests."""
        logger.info("🚀 Starting eBay Backend Integration Test Suite")
        logger.info("=" * 60)

        results = {}

        # Test 1: Health Check
        logger.info("🏥 Testing backend health...")
        results["health_check"] = await self.test_health_check()

        # Test 2: Market Agent eBay Search
        logger.info("🛒 Testing market agent eBay search...")
        results["market_agent_search"] = await self.test_market_agent_ebay_search()

        # Test 3: Executive Agent eBay Analysis
        logger.info("📊 Testing executive agent eBay analysis...")
        results["executive_agent_analysis"] = (
            await self.test_executive_agent_ebay_analysis()
        )

        # Test 4: Chat with eBay Context
        logger.info("💬 Testing chat with eBay context...")
        results["chat_ebay_context"] = await self.test_chat_with_ebay_context()

        return results


async def main():
    """Main test function."""
    logger.info("🔧 eBay Sandbox Integration Test with FlipSync Backend")
    logger.info("=" * 70)
    logger.info("📋 Testing eBay agents through Docker backend API")
    logger.info("🏗️ Backend URL: http://localhost:8001")
    logger.info("🧪 Environment: Sandbox Only")
    logger.info("")

    async with FlipSyncBackendTester() as tester:
        results = await tester.run_comprehensive_test()

        # Print results summary
        logger.info("")
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 40)

        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)

        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {test_name}: {status}")

        logger.info("")
        logger.info(f"📈 Overall Score: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED! eBay sandbox integration is working!")
            logger.info("")
            logger.info("🚀 Next Steps:")
            logger.info("   1. Test multi-agent coordination workflows")
            logger.info("   2. Performance testing with realistic data volumes")
            logger.info("   3. Error handling and recovery testing")
            return 0
        else:
            logger.error("❌ Some tests failed. Check logs for details.")
            logger.info("")
            logger.info("🔧 Troubleshooting:")
            logger.info("   1. Ensure Docker containers are running")
            logger.info("   2. Check eBay sandbox credentials in .env")
            logger.info("   3. Verify agent configurations")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
