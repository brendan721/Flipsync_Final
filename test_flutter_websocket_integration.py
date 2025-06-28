#!/usr/bin/env python3
"""
Test Flutter WebSocket Integration with Backend
==============================================

This script tests the complete Flutter → Backend → AI → Response flow
to verify that the WebSocket configuration changes work correctly.
"""

import asyncio
import json
import jwt
import time
import websockets
from datetime import datetime, timedelta


async def test_flutter_websocket_integration():
    """Test the complete Flutter WebSocket integration."""

    print("🧪 Testing Flutter WebSocket Integration")
    print("=" * 50)

    # Step 1: Generate a valid JWT token (same as Flutter would)
    print("🔑 Step 1: Generating JWT token...")
    secret = "development-jwt-secret-not-for-production-use"
    payload = {
        "sub": "flutter-test-user@example.com",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    print(f"✅ JWT token generated: {token[:50]}...")

    # Step 2: Test WebSocket connection (Flutter format)
    print("\n📡 Step 2: Testing WebSocket connection...")

    # Use localhost for testing from within Docker container
    # This tests the WebSocket endpoint that Flutter would connect to
    ws_url = f"ws://localhost:8001/api/v1/ws/chat/main?token={token}"
    print(f"🔗 Connecting to: {ws_url}")

    try:
        # Connect using the Flutter-style URL
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected successfully!")

            # Step 3: Wait for connection established message
            print("\n📨 Step 3: Waiting for connection established...")
            try:
                welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome)
                print(f"✅ Connection established: {welcome_data.get('type')}")
                if welcome_data.get("type") == "connection_established":
                    client_id = welcome_data.get("data", {}).get("client_id")
                    print(f"📱 Client ID: {client_id}")
            except asyncio.TimeoutError:
                print("⚠️ No welcome message received")

            # Step 4: Send Flutter-style chat message
            print("\n💬 Step 4: Sending Flutter-style chat message...")
            flutter_message = {
                "type": "message",
                "conversation_id": "main",
                "data": {
                    "id": f"flutter_msg_{int(time.time())}",
                    "content": "Hello from Flutter! Please provide business analysis for my eBay store.",
                    "sender": "user",
                    "timestamp": datetime.now().isoformat(),
                },
            }

            print(f"📤 Sending: {flutter_message['data']['content']}")
            await websocket.send(json.dumps(flutter_message))

            # Step 5: Monitor for AI response
            print("\n🤖 Step 5: Monitoring for AI response...")
            timeout_seconds = 120
            start_time = datetime.now()

            user_echo_received = False
            ai_response_received = False
            typing_indicators = 0

            while (datetime.now() - start_time).total_seconds() < timeout_seconds:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)

                    message_type = data.get("type")

                    if message_type == "message":
                        sender = data.get("data", {}).get("sender")
                        content = data.get("data", {}).get("content", "")

                        if sender == "user" and not user_echo_received:
                            print("📝 ✅ User message echo received")
                            user_echo_received = True
                        elif sender == "agent":
                            elapsed = (datetime.now() - start_time).total_seconds()
                            print(
                                f"🤖 ✅ AI response received after {elapsed:.1f} seconds!"
                            )
                            print(f"📄 Response preview: {content[:150]}...")

                            # Check if it's a real AI response
                            metadata = data.get("data", {}).get("metadata", {})
                            agent_type = data.get("data", {}).get(
                                "agent_type", "unknown"
                            )

                            if metadata.get("is_fallback"):
                                print("⚠️ This was a fallback response")
                            else:
                                print("✅ This was a real AI-generated response!")

                            print(f"🎯 Agent type: {agent_type}")
                            ai_response_received = True
                            break

                    elif message_type == "typing":
                        typing_indicators += 1
                        if typing_indicators == 1:
                            print("⌨️ ✅ Typing indicator received")

                    elif message_type == "ping":
                        print("🏓 Heartbeat ping received")

                except asyncio.TimeoutError:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(
                        f"⏳ Still waiting for AI response... ({elapsed:.1f}s elapsed)"
                    )
                    continue

            # Step 6: Results summary
            print("\n📊 Step 6: Test Results Summary")
            print("=" * 30)
            print(f"✅ WebSocket Connection: {'PASS' if True else 'FAIL'}")
            print(f"✅ User Message Echo: {'PASS' if user_echo_received else 'FAIL'}")
            print(
                f"✅ Typing Indicators: {'PASS' if typing_indicators > 0 else 'FAIL'}"
            )
            print(f"✅ AI Response: {'PASS' if ai_response_received else 'FAIL'}")

            if ai_response_received and user_echo_received:
                print("\n🎉 SUCCESS: Flutter WebSocket integration is working!")
                print("✅ Port 8001 configuration is correct")
                print("✅ Chat messages are processed successfully")
                print("✅ AI responses are delivered via WebSocket")
                return True
            else:
                print("\n❌ PARTIAL SUCCESS: Some functionality not working")
                return False

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check if backend is running: docker ps | grep flipsync-api")
        print("2. Verify port mapping: should be 8001:8000")
        print("3. Check backend logs: docker logs flipsync-api")
        return False


async def main():
    """Main test function."""
    print("🚀 Starting Flutter WebSocket Integration Test")
    print("This test verifies the corrected port configuration (8001)")
    print("")

    success = await test_flutter_websocket_integration()

    print("\n" + "=" * 50)
    if success:
        print("🎯 CONCLUSION: Flutter WebSocket integration is READY!")
        print("📱 Flutter app can now connect to backend on port 8001")
        print("💬 Chat functionality will work end-to-end")
    else:
        print("🚨 CONCLUSION: Integration issues detected")
        print("🔧 Review the troubleshooting steps above")

    return success


if __name__ == "__main__":
    asyncio.run(main())
