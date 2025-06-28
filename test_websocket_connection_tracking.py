#!/usr/bin/env python3
"""
WebSocket Connection Tracking Investigation for FlipSync.
Tests WebSocket connection establishment and recipient tracking to resolve "0 recipients" issue.
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


class WebSocketConnectionTrackingTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.ws_url = "ws://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"

        # JWT configuration
        self.jwt_secret = "development-jwt-secret-not-for-production-use"
        self.jwt_algorithm = "HS256"

    def generate_test_jwt_token(self, user_id: str = "connection_test_user") -> str:
        """Generate a valid JWT token for testing."""
        now = datetime.utcnow()
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=1),
            "jti": f"connection_token_{int(time.time())}",
            "roles": ["user"],
            "permissions": ["chat", "websocket"],
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    async def test_websocket_connection_establishment(self) -> Dict[str, Any]:
        """Test WebSocket connection establishment and tracking."""
        logger.info("🔍 Testing WebSocket Connection Establishment")

        conversation_id = f"connection_test_{int(time.time())}"
        user_id = "connection_test_user"
        client_id = f"client_{int(time.time())}"

        jwt_token = self.generate_test_jwt_token(user_id)
        ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"

        results = {
            "connection_successful": False,
            "welcome_message_received": False,
            "connection_tracked": False,
            "conversation_registered": False,
            "error_details": None,
        }

        try:
            async with websockets.connect(ws_uri) as websocket:
                results["connection_successful"] = True
                logger.info("✅ WebSocket connection established")

                # Wait for welcome message
                try:
                    welcome_response = await asyncio.wait_for(
                        websocket.recv(), timeout=5.0
                    )
                    welcome_data = json.loads(welcome_response)

                    if welcome_data.get("type") == "connection_established":
                        results["welcome_message_received"] = True
                        logger.info("✅ Welcome message received")
                        logger.info(f"📋 Welcome data: {welcome_data}")

                except asyncio.TimeoutError:
                    logger.warning("⏰ No welcome message received within 5 seconds")

                # Test connection tracking via API
                await asyncio.sleep(1)  # Give time for connection to be registered
                results["connection_tracked"] = await self._check_connection_tracking(
                    conversation_id
                )

                # Test conversation registration
                results["conversation_registered"] = (
                    await self._check_conversation_registration(conversation_id)
                )

        except Exception as e:
            logger.error(f"❌ WebSocket connection error: {e}")
            results["error_details"] = str(e)

        return results

    async def _check_connection_tracking(self, conversation_id: str) -> bool:
        """Check if the WebSocket connection is being tracked."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check WebSocket manager status using correct endpoint
                async with session.get(f"{self.api_base}/ws/stats") as response:
                    if response.status == 200:
                        status_data = await response.json()
                        active_connections = status_data.get("active_connections", 0)
                        total_connections = status_data.get("total_connections", 0)
                        logger.info(
                            f"📊 WebSocket stats: {active_connections} active, {total_connections} total"
                        )
                        return active_connections > 0
                    else:
                        logger.warning(
                            f"⚠️ WebSocket status endpoint returned {response.status}"
                        )
                        return False
        except Exception as e:
            logger.error(f"❌ Error checking connection tracking: {e}")
            return False

    async def _check_conversation_registration(self, conversation_id: str) -> bool:
        """Check if the conversation is registered for message broadcasting."""
        try:
            async with aiohttp.ClientSession() as session:
                # Try to broadcast a test message to the conversation
                test_message = {
                    "message": "Connection tracking test",
                    "message_type": "system_notification",
                }

                async with session.post(
                    f"{self.api_base}/ws/conversations/{conversation_id}/broadcast?message=Connection tracking test&message_type=system_notification"
                ) as response:
                    if response.status == 200:
                        broadcast_data = await response.json()
                        recipients = broadcast_data.get("recipients", 0)
                        logger.info(f"📊 Broadcast test recipients: {recipients}")
                        return recipients > 0
                    else:
                        logger.warning(f"⚠️ Broadcast test returned {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Error checking conversation registration: {e}")
            return False

    async def test_multiple_connections(self) -> Dict[str, Any]:
        """Test multiple WebSocket connections to the same conversation."""
        logger.info("🔍 Testing Multiple WebSocket Connections")

        conversation_id = f"multi_test_{int(time.time())}"
        user_id = "multi_test_user"

        results = {
            "connections_established": 0,
            "total_recipients": 0,
            "connection_details": [],
            "broadcast_successful": False,
        }

        connections = []

        try:
            # Establish multiple connections
            for i in range(3):
                client_id = f"client_{int(time.time())}_{i}"
                jwt_token = self.generate_test_jwt_token(f"{user_id}_{i}")
                ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}_{i}&client_id={client_id}"

                try:
                    websocket = await websockets.connect(ws_uri)
                    connections.append(websocket)
                    results["connections_established"] += 1

                    # Wait for welcome message
                    welcome_response = await asyncio.wait_for(
                        websocket.recv(), timeout=3.0
                    )
                    welcome_data = json.loads(welcome_response)

                    results["connection_details"].append(
                        {
                            "client_id": client_id,
                            "user_id": f"{user_id}_{i}",
                            "welcome_received": welcome_data.get("type")
                            == "connection_established",
                        }
                    )

                    logger.info(f"✅ Connection {i+1} established: {client_id}")

                except Exception as e:
                    logger.error(f"❌ Failed to establish connection {i+1}: {e}")

            # Wait for all connections to be registered
            await asyncio.sleep(2)

            # Test broadcasting to the conversation
            if results["connections_established"] > 0:
                async with aiohttp.ClientSession() as session:
                    test_message = {
                        "message": "Multi-connection test broadcast",
                        "message_type": "system_notification",
                    }

                    async with session.post(
                        f"{self.api_base}/websocket/conversations/{conversation_id}/broadcast",
                        json=test_message,
                    ) as response:
                        if response.status == 200:
                            broadcast_data = await response.json()
                            results["total_recipients"] = broadcast_data.get(
                                "recipients", 0
                            )
                            results["broadcast_successful"] = (
                                results["total_recipients"] > 0
                            )
                            logger.info(
                                f"📊 Broadcast reached {results['total_recipients']} recipients"
                            )
                        else:
                            logger.warning(
                                f"⚠️ Broadcast failed with status {response.status}"
                            )

        except Exception as e:
            logger.error(f"❌ Error in multiple connections test: {e}")

        finally:
            # Clean up connections
            for websocket in connections:
                try:
                    await websocket.close()
                except:
                    pass

        return results

    async def run_connection_tracking_tests(self) -> Dict[str, Any]:
        """Run comprehensive WebSocket connection tracking tests."""
        logger.info("🚀 Starting WebSocket Connection Tracking Investigation")
        logger.info("=" * 70)

        test_results = {
            "single_connection_test": {},
            "multiple_connections_test": {},
            "connection_tracking_working": False,
            "recipient_tracking_working": False,
        }

        # Test 1: Single Connection
        logger.info("🧪 TEST 1: Single WebSocket Connection")
        test_results["single_connection_test"] = (
            await self.test_websocket_connection_establishment()
        )

        # Test 2: Multiple Connections
        logger.info("🧪 TEST 2: Multiple WebSocket Connections")
        test_results["multiple_connections_test"] = (
            await self.test_multiple_connections()
        )

        # Analyze results
        single_test = test_results["single_connection_test"]
        multi_test = test_results["multiple_connections_test"]

        test_results["connection_tracking_working"] = single_test.get(
            "connection_tracked", False
        ) and single_test.get("welcome_message_received", False)

        test_results["recipient_tracking_working"] = (
            multi_test.get("broadcast_successful", False)
            and multi_test.get("total_recipients", 0) > 0
        )

        return test_results


async def main():
    """Main test execution."""
    tester = WebSocketConnectionTrackingTest()
    results = await tester.run_connection_tracking_tests()

    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 WEBSOCKET CONNECTION TRACKING TEST RESULTS")
    logger.info("=" * 70)

    # Single Connection Results
    single_results = results["single_connection_test"]
    logger.info("📊 SINGLE CONNECTION TEST:")
    logger.info(
        f"Connection Successful: {'✅' if single_results.get('connection_successful') else '❌'}"
    )
    logger.info(
        f"Welcome Message Received: {'✅' if single_results.get('welcome_message_received') else '❌'}"
    )
    logger.info(
        f"Connection Tracked: {'✅' if single_results.get('connection_tracked') else '❌'}"
    )
    logger.info(
        f"Conversation Registered: {'✅' if single_results.get('conversation_registered') else '❌'}"
    )

    if single_results.get("error_details"):
        logger.error(f"Error Details: {single_results['error_details']}")

    # Multiple Connections Results
    multi_results = results["multiple_connections_test"]
    logger.info("📊 MULTIPLE CONNECTIONS TEST:")
    logger.info(
        f"Connections Established: {multi_results.get('connections_established', 0)}"
    )
    logger.info(f"Total Recipients: {multi_results.get('total_recipients', 0)}")
    logger.info(
        f"Broadcast Successful: {'✅' if multi_results.get('broadcast_successful') else '❌'}"
    )

    # Overall Assessment
    logger.info("=" * 70)
    logger.info("📈 OVERALL ASSESSMENT:")
    logger.info(
        f"Connection Tracking Working: {'✅' if results['connection_tracking_working'] else '❌'}"
    )
    logger.info(
        f"Recipient Tracking Working: {'✅' if results['recipient_tracking_working'] else '❌'}"
    )

    if results["connection_tracking_working"] and results["recipient_tracking_working"]:
        logger.info("🎉 SUCCESS: WebSocket connection and recipient tracking working!")
    else:
        logger.error(
            "💥 ISSUES: WebSocket connection or recipient tracking needs attention"
        )

        if not results["connection_tracking_working"]:
            logger.error("❌ WebSocket connections not being properly tracked")
            logger.error("💡 Possible causes:")
            logger.error("   - WebSocket manager not registering connections")
            logger.error("   - Connection cleanup happening too early")
            logger.error("   - Authentication issues preventing registration")

        if not results["recipient_tracking_working"]:
            logger.error("❌ Recipients not being found for message broadcasting")
            logger.error("💡 Possible causes:")
            logger.error("   - Conversation ID mapping not working")
            logger.error("   - Connection cleanup before message sending")
            logger.error("   - WebSocket manager conversation tracking broken")

    return results


if __name__ == "__main__":
    results = asyncio.run(main())
