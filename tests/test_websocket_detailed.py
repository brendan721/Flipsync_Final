#!/usr/bin/env python3
"""
Detailed WebSocket Authentication Test with Debug Information
"""

import asyncio
import json
import websockets
import requests
import jwt
from datetime import datetime, timezone

BASE_URL = "http://174.138.77.110:8000"
WS_URL = "ws://174.138.77.110:8000"

async def test_detailed_websocket_auth():
    print("🔍 Detailed WebSocket Authentication Analysis")
    
    # First, get a valid token and decode it
    print("\n1. Getting and analyzing authentication token...")
    login_data = {
        "email": "test@example.com",
        "password": "SecurePassword!"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        token = token_data.get("access_token")
        print(f"✅ Token obtained: {token[:30]}...")
        
        # Decode the token to see its contents
        try:
            # Use the same secret as the backend
            secret = "development-jwt-secret-not-for-production-use"
            payload = jwt.decode(token, secret, algorithms=["HS256"], options={"verify_exp": False})
            print(f"📋 Token payload: {json.dumps(payload, indent=2, default=str)}")
        except Exception as e:
            print(f"❌ Failed to decode token: {e}")
            
    else:
        print(f"❌ Failed to get token: {response.status_code} - {response.text}")
        return
    
    # Test token validation endpoint
    print("\n2. Testing token validation endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/auth/validate-token", headers=headers)
    print(f"Token validation response ({response.status_code}): {response.json()}")
    
    # Test WebSocket with detailed error handling
    print("\n3. Testing WebSocket with detailed error information...")
    
    # Test with query parameter
    print("\n3a. WebSocket with query parameter:")
    try:
        ws_url = f"{WS_URL}/ws/flipsync?token={token}"
        print(f"Connecting to: {ws_url}")
        
        async with websockets.connect(ws_url, timeout=10) as websocket:
            print("✅ WebSocket connected successfully")
            
            # Wait for initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"📨 Initial message: {data.get('type')}")
            except asyncio.TimeoutError:
                print("⏰ No initial message received")
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ WebSocket connection closed: Code {e.code}, Reason: {e.reason}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket invalid status: {e.status_code}")
    except Exception as e:
        print(f"❌ WebSocket error: {type(e).__name__}: {e}")
    
    # Test with Authorization header
    print("\n3b. WebSocket with Authorization header:")
    try:
        ws_url = f"{WS_URL}/ws/flipsync"
        headers = {"Authorization": f"Bearer {token}"}
        print(f"Connecting to: {ws_url} with headers: {headers}")
        
        async with websockets.connect(ws_url, extra_headers=headers, timeout=10) as websocket:
            print("✅ WebSocket connected successfully with headers")
            
            # Wait for initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                print(f"📨 Initial message: {data.get('type')}")
            except asyncio.TimeoutError:
                print("⏰ No initial message received")
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ WebSocket connection closed: Code {e.code}, Reason: {e.reason}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket invalid status: {e.status_code}")
    except Exception as e:
        print(f"❌ WebSocket error: {type(e).__name__}: {e}")
    
    # Test without token (should fail)
    print("\n3c. WebSocket without token (should fail):")
    try:
        ws_url = f"{WS_URL}/ws/flipsync"
        print(f"Connecting to: {ws_url} (no token)")
        
        async with websockets.connect(ws_url, timeout=5) as websocket:
            print("❌ WebSocket connected without token (THIS IS BAD)")
                
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"✅ WebSocket properly rejected: Code {e.code}, Reason: {e.reason}")
    except websockets.exceptions.InvalidStatusCode as e:
        print(f"✅ WebSocket properly rejected with status: {e.status_code}")
    except Exception as e:
        print(f"✅ WebSocket connection failed as expected: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_detailed_websocket_auth())
