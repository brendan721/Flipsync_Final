#!/usr/bin/env python3
"""
WebSocket Connection Test for FlipSync Unified WebSocket Endpoint
================================================================

This script tests the WebSocket connection to the FlipSync backend
to verify the unified WebSocket implementation is working correctly.
"""

import asyncio
import json
import websockets
import sys
from datetime import datetime

async def test_websocket_connection():
    """Test connection to FlipSync unified WebSocket endpoint."""
    
    # WebSocket URL for FlipSync unified endpoint
    ws_url = "ws://localhost:8000/ws/flipsync"
    
    # Add query parameters
    params = {
        "client_id": f"test_client_{int(datetime.now().timestamp())}",
        "conversation_id": "test_conversation",
        "user_id": "test_user"
    }
    
    # Build URL with parameters
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{ws_url}?{param_string}"
    
    print(f"🔌 Testing WebSocket connection to: {full_url}")
    
    try:
        # Connect to WebSocket
        async with websockets.connect(full_url) as websocket:
            print("✅ WebSocket connection established successfully!")
            
            # Wait for connection confirmation
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"📨 Received connection confirmation: {data}")
                
                if data.get("type") == "connection_established":
                    print("✅ Connection confirmation received!")
                    print(f"   Client ID: {data.get('client_id')}")
                    print(f"   Capabilities: {data.get('capabilities')}")
                else:
                    print(f"⚠️ Unexpected message type: {data.get('type')}")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for connection confirmation")
                return False
            
            # Send a test ping message
            ping_message = {
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📤 Sending ping message: {ping_message}")
            await websocket.send(json.dumps(ping_message))
            
            # Wait for pong response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📨 Received response: {data}")
                
                if data.get("type") == "pong":
                    print("✅ Ping/Pong test successful!")
                else:
                    print(f"⚠️ Expected pong, got: {data.get('type')}")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for pong response")
            
            # Send a test chat message
            chat_message = {
                "type": "chat_message",
                "conversation_id": "test_conversation",
                "data": {
                    "message": "Hello from WebSocket test!",
                    "user_id": "test_user"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"📤 Sending chat message: {chat_message}")
            await websocket.send(json.dumps(chat_message))
            
            # Wait for any response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"📨 Received chat response: {data}")
                
            except asyncio.TimeoutError:
                print("⏰ Timeout waiting for chat response")
            
            print("✅ WebSocket test completed successfully!")
            return True
            
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ WebSocket connection closed: {e}")
        return False
    except websockets.exceptions.InvalidURI as e:
        print(f"❌ Invalid WebSocket URI: {e}")
        return False
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

async def main():
    """Main test function."""
    print("🧪 FlipSync WebSocket Connection Test")
    print("=" * 50)
    
    success = await test_websocket_connection()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 WebSocket test PASSED - Connection working correctly!")
        sys.exit(0)
    else:
        print("❌ WebSocket test FAILED - Connection issues detected!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
