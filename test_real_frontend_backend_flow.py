#!/usr/bin/env python3
"""
Real Frontend-Backend Flow Test for FlipSync.
Tests the actual chat flow that the Flutter app would use.
"""

import asyncio
import websockets
import jwt
import json
import time
import logging
import aiohttp
from typing import Dict, Any
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class RealFrontendBackendTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"

        # JWT configuration (matching Flutter app)
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"

    def generate_test_jwt_token(self, user_id: str = "real_test_user") -> str:
        """Generate a valid JWT token matching Flutter app format."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": f"real_token_{int(time.time())}",
            "roles": ["user"],
            "permissions": ["chat", "websocket"],
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def test_real_chat_message_flow(self) -> Dict[str, Any]:
        """Test the real chat message flow exactly like Flutter app."""
        logger.info("🚀 Testing Real Chat Message Flow")

        # Use 'main' conversation ID like Flutter app
        conversation_id = "main"
        user_id = "real_test_user"
        client_id = f"client_{int(time.time())}"

        jwt_token = self.generate_test_jwt_token(user_id)

        # Build WebSocket URL exactly like Flutter app
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"

        results = {
            "connection_successful": False,
            "auth_confirmed": False,
            "message_sent": False,
            "ai_response_received": False,
            "response_content": "",
            "response_time": 0.0,
            "websocket_messages": [],
            "backend_processing_detected": False,
            "error_details": None,
        }

        start_time = time.time()

        try:
            logger.info(f"🔌 Connecting to: {ws_uri}")
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                logger.info("✅ WebSocket connection established")

                # Listen for initial messages
                try:
                    while True:
                        try:
                            message = await asyncio.wait_for(
                                websocket.recv(), timeout=2.0
                            )
                            message_data = json.loads(message)
                            results["websocket_messages"].append(message_data)

                            logger.info(
                                f"📥 Received: {message_data.get('type', 'unknown')}"
                            )

                            if message_data.get("type") == "connection_established":
                                results["auth_confirmed"] = True
                                logger.info("✅ Authentication confirmed")
                                break

                        except asyncio.TimeoutError:
                            logger.info("⏰ No more initial messages")
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Error during initial message handling: {e}")

                # Send a real user message
                logger.info("📤 Sending real user message...")
                test_message = {
                    "type": "message",
                    "conversation_id": conversation_id,
                    "data": {
                        "id": f"msg_{int(time.time())}",
                        "content": "I need help with my eBay listings. What are the best strategies to increase sales?",
                        "sender": "user",
                        "timestamp": datetime.now().isoformat(),
                    },
                }

                message_start_time = time.time()
                await websocket.send(json.dumps(test_message))
                results["message_sent"] = True
                logger.info("✅ Message sent")

                # Wait for AI response with extended timeout
                logger.info("🔍 Waiting for AI response...")
                response_received = False

                try:
                    while not response_received:
                        response = await asyncio.wait_for(
                            websocket.recv(), timeout=60.0
                        )
                        response_data = json.loads(response)
                        results["websocket_messages"].append(response_data)

                        logger.info(
                            f"📥 Response type: {response_data.get('type', 'unknown')}"
                        )

                        if response_data.get("type") == "message":
                            message_end_time = time.time()
                            results["response_time"] = (
                                message_end_time - message_start_time
                            )

                            response_content = response_data.get("data", {}).get(
                                "content", ""
                            )
                            results["response_content"] = response_content

                            # Check if this is a real AI response
                            if len(response_content) > 20:  # Meaningful response
                                results["ai_response_received"] = True
                                response_received = True
                                logger.info(
                                    f"✅ AI response received in {results['response_time']:.2f}s"
                                )
                                logger.info(
                                    f"📋 Response preview: {response_content[:100]}..."
                                )
                            else:
                                logger.info(f"📋 Short response: {response_content}")

                        elif response_data.get("type") == "typing":
                            logger.info("⌨️ Typing indicator received")
                            results["backend_processing_detected"] = True

                        else:
                            logger.info(f"📋 Other message: {response_data}")

                except asyncio.TimeoutError:
                    logger.error("⏰ No AI response received within 60 seconds")
                    results["error_details"] = "AI response timeout"

        except Exception as e:
            logger.error(f"❌ Test error: {e}")
            results["error_details"] = str(e)

        results["total_time"] = time.time() - start_time
        return results

    async def test_backend_agent_availability(self) -> Dict[str, Any]:
        """Test if backend agents are available and responding."""
        logger.info("🔍 Testing Backend Agent Availability")

        results = {
            "agents_endpoint_accessible": False,
            "active_agents": [],
            "agent_count": 0,
            "executive_agent_available": False,
            "real_agent_manager_working": False,
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Test agents endpoint
                async with session.get(f"{self.api_base}/agents/status") as response:
                    if response.status == 200:
                        results["agents_endpoint_accessible"] = True
                        agent_data = await response.json()

                        if "agents" in agent_data:
                            results["active_agents"] = agent_data["agents"]
                            results["agent_count"] = len(agent_data["agents"])

                            # Check for executive agent
                            for agent in agent_data["agents"]:
                                if "executive" in agent.get("id", "").lower():
                                    results["executive_agent_available"] = True
                                    break

                        if "real_agent_manager" in agent_data:
                            results["real_agent_manager_working"] = (
                                agent_data["real_agent_manager"].get("status")
                                == "active"
                            )

                        logger.info(f"📊 Found {results['agent_count']} active agents")
                    else:
                        logger.warning(
                            f"⚠️ Agents endpoint returned status: {response.status}"
                        )

        except Exception as e:
            logger.error(f"❌ Error testing agent availability: {e}")
            results["error_details"] = str(e)

        return results

    async def run_real_tests(self) -> Dict[str, Any]:
        """Run real frontend-backend integration tests."""
        logger.info("🚀 Starting Real Frontend-Backend Integration Tests")
        logger.info("=" * 70)

        test_results = {
            "chat_flow_test": {},
            "agent_availability_test": {},
            "integration_working": False,
            "issues_found": [],
            "recommendations": [],
        }

        # Test 1: Backend Agent Availability
        logger.info("🧪 TEST 1: Backend Agent Availability")
        test_results["agent_availability_test"] = (
            await self.test_backend_agent_availability()
        )

        # Test 2: Real Chat Message Flow
        logger.info("🧪 TEST 2: Real Chat Message Flow")
        test_results["chat_flow_test"] = await self.test_real_chat_message_flow()

        # Analyze results
        agent_test = test_results["agent_availability_test"]
        chat_test = test_results["chat_flow_test"]

        # Determine if integration is working
        test_results["integration_working"] = (
            chat_test.get("connection_successful", False)
            and chat_test.get("message_sent", False)
            and chat_test.get("ai_response_received", False)
        )

        # Identify issues
        if not chat_test.get("auth_confirmed", False):
            test_results["issues_found"].append(
                "WebSocket authentication not confirmed"
            )

        if not chat_test.get("ai_response_received", False):
            test_results["issues_found"].append("AI responses not being received")

        if chat_test.get("response_time", 0) > 30:
            test_results["issues_found"].append("Response time exceeds 30 seconds")

        if not agent_test.get("executive_agent_available", False):
            test_results["issues_found"].append("Executive agent not available")

        # Generate recommendations
        if not test_results["integration_working"]:
            test_results["recommendations"].append(
                "Check WebSocket message handling in backend"
            )
            test_results["recommendations"].append(
                "Verify agent routing is working correctly"
            )

        if chat_test.get("response_time", 0) > 15:
            test_results["recommendations"].append(
                "Consider optimizing AI model performance"
            )

        return test_results


async def main():
    """Main test execution."""
    tester = RealFrontendBackendTest()

    # Wait for services to be ready
    logger.info("⏳ Waiting for services to be ready...")
    await asyncio.sleep(3)

    results = await tester.run_real_tests()

    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 REAL FRONTEND-BACKEND INTEGRATION TEST RESULTS")
    logger.info("=" * 70)

    # Agent Availability Results
    agent_results = results["agent_availability_test"]
    logger.info("📊 AGENT AVAILABILITY TEST:")
    logger.info(
        f"Agents Endpoint Accessible: {'✅' if agent_results.get('agents_endpoint_accessible') else '❌'}"
    )
    logger.info(f"Active Agent Count: {agent_results.get('agent_count', 0)}")
    logger.info(
        f"Executive Agent Available: {'✅' if agent_results.get('executive_agent_available') else '❌'}"
    )
    logger.info(
        f"Real Agent Manager Working: {'✅' if agent_results.get('real_agent_manager_working') else '❌'}"
    )

    # Chat Flow Results
    chat_results = results["chat_flow_test"]
    logger.info("📊 CHAT FLOW TEST:")
    logger.info(
        f"Connection Successful: {'✅' if chat_results.get('connection_successful') else '❌'}"
    )
    logger.info(
        f"Auth Confirmed: {'✅' if chat_results.get('auth_confirmed') else '❌'}"
    )
    logger.info(f"Message Sent: {'✅' if chat_results.get('message_sent') else '❌'}")
    logger.info(
        f"AI Response Received: {'✅' if chat_results.get('ai_response_received') else '❌'}"
    )
    logger.info(f"Response Time: {chat_results.get('response_time', 0):.2f}s")
    logger.info(
        f"Backend Processing Detected: {'✅' if chat_results.get('backend_processing_detected') else '❌'}"
    )

    # Overall Assessment
    logger.info("=" * 70)
    logger.info("📈 OVERALL ASSESSMENT:")
    logger.info(
        f"Integration Working: {'✅' if results['integration_working'] else '❌'}"
    )

    if results["issues_found"]:
        logger.error("💥 ISSUES FOUND:")
        for issue in results["issues_found"]:
            logger.error(f"   - {issue}")

    if results["recommendations"]:
        logger.info("💡 RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            logger.info(f"   - {rec}")

    # Response content preview
    if chat_results.get("response_content"):
        logger.info("=" * 70)
        logger.info("📋 RESPONSE CONTENT PREVIEW:")
        logger.info(f"'{chat_results['response_content'][:200]}...'")

    return results


if __name__ == "__main__":
    results = asyncio.run(main())
