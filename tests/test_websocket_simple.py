#!/usr/bin/env python3
"""
Test simple WebSocket endpoint to debug routing
"""

import asyncio
import json
import websockets
import requests

BASE_URL = "http://174.138.77.110:8000"
WS_URL = "ws://174.138.77.110:8000"

async def test_simple_websocket():
    print("🔍 Testing Simple WebSocket Endpoints")
    
    # Test the simple test endpoint first
    print("\n1. Testing simple test endpoint: /ws/test")
    try:
        async with websockets.connect(f"{WS_URL}/ws/test", timeout=10) as websocket:
            print("✅ Test endpoint connected!")
            
            # Wait for message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"📨 Received: {data}")
            except asyncio.TimeoutError:
                print("⏰ No message received")
                
    except Exception as e:
        print(f"❌ Test endpoint failed: {type(e).__name__}: {e}")
    
    # Get a token for the main endpoint test
    print("\n2. Getting authentication token...")
    login_data = {"email": "test@example.com", "password": "SecurePassword!"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ Token obtained: {token[:30]}...")
        
        # Test main endpoint with token
        print("\n3. Testing main endpoint with token: /ws/flipsync")
        try:
            ws_url = f"{WS_URL}/ws/flipsync?token={token}"
            async with websockets.connect(ws_url, timeout=10) as websocket:
                print("✅ Main endpoint connected with token!")
                
                # Wait for message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    print(f"📨 Received: {data}")
                except asyncio.TimeoutError:
                    print("⏰ No message received")
                    
        except Exception as e:
            print(f"❌ Main endpoint with token failed: {type(e).__name__}: {e}")
            
    else:
        print(f"❌ Failed to get token: {response.status_code}")

if __name__ == "__main__":
    asyncio.run(test_simple_websocket())
