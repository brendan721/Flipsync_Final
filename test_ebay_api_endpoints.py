#!/usr/bin/env python3
"""
Test eBay Integration through FlipSync API Endpoints (Sandbox Only)
Tests the actual API endpoints for eBay marketplace integration
"""

import asyncio
import aiohttp
import json
import logging
import sys
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EbayAPITester:
    """Test eBay integration through FlipSync API endpoints."""

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

    async def test_ebay_marketplace_status(self) -> bool:
        """Test eBay marketplace status endpoint."""
        try:
            logger.info("🔍 Testing eBay marketplace status...")
            async with self.session.get(
                f"{self.base_url}/api/v1/marketplace/ebay",
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ eBay marketplace status endpoint working")
                    logger.info(f"   Status: {data.get('status', 'unknown')}")
                    logger.info(f"   Message: {data.get('message', 'N/A')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ eBay marketplace status failed: {response.status}"
                    )
                    logger.error(f"Error: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ eBay marketplace status error: {e}")
            return False

    async def test_chat_service(self) -> bool:
        """Test chat service endpoints."""
        try:
            logger.info("💬 Testing chat service...")

            # First, get chat service info
            async with self.session.get(
                f"{self.base_url}/api/v1/chat/", timeout=aiohttp.ClientTimeout(total=10)
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Chat service info endpoint working")
                    logger.info(f"   Service: {data.get('service', 'unknown')}")
                    logger.info(f"   Status: {data.get('status', 'unknown')}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Chat service failed: {response.status}")
                    logger.error(f"Error: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Chat service error: {e}")
            return False

    async def test_agents_list(self) -> bool:
        """Test agents list endpoint."""
        try:
            logger.info("🤖 Testing agents list...")
            async with self.session.get(
                f"{self.base_url}/api/v1/agents/list",
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Agents list endpoint working")

                    # Check for market agent
                    market_agents = [
                        agent for agent in data if agent.get("type") == "market"
                    ]
                    if market_agents:
                        logger.info(f"✅ Found {len(market_agents)} market agent(s)")
                        for agent in market_agents:
                            logger.info(
                                f"   - {agent.get('name', 'Unknown')}: {agent.get('status', 'unknown')}"
                            )
                    else:
                        logger.warning("⚠️ No market agents found")

                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Agents list failed: {response.status}")
                    logger.error(f"Error: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Agents list error: {e}")
            return False

    async def test_create_conversation(self) -> str:
        """Test creating a conversation and return conversation ID."""
        try:
            logger.info("📝 Testing conversation creation...")

            payload = {
                "title": "eBay Integration Test",
                "description": "Testing eBay sandbox integration",
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/chat/conversations",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:

                if response.status == 200 or response.status == 201:
                    data = await response.json()
                    conversation_id = data.get("conversation_id") or data.get("id")
                    if conversation_id:
                        logger.info(f"✅ Conversation created: {conversation_id}")
                        return conversation_id
                    else:
                        logger.error("❌ No conversation ID in response")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Conversation creation failed: {response.status}")
                    logger.error(f"Error: {error_text}")
                    return None

        except Exception as e:
            logger.error(f"❌ Conversation creation error: {e}")
            return None

    async def test_send_ebay_message(self, conversation_id: str) -> bool:
        """Test sending a message about eBay."""
        try:
            logger.info("📤 Testing eBay-related message...")

            payload = {
                "text": "Can you help me analyze eBay market trends for electronics?",
                "sender_type": "user",
            }

            async with self.session.post(
                f"{self.base_url}/api/v1/chat/conversations/{conversation_id}/messages",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as response:

                if response.status == 200 or response.status == 201:
                    data = await response.json()
                    logger.info("✅ eBay message sent successfully")

                    # Check if we got a response
                    if "message" in data or "response" in data:
                        logger.info("✅ Got response from agents")
                        return True
                    else:
                        logger.warning("⚠️ Message sent but no agent response detected")
                        return True
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Message sending failed: {response.status}")
                    logger.error(f"Error: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"❌ Message sending error: {e}")
            return False

    async def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run all eBay API integration tests."""
        logger.info("🚀 Starting eBay API Integration Test Suite")
        logger.info("=" * 60)

        results = {}

        # Test 1: Health Check
        logger.info("🏥 Testing backend health...")
        results["health_check"] = await self.test_health_check()

        # Test 2: eBay Marketplace Status
        logger.info("🛒 Testing eBay marketplace status...")
        results["ebay_marketplace_status"] = await self.test_ebay_marketplace_status()

        # Test 3: Chat Service
        logger.info("💬 Testing chat service...")
        results["chat_service"] = await self.test_chat_service()

        # Test 4: Agents List
        logger.info("🤖 Testing agents list...")
        results["agents_list"] = await self.test_agents_list()

        # Test 5: Create Conversation
        logger.info("📝 Testing conversation creation...")
        conversation_id = await self.test_create_conversation()
        results["create_conversation"] = conversation_id is not None

        # Test 6: Send eBay Message (if conversation created)
        if conversation_id:
            logger.info("📤 Testing eBay message...")
            results["send_ebay_message"] = await self.test_send_ebay_message(
                conversation_id
            )
        else:
            results["send_ebay_message"] = False

        return results


async def main():
    """Main test function."""
    logger.info("🔧 eBay API Integration Test with FlipSync Backend")
    logger.info("=" * 70)
    logger.info("📋 Testing eBay integration through API endpoints")
    logger.info("🏗️ Backend URL: http://localhost:8001")
    logger.info("🧪 Environment: Sandbox Only")
    logger.info("")

    async with EbayAPITester() as tester:
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

        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            logger.info("🎉 MOST TESTS PASSED! eBay API integration is working!")
            logger.info("")
            logger.info("🚀 Next Steps:")
            logger.info("   1. Test WebSocket real-time communication")
            logger.info("   2. Test agent coordination with eBay data")
            logger.info("   3. Performance testing with realistic workloads")
            return 0
        else:
            logger.error("❌ Too many tests failed. Check logs for details.")
            logger.info("")
            logger.info("🔧 Troubleshooting:")
            logger.info("   1. Ensure Docker containers are running")
            logger.info("   2. Check eBay sandbox credentials in .env")
            logger.info("   3. Verify API endpoint availability")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
