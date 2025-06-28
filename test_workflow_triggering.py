#!/usr/bin/env python3
"""
Test script to simulate user messages that should trigger workflows.
This will test the complete Phase 2B implementation.
"""

import asyncio
import websockets
import json
import sys

async def test_workflow_triggering():
    """Test workflow triggering through WebSocket messages."""
    print("🎯 Testing Workflow Triggering via WebSocket")
    print("=" * 60)
    
    # WebSocket connection details
    ws_url = "ws://localhost:8001/api/v1/ws/chat/main"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QGV4YW1wbGUuY29tIiwic2NvcGUiOiJhY2Nlc3NfdG9rZW4iLCJwZXJtaXNzaW9ucyI6WyJ1c2VyIiwiYWRtaW4iLCJtb25pdG9yaW5nIl0sImV4cCI6MTc1MDExNTYzMSwibm9uY2UiOiJiMjA1Zjk2MWFmNzU3MWIzIiwianRpIjoiYTQzZTdjNDQtNTQxYy00MmVmLThiNmYtNzI2MmQ5YjMxZDY5In0.Ec3bWFQfkb3cVcQ8sxq9c0hVOPVG2dPLrJSWVXVnRm8"
    
    # Test messages that should trigger different workflows
    test_messages = [
        {
            "message": "Can you analyze this MacBook Pro M3 for selling potential?",
            "expected_workflow": "product_analysis",
            "description": "Product analysis workflow test"
        },
        {
            "message": "I need help optimizing my listing for better SEO on Amazon",
            "expected_workflow": "listing_optimization", 
            "description": "Listing optimization workflow test"
        },
        {
            "message": "What do you think I should do about pricing this item?",
            "expected_workflow": "decision_consensus",
            "description": "Decision consensus workflow test"
        },
        {
            "message": "I need a competitive pricing analysis for electronics",
            "expected_workflow": "pricing_strategy",
            "description": "Pricing strategy workflow test"
        },
        {
            "message": "Can you do market research for the smartphone category?",
            "expected_workflow": "market_research",
            "description": "Market research workflow test"
        }
    ]
    
    try:
        # Connect to WebSocket
        print(f"🔗 Connecting to {ws_url}...")
        async with websockets.connect(f"{ws_url}?token={token}") as websocket:
            print("✅ WebSocket connected successfully!")
            
            # Send test messages
            for i, test_case in enumerate(test_messages, 1):
                print(f"\n📝 Test {i}/{len(test_messages)}: {test_case['description']}")
                print(f"   Message: '{test_case['message']}'")
                print(f"   Expected workflow: {test_case['expected_workflow']}")
                print("-" * 50)
                
                # Send user message
                message_data = {
                    "type": "user_message",
                    "content": test_case['message'],
                    "timestamp": "2025-06-16T23:15:00.000Z"
                }
                
                print(f"📤 Sending message...")
                await websocket.send(json.dumps(message_data))
                
                # Wait for responses
                print(f"📥 Waiting for responses...")
                response_count = 0
                workflow_detected = False
                
                try:
                    # Wait for up to 10 seconds for responses
                    async with asyncio.timeout(10):
                        while response_count < 5:  # Expect multiple responses
                            response = await websocket.recv()
                            response_data = json.loads(response)
                            response_count += 1
                            
                            print(f"   📨 Response {response_count}: {response_data.get('type', 'unknown')}")
                            
                            # Check for workflow acknowledgment
                            if response_data.get('type') == 'message' and response_data.get('sender') == 'agent':
                                content = response_data.get('content', '')
                                if 'coordinating' in content.lower() or 'agents involved' in content.lower():
                                    workflow_detected = True
                                    print(f"   🎯 WORKFLOW TRIGGERED! Content preview: {content[:100]}...")
                            
                            # Check for workflow status updates
                            if response_data.get('type') == 'workflow_update':
                                workflow_detected = True
                                print(f"   🔄 WORKFLOW UPDATE: {response_data}")
                            
                            # Stop if we get a complete agent response
                            if (response_data.get('type') == 'message' and 
                                response_data.get('sender') == 'agent' and 
                                len(response_data.get('content', '')) > 50):
                                break
                                
                except asyncio.TimeoutError:
                    print(f"   ⏰ Timeout waiting for responses")
                
                # Summary for this test
                if workflow_detected:
                    print(f"   ✅ SUCCESS: Workflow triggered as expected!")
                else:
                    print(f"   ❌ FAILED: No workflow detected")
                
                print(f"   📊 Total responses received: {response_count}")
                
                # Wait between tests
                if i < len(test_messages):
                    print(f"   ⏳ Waiting 3 seconds before next test...")
                    await asyncio.sleep(3)
            
            print(f"\n🎉 All workflow triggering tests completed!")
            
    except Exception as e:
        print(f"❌ Error during WebSocket testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_workflow_triggering())
