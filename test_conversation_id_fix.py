#!/usr/bin/env python3
"""
Test script to verify the conversation ID mapping fix.
This script tests that the workflow final response is sent to both UUID and original conversation IDs.
"""

import asyncio
import json
import time
import websockets
import jwt
from datetime import datetime, timedelta

# JWT Configuration
JWT_SECRET = "development-jwt-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

def create_jwt_token(user_email: str = "test-user-fix@example.com") -> str:
    """Create a JWT token for authentication."""
    payload = {
        "sub": user_email,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def test_conversation_id_fix():
    """Test that the conversation ID mapping fix works."""
    print("🔧 CONVERSATION ID MAPPING FIX TEST")
    print("=" * 50)
    
    # Create JWT token
    print("📝 Step 1: Creating JWT token...")
    token = create_jwt_token()
    print(f"✅ JWT token created: {token[:50]}...")
    
    # WebSocket URL with token - using "main" conversation ID
    ws_url = f"ws://localhost:8001/api/v1/ws/chat/main?token={token}"
    print(f"🔗 WebSocket URL: {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Wait for connection established
            print("📨 Step 2: Waiting for connection established...")
            connection_msg = await websocket.recv()
            connection_data = json.loads(connection_msg)
            print(f"✅ Connection established: {connection_data}")
            client_id = connection_data['data']['client_id']
            print(f"📱 Client ID: {client_id}")
            
            # Send a simple message first to establish conversation mapping
            print("\n💬 Step 3: Sending initial message to establish conversation mapping...")
            initial_message = {
                "type": "message",
                "conversation_id": "main",
                "data": {
                    "id": f"test_initial_{int(time.time())}",
                    "content": "hello",
                    "sender": "user",
                    "timestamp": datetime.now().isoformat(),
                },
            }
            
            print(f"📤 Sending initial message: {initial_message['data']['content']}")
            await websocket.send(json.dumps(initial_message))
            
            # Wait for initial response
            print("🔍 Step 4: Waiting for initial response...")
            initial_responses = []
            for _ in range(3):  # Wait for up to 3 messages (typing, message, etc.)
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    initial_responses.append(data)
                    print(f"📨 Initial response: {data.get('type', 'unknown')}")
                    if data.get('type') == 'message':
                        break
                except asyncio.TimeoutError:
                    break
            
            print(f"✅ Initial conversation established with {len(initial_responses)} responses")
            
            # Now send the pricing strategy message
            print("\n💬 Step 5: Sending pricing strategy message...")
            test_message = {
                "type": "message",
                "conversation_id": "main",
                "data": {
                    "id": f"test_pricing_{int(time.time())}",
                    "content": "analyze my pricing strategy",
                    "sender": "user",
                    "timestamp": datetime.now().isoformat(),
                },
            }
            
            print(f"📤 Sending pricing message: {test_message['data']['content']}")
            await websocket.send(json.dumps(test_message))
            
            # Monitor responses for workflow completion
            print("\n🔍 Step 6: Monitoring for workflow completion...")
            responses = []
            workflow_final_received = False
            start_time = time.time()
            timeout = 480  # 8 minutes
            
            while time.time() - start_time < timeout:
                try:
                    # Wait for message with 30 second timeout
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    responses.append(data)
                    
                    elapsed = time.time() - start_time
                    print(f"📨 [{elapsed:.1f}s] Response: {data.get('type', 'unknown')}")
                    
                    # Check if this is the workflow final response
                    if data.get('type') == 'message':
                        message_data = data.get('data', {})
                        metadata = message_data.get('metadata', {})
                        
                        if metadata.get('is_final_response'):
                            print(f"🎉 WORKFLOW FINAL RESPONSE RECEIVED!")
                            print(f"   Content preview: {message_data.get('content', '')[:100]}...")
                            print(f"   Conversation ID: {data.get('conversation_id', 'unknown')}")
                            workflow_final_received = True
                            break
                        elif 'workflow' in str(metadata):
                            print(f"   Workflow-related message detected")
                    
                    # Also check for ping/pong to show connection is alive
                    if data.get('type') in ['ping', 'pong']:
                        print(f"   💓 Heartbeat: {data.get('type')}")
                
                except asyncio.TimeoutError:
                    elapsed = time.time() - start_time
                    print(f"⏳ [{elapsed:.1f}s] Still waiting for workflow completion...")
                    if elapsed > timeout:
                        break
                    continue
                
                except websockets.exceptions.ConnectionClosed:
                    print("❌ WebSocket connection closed unexpectedly")
                    break
            
            # Analyze results
            print(f"\n📊 RESULTS ANALYSIS:")
            print(f"   - Total responses: {len(responses)}")
            print(f"   - Workflow final response received: {workflow_final_received}")
            print(f"   - Test duration: {time.time() - start_time:.1f} seconds")
            
            print(f"\n🎯 FINAL RESULT:")
            if workflow_final_received:
                print("✅ SUCCESS: The conversation ID mapping fix is working!")
                print("   The third message (workflow final response) was received.")
            else:
                print("❌ ISSUE: Third message (workflow final response) not received.")
                print("   The conversation ID mapping issue may still persist.")
            
            return {
                "success": workflow_final_received,
                "total_responses": len(responses),
                "test_duration": time.time() - start_time
            }
    
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(test_conversation_id_fix())
    print(f"\n🏁 TEST COMPLETE: {result}")
