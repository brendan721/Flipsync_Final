#!/usr/bin/env python3
"""
Final WebSocket Authentication Test with Valid Token
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_websocket_with_valid_token():
    print("🔐 Final WebSocket Authentication Test")
    
    # Get a valid token
    print("\n1. Getting valid authentication token...")
    login_data = {
        "email": "test@example.com",
        "password": "SecurePassword!"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token")
        user_id = token_data.get("user", {}).get("id")
        print(f"✅ Token obtained for user: {user_id}")
        print(f"📋 Token: {token[:50]}...")
    else:
        print(f"❌ Failed to get token: {response.status_code}")
        return
    
    # Test WebSocket with valid token (query parameter)
    print("\n2. Testing WebSocket with valid token (query parameter)...")
    try:
        ws_url = f"{WS_URL}/ws/flipsync?token={token}"
        print(f"🔌 Connecting to: {ws_url[:50]}...")
        
        async with websockets.connect(ws_url, timeout=10) as websocket:
            print("✅ WebSocket connected successfully with valid token!")
            
            # Send a test message
            test_message = {
                "type": "ping",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id
            }
            await websocket.send(json.dumps(test_message))
            print("📤 Sent ping message")
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"📨 Received response: {data.get('type')} - {data.get('message', '')}")
                
                # Send another message to test bidirectional communication
                chat_message = {
                    "type": "chat_message",
                    "conversation_id": "test-conversation",
                    "data": {
                        "message": "Hello from integration test!",
                        "user_id": user_id
                    }
                }
                await websocket.send(json.dumps(chat_message))
                print("📤 Sent chat message")
                
                # Wait for chat response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(response)
                print(f"📨 Chat response: {data.get('type')}")
                
            except asyncio.TimeoutError:
                print("⏰ No response received (connection established but no messages)")
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ WebSocket connection closed: Code {e.code}, Reason: {e.reason}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket invalid status: {e.status_code}")
    except Exception as e:
        print(f"❌ WebSocket error: {type(e).__name__}: {e}")
    
    # Test WebSocket without token (should fail)
    print("\n3. Testing WebSocket without token (should be rejected)...")
    try:
        ws_url = f"{WS_URL}/ws/flipsync"
        print(f"🔌 Connecting to: {ws_url} (no token)")
        
        async with websockets.connect(ws_url, timeout=5) as websocket:
            print("❌ WebSocket connected without token (THIS SHOULD NOT HAPPEN)")
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"✅ WebSocket properly rejected: Code {e.code}, Reason: {e.reason}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"✅ WebSocket properly rejected with status: {e.status_code}")
    except Exception as e:
        print(f"✅ WebSocket connection failed as expected: {type(e).__name__}: {e}")

    print("\n🎯 WebSocket Authentication Test Complete!")

if __name__ == "__main__":
    asyncio.run(test_websocket_with_valid_token())
