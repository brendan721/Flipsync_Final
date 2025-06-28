#!/usr/bin/env python3
"""
Test script to verify the workflow final response fix.
This script tests that the third message (workflow final response) is properly received.
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

def create_jwt_token(user_email: str = "flutter-test-user@example.com") -> str:
    """Create a JWT token for authentication."""
    payload = {
        "sub": user_email,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def test_workflow_completion():
    """Test that workflow final response is received."""
    print("🔍 WORKFLOW COMPLETION TEST")
    print("=" * 50)
    
    # Create JWT token
    print("📝 Step 1: Creating JWT token...")
    token = create_jwt_token()
    print(f"✅ JWT token created: {token[:50]}...")
    
    # WebSocket URL with token
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
            
            # Send pricing strategy message
            print("\n💬 Step 3: Sending pricing strategy message...")
            test_message = {
                "type": "message",
                "conversation_id": "main",
                "data": {
                    "id": f"test_msg_{int(time.time())}",
                    "content": "analyze my pricing strategy",
                    "sender": "user",
                    "timestamp": datetime.now().isoformat(),
                },
            }
            
            print(f"📤 Sending message: {test_message['data']['content']}")
            await websocket.send(json.dumps(test_message))
            
            # Monitor responses for up to 8 minutes (workflow can take 3-7 minutes)
            print("\n🔍 Step 4: Monitoring responses (up to 8 minutes)...")
            responses = []
            workflow_responses = []
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
                    
                    # Check if this is a workflow-related message
                    if data.get('type') == 'message':
                        message_data = data.get('data', {})
                        metadata = message_data.get('metadata', {})
                        
                        if metadata.get('is_final_response'):
                            print(f"🎉 WORKFLOW FINAL RESPONSE RECEIVED!")
                            print(f"   Content preview: {message_data.get('content', '')[:100]}...")
                            workflow_responses.append(data)
                            break
                        elif 'workflow' in metadata.get('workflow_type', ''):
                            print(f"   Workflow-related message detected")
                            workflow_responses.append(data)
                    
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
            print(f"   - Workflow responses: {len(workflow_responses)}")
            print(f"   - Test duration: {time.time() - start_time:.1f} seconds")
            
            # Check if we got the final workflow response
            final_response_received = any(
                r.get('data', {}).get('metadata', {}).get('is_final_response') 
                for r in workflow_responses
            )
            
            print(f"\n🎯 FINAL RESULT:")
            print(f"   - Workflow final response received: {final_response_received}")
            
            if final_response_received:
                print("✅ SUCCESS: The fix is working! Third message received.")
            else:
                print("❌ ISSUE: Third message (workflow final response) not received.")
                print("   This indicates the conversation ID mapping issue persists.")
            
            return {
                "success": final_response_received,
                "total_responses": len(responses),
                "workflow_responses": len(workflow_responses),
                "test_duration": time.time() - start_time
            }
    
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(test_workflow_completion())
    print(f"\n🏁 TEST COMPLETE: {result}")
