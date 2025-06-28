#!/usr/bin/env python3
"""
Test script to reproduce the chat screen clearing issue.
This script simulates the Flutter chat interaction to identify the root cause.
"""

import asyncio
import json
import time
import websockets
import jwt
from datetime import datetime, timedelta


async def test_chat_issue():
    """Test the chat functionality to reproduce the screen clearing issue."""

    print("🔍 CHAT ISSUE INVESTIGATION")
    print("=" * 50)

    # Step 1: Create JWT token for authentication
    print("\n📝 Step 1: Creating JWT token...")
    # Use the development secret from the WebSocket authentication
    secret = "development-jwt-secret-not-for-production-use"
    payload = {
        "sub": "flutter-test-user@example.com",
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        "iat": int(datetime.now().timestamp()),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    print(f"✅ JWT token created: {token[:50]}...")

    # Step 2: Connect to WebSocket
    print("\n🔌 Step 2: Connecting to WebSocket...")
    ws_url = f"ws://localhost:8001/api/v1/ws/chat/main?token={token}"
    print(f"🔗 WebSocket URL: {ws_url}")

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected successfully!")

            # Step 3: Wait for connection established message
            print("\n📨 Step 3: Waiting for connection established...")
            try:
                welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                welcome_data = json.loads(welcome)
                print(f"✅ Connection established: {welcome_data}")

                if welcome_data.get("type") == "connection_established":
                    client_id = welcome_data.get("data", {}).get("client_id")
                    print(f"📱 Client ID: {client_id}")
            except asyncio.TimeoutError:
                print("⚠️ No welcome message received")

            # Step 4: Send first message
            print("\n💬 Step 4: Sending FIRST message...")
            first_message = {
                "type": "message",
                "conversation_id": "main",
                "data": {
                    "id": f"test_msg_1_{int(time.time())}",
                    "content": "hello",
                    "sender": "user",
                    "timestamp": datetime.now().isoformat(),
                },
            }

            print(f"📤 Sending first message: {first_message['data']['content']}")
            await websocket.send(json.dumps(first_message))

            # Monitor responses for first message
            print("\n🔍 Step 5: Monitoring responses to FIRST message...")
            first_message_responses = []
            timeout_seconds = 30
            start_time = datetime.now()

            while (datetime.now() - start_time).seconds < timeout_seconds:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_data = json.loads(response)
                    first_message_responses.append(response_data)

                    print(
                        f"📨 First message response: {response_data.get('type')} - {response_data.get('conversation_id')}"
                    )

                    # Check if we got an AI response
                    if (
                        response_data.get("type") == "message"
                        and response_data.get("data", {}).get("sender") == "agent"
                    ):
                        print("🤖 AI response received for first message!")
                        break

                except asyncio.TimeoutError:
                    continue

            print(
                f"\n📊 First message generated {len(first_message_responses)} responses"
            )

            # Step 6: Send second message (this is where the issue occurs)
            print("\n💬 Step 6: Sending SECOND message (critical test)...")
            second_message = {
                "type": "message",
                "conversation_id": "main",
                "data": {
                    "id": f"test_msg_2_{int(time.time())}",
                    "content": "analyze my pricing strategy",
                    "sender": "user",
                    "timestamp": datetime.now().isoformat(),
                },
            }

            print(f"📤 Sending second message: {second_message['data']['content']}")
            await websocket.send(json.dumps(second_message))

            # Monitor responses for second message - this is where the issue should manifest
            print(
                "\n🔍 Step 7: Monitoring responses to SECOND message (issue detection)..."
            )
            second_message_responses = []
            conversation_id_changes = []

            while (datetime.now() - start_time).seconds < timeout_seconds + 30:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    response_data = json.loads(response)
                    second_message_responses.append(response_data)

                    # Track conversation ID changes
                    conv_id = response_data.get("conversation_id")
                    if conv_id and conv_id != "main":
                        conversation_id_changes.append(conv_id)
                        print(f"🚨 CONVERSATION ID CHANGE DETECTED: {conv_id}")

                    print(
                        f"📨 Second message response: {response_data.get('type')} - {conv_id}"
                    )

                    # Check if we got an AI response
                    if (
                        response_data.get("type") == "message"
                        and response_data.get("data", {}).get("sender") == "agent"
                    ):
                        print("🤖 AI response received for second message!")
                        break

                except asyncio.TimeoutError:
                    continue

            print(
                f"\n📊 Second message generated {len(second_message_responses)} responses"
            )

            # Step 8: Analysis
            print("\n🔍 Step 8: ISSUE ANALYSIS")
            print("=" * 30)

            if conversation_id_changes:
                print(f"🚨 ISSUE DETECTED: Conversation ID changed from 'main' to:")
                for conv_id in set(conversation_id_changes):
                    print(f"   - {conv_id}")
                print("\n💡 This is likely the root cause of the chat screen clearing!")
                print(
                    "   The frontend ChatBloc is listening to 'main' conversation stream,"
                )
                print(
                    "   but the backend is now sending messages to a UUID conversation."
                )
            else:
                print("✅ No conversation ID changes detected")

            # Check for duplicate messages
            all_responses = first_message_responses + second_message_responses
            message_ids = []
            duplicates = []

            for response in all_responses:
                if response.get("type") == "message":
                    msg_id = response.get("data", {}).get("id")
                    if msg_id:
                        if msg_id in message_ids:
                            duplicates.append(msg_id)
                        else:
                            message_ids.append(msg_id)

            if duplicates:
                print(f"⚠️ Duplicate messages detected: {duplicates}")
            else:
                print("✅ No duplicate messages detected")

            print(f"\n📈 SUMMARY:")
            print(f"   - First message responses: {len(first_message_responses)}")
            print(f"   - Second message responses: {len(second_message_responses)}")
            print(f"   - Conversation ID changes: {len(set(conversation_id_changes))}")
            print(f"   - Duplicate messages: {len(duplicates)}")

            return {
                "conversation_id_changes": list(set(conversation_id_changes)),
                "total_responses": len(all_responses),
                "duplicates": duplicates,
                "issue_detected": len(conversation_id_changes) > 0,
            }

    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    result = asyncio.run(test_chat_issue())
    print(f"\n🎯 FINAL RESULT: {result}")
