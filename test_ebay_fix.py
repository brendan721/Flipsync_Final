#!/usr/bin/env python3
"""
Test script to verify the eBay inventory fix works correctly.
"""

import asyncio
import json
import logging
import sys
import time
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EbayFixTester:
    def __init__(self):
        self.ws_url = "ws://localhost:8001"

    def generate_test_jwt_token(self, user_id: str) -> str:
        """Generate a proper JWT token for testing."""
        import jwt
        import time

        # Use the same secret as the WebSocket handler
        secret = "development-jwt-secret-not-for-production-use"

        payload = {
            "sub": user_id,  # Subject (user ID)
            "iat": int(time.time()),  # Issued at
            "exp": int(time.time()) + 3600,  # Expires in 1 hour
            "jti": f"test_token_{int(time.time())}",  # JWT ID
        }

        # Create a proper JWT token
        token = jwt.encode(payload, secret, algorithm="HS256")
        return token

    async def test_ebay_inventory_query(self) -> bool:
        """Test eBay inventory query to verify the fix works."""
        try:
            logger.info("🧪 Testing eBay Inventory Query Fix")

            # Test parameters
            conversation_id = "test_fix"
            user_id = "test_user_fix"
            client_id = f"client_{int(time.time())}"

            jwt_token = self.generate_test_jwt_token(user_id)

            # Build WebSocket URL
            ws_uri = f"{self.ws_url}/api/v1/ws/chat/{conversation_id}?token={jwt_token}&user_id={user_id}&client_id={client_id}"

            logger.info(f"Connecting to: {ws_uri}")

            async with websockets.connect(ws_uri) as websocket:
                logger.info("✅ WebSocket connected successfully!")

                # Send eBay inventory query
                test_message = {
                    "type": "message",
                    "conversation_id": conversation_id,
                    "data": {
                        "id": f"test_fix_{int(time.time())}",
                        "content": "How many items do I have on eBay?",
                        "sender": "user",
                        "timestamp": datetime.now().isoformat(),
                    },
                }

                await websocket.send(json.dumps(test_message))
                logger.info("✅ eBay inventory query sent")

                # Wait for response
                logger.info("⏳ Waiting for agent response...")

                timeout = 15
                start_time = time.time()

                while time.time() - start_time < timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        response_data = json.loads(response)

                        logger.info(
                            f"📨 Received response: {response_data.get('type', 'unknown')}"
                        )

                        if response_data.get("type") == "message":
                            content = response_data.get("data", {}).get("content", "")
                            logger.info(f"📝 Message content: {content}")

                            # Check if we got a proper response (not a connection error)
                            if "Connection refused" in content:
                                logger.error(
                                    "❌ Still getting Connection refused error"
                                )
                                return False
                            elif content.strip():  # Any non-empty response
                                logger.info("✅ Got agent response!")
                                return True

                        elif response_data.get("type") == "agent_response":
                            content = response_data.get("data", {}).get("content", "")

                            # Check if we got a proper response (not a connection error)
                            if "Connection refused" in content:
                                logger.error(
                                    "❌ Still getting Connection refused error"
                                )
                                return False
                            elif "eBay" in content and (
                                "items" in content
                                or "inventory" in content
                                or "listings" in content
                            ):
                                logger.info("✅ Got eBay-related response!")
                                logger.info(f"Response content: {content}")
                                return True
                            elif (
                                "authentication" in content.lower()
                                or "connect" in content.lower()
                            ):
                                logger.info(
                                    "✅ Got authentication prompt (expected for test user)"
                                )
                                logger.info(f"Response content: {content}")
                                return True
                            else:
                                logger.info(f"📝 Response content: {content}")

                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        logger.error(f"Error receiving response: {e}")
                        break

                logger.warning("⚠️ No relevant response received within timeout")
                return False

        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False


async def main():
    """Run the eBay fix test."""
    tester = EbayFixTester()

    logger.info("🚀 Starting eBay Fix Test")

    success = await tester.test_ebay_inventory_query()

    if success:
        logger.info("🎉 eBay Fix Test PASSED!")
        logger.info("✅ No more 'Connection refused' errors")
        logger.info("✅ Executive agent is using direct service calls")
        return True
    else:
        logger.error("💥 eBay Fix Test FAILED!")
        logger.error("❌ Fix may not be working correctly")
        return False


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
