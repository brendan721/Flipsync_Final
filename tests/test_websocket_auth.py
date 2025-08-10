#!/usr/bin/env python3
"""
Simple WebSocket Authentication Test
"""

import asyncio
import json
import websockets
import requests
from datetime import datetime, timezone

BASE_URL = "http://174.138.77.110:8000"
WS_URL = "ws://174.138.77.110:8000"

async def test_websocket_auth():
    print("🧪 Testing WebSocket Authentication")
    
    # First, get a valid token
    print("1. Getting authentication token...")
    login_data = {
        "email": "test@example.com",
        "password": "SecurePassword!"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ Token obtained: {token[:20]}...")
    else:
        print(f"❌ Failed to get token: {response.status_code}")
        return
    
    # Test 1: WebSocket with valid token (query param)
    print("\n2. Testing WebSocket with valid token (query param)...")
    try:
        ws_url = f"{WS_URL}/ws/flipsync?token={token}"
        async with websockets.connect(ws_url, timeout=5) as websocket:
            print("✅ WebSocket connected with token")
            
            # Wait for connection message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=3)
                data = json.loads(message)
                print(f"📨 Received: {data.get('type')}")
            except asyncio.TimeoutError:
                print("⏰ No initial message received")
                
    except Exception as e:
        print(f"❌ WebSocket with token failed: {e}")
    
    # Test 2: WebSocket without token (should fail)
    print("\n3. Testing WebSocket without token (should fail)...")
    try:
        ws_url = f"{WS_URL}/ws/flipsync"
        async with websockets.connect(ws_url, timeout=5) as websocket:
            print("❌ WebSocket connected without token (THIS IS BAD)")
            
            # Try to send a message
            ping_msg = {"type": "ping", "timestamp": datetime.now(timezone.utc).isoformat()}
            await websocket.send(json.dumps(ping_msg))
            
            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=3)
                print(f"📨 Unexpected response: {response}")
            except asyncio.TimeoutError:
                print("⏰ No response (connection may be hanging)")
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"✅ WebSocket properly rejected: {e}")
    except Exception as e:
        print(f"✅ WebSocket connection failed as expected: {e}")
    
    # Test 3: WebSocket with invalid token
    print("\n4. Testing WebSocket with invalid token...")
    try:
        invalid_token = "invalid.jwt.token"
        ws_url = f"{WS_URL}/ws/flipsync?token={invalid_token}"
        async with websockets.connect(ws_url, timeout=5) as websocket:
            print("❌ WebSocket connected with invalid token (THIS IS BAD)")
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"✅ WebSocket properly rejected invalid token: {e}")
    except Exception as e:
        print(f"✅ WebSocket with invalid token failed as expected: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_auth())
