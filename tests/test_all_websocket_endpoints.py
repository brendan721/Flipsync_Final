#!/usr/bin/env python3
"""
Test all WebSocket endpoints to find which ones work
"""

import asyncio
import json
import websockets
import requests

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_all_websocket_endpoints():
    print("🔍 Testing All WebSocket Endpoints")
    
    # Get a token first
    print("\n1. Getting authentication token...")
    login_data = {"email": "test@example.com", "password": "SecurePassword!"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ Token obtained: {token[:30]}...")
    else:
        print(f"❌ Failed to get token: {response.status_code}")
        return
    
    # Test different WebSocket endpoints from the codebase
    endpoints_to_test = [
        # From websocket_unified.py
        "/ws/test",
        "/ws/flipsync",
        
        # From websocket_monitoring.py
        "/ws/monitoring",
        
        # From agents_4plus1.py
        "/api/v1/agents/4plus1/ws/status",
        
        # From decisions_4plus1.py
        "/api/v1/decisions/4plus1/ws/live",
        
        # From chat_4plus1_ws.py
        "/api/v1/chat/4plus1/test-conversation",
        
        # Direct WebSocket endpoints from main.py
        "/ws/agents/",
        "/ws/chat/4plus1/",
    ]
    
    for i, endpoint in enumerate(endpoints_to_test, 2):
        print(f"\n{i}. Testing endpoint: {endpoint}")
        
        # Test without token first
        try:
            async with websockets.connect(f"{WS_URL}{endpoint}", timeout=5) as websocket:
                print(f"   ✅ Connected without token!")
                
                # Try to receive a message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3)
                    print(f"   📨 Received: {message[:100]}...")
                except asyncio.TimeoutError:
                    print("   ⏰ No message received")
                    
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"   ❌ HTTP Status: {e.status_code}")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"   ❌ Connection closed: Code {e.code}, Reason: {e.reason}")
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}: {e}")
        
        # Test with token in query params
        try:
            ws_url = f"{WS_URL}{endpoint}?token={token}"
            async with websockets.connect(ws_url, timeout=5) as websocket:
                print(f"   ✅ Connected with token!")
                
                # Try to receive a message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=3)
                    print(f"   📨 Received: {message[:100]}...")
                except asyncio.TimeoutError:
                    print("   ⏰ No message received")
                    
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"   ❌ With token - HTTP Status: {e.status_code}")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"   ❌ With token - Connection closed: Code {e.code}, Reason: {e.reason}")
        except Exception as e:
            print(f"   ❌ With token - Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_websocket_endpoints())
