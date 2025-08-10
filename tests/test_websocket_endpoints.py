#!/usr/bin/env python3
"""
Test different WebSocket endpoint paths to find the correct one
"""

import asyncio
import websockets
from websockets.exceptions import InvalidStatusCode, ConnectionClosedError

BASE_WS_URL = "ws://localhost:8000"

async def test_websocket_endpoints():
    print("🔍 Testing WebSocket Endpoint Paths")
    
    # Test different possible WebSocket paths
    test_paths = [
        "/ws/flipsync",           # Expected path (prefix + endpoint)
        "/flipsync",              # Direct endpoint
        "/api/v1/ws/flipsync",    # API versioned path
        "/websocket/flipsync",    # Alternative path
        "/ws",                    # Just the prefix
        "/api/v1/ws",             # From OpenAPI spec
    ]
    
    for i, path in enumerate(test_paths, 1):
        print(f"\n{i}. Testing: {BASE_WS_URL}{path}")
        
        try:
            async with websockets.connect(f"{BASE_WS_URL}{path}", timeout=5) as websocket:
                print("   ✅ Connection successful!")
                
                # Try to receive a message
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2)
                    print(f"   📨 Received: {message[:100]}...")
                except asyncio.TimeoutError:
                    print("   ⏰ No initial message")
                    
        except InvalidStatusCode as e:
            print(f"   ❌ HTTP Status: {e.status_code}")
        except ConnectionClosedError as e:
            print(f"   ❌ Connection closed: Code {e.code}, Reason: {e.reason}")
        except Exception as e:
            print(f"   ❌ Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket_endpoints())
