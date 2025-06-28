#!/usr/bin/env python3
"""
Test WebSocket Connection to FlipSync Backend
============================================

This script tests the WebSocket connection with improved authentication handling.
"""

import asyncio
import json
import logging
import websockets
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_websocket_connection():
    """Test WebSocket connection with fallback authentication."""

    # WebSocket URL (no token - testing fallback)
    ws_url = "ws://localhost:8001/api/v1/ws/chat/main?user_id=test_user&client_id=test_client_123"

    logger.info(f"🔗 Connecting to: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            logger.info("✅ WebSocket connected successfully!")

            # Send a test message (using correct format)
            test_message = {
                "type": "message",
                "conversation_id": "main",
                "data": {
                    "content": "What are the best eBay selling strategies?",
                    "sender": "user",
                },
            }

            logger.info(f"📤 Sending message: {test_message}")
            await websocket.send(json.dumps(test_message))

            # Wait for responses
            logger.info("👂 Listening for responses...")

            timeout_seconds = 90  # Increased for AI processing time
            start_time = datetime.now()

            while True:
                try:
                    # Wait for message with timeout
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    logger.info(f"📥 Received: {response}")

                    # Parse response
                    try:
                        response_data = json.loads(response)
                        if (
                            response_data.get("type") == "message"
                            and response_data.get("data", {}).get("sender") == "agent"
                        ):
                            logger.info("🤖 Received agent response!")
                            logger.info(
                                f"📝 Agent message: {response_data.get('data', {}).get('text', 'No text')}"
                            )
                            break
                    except json.JSONDecodeError:
                        logger.warning(
                            f"⚠️ Could not parse response as JSON: {response}"
                        )

                except asyncio.TimeoutError:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > timeout_seconds:
                        logger.warning(f"⏰ Timeout after {timeout_seconds} seconds")
                        break
                    logger.info(f"⏳ Still waiting... ({elapsed:.1f}s elapsed)")
                    continue

                except websockets.exceptions.ConnectionClosed:
                    logger.error("❌ WebSocket connection closed unexpectedly")
                    break

            logger.info("🏁 Test completed")

    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")
        return False

    return True


async def main():
    """Main test function."""
    logger.info("🚀 Starting WebSocket connection test...")

    success = await test_websocket_connection()

    if success:
        logger.info("✅ WebSocket test completed successfully!")
    else:
        logger.error("❌ WebSocket test failed!")

    return success


if __name__ == "__main__":
    asyncio.run(main())
