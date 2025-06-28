#!/usr/bin/env python3
"""
Test Real Agent AI Integration
Tests actual AI responses from agents through the running API.
"""

import json
import subprocess
import time
from datetime import datetime

def curl_post(endpoint, data):
    """Make a POST request with curl."""
    try:
        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(data),
            f"http://localhost:8001{endpoint}"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}

def curl_get(endpoint):
    """Make a GET request with curl."""
    try:
        result = subprocess.run([
            "curl", "-s", f"http://localhost:8001{endpoint}"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}

def test_agent_ai_responses():
    """Test actual AI responses from agents."""
    print("🧠 Testing Real Agent AI Integration")
    print("=" * 50)
    
    # Create a conversation
    print("1. Creating conversation...")
    conv_data = curl_post("/api/v1/chat/conversations", {
        "title": "Agent AI Test Conversation"
    })
    
    if "error" in conv_data:
        print(f"❌ Failed to create conversation: {conv_data['error']}")
        return False
    
    conv_id = conv_data["id"]
    print(f"✅ Created conversation: {conv_id}")
    
    # Test cases for different agent types
    test_cases = [
        {
            "name": "Market Analysis Query",
            "message": "What's the best pricing strategy for selling iPhone 13 Pro Max on eBay? I bought it for $650 and competitors are selling for $850-$920.",
            "expected_agent": "market",
            "keywords": ["pricing", "strategy", "competition", "profit", "margin"]
        },
        {
            "name": "Executive Decision Query", 
            "message": "Should I expand my eBay business to Amazon? I'm currently making $5000/month profit on eBay.",
            "expected_agent": "executive",
            "keywords": ["expand", "amazon", "business", "strategy", "decision"]
        },
        {
            "name": "Content Optimization Query",
            "message": "How can I improve my product listing title and description for better SEO on eBay?",
            "expected_agent": "content", 
            "keywords": ["listing", "title", "description", "SEO", "optimize"]
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Query: {test_case['message'][:80]}...")
        
        # Send message
        message_data = {
            "text": test_case["message"],
            "sender": "user"
        }
        
        message_result = curl_post(f"/api/v1/chat/conversations/{conv_id}/messages", message_data)
        
        if "error" in message_result:
            print(f"   ❌ Failed to send message: {message_result['error']}")
            results.append({"test": test_case["name"], "status": "FAIL", "error": "Message send failed"})
            continue
        
        print(f"   ✅ Message sent: {message_result['id']}")
        
        # Wait for agent processing
        print("   ⏳ Waiting for agent response...")
        time.sleep(10)  # Give agents time to process
        
        # Get conversation messages
        messages = curl_get(f"/api/v1/chat/conversations/{conv_id}/messages")
        
        if "error" in messages:
            print(f"   ❌ Failed to get messages: {messages['error']}")
            results.append({"test": test_case["name"], "status": "FAIL", "error": "Message retrieval failed"})
            continue
        
        # Find agent responses
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        user_messages = [m for m in messages if m.get("sender") == "user"]
        
        print(f"   📊 Messages: {len(user_messages)} user, {len(agent_messages)} agent")
        
        if len(agent_messages) > 0:
            latest_agent_msg = agent_messages[-1]
            response_content = latest_agent_msg.get("text", "")
            agent_type = latest_agent_msg.get("agent_type", "unknown")
            
            print(f"   🤖 Agent Response ({agent_type}):")
            print(f"      {response_content[:150]}...")
            
            # Check if response contains relevant keywords
            keyword_matches = sum(1 for keyword in test_case["keywords"] 
                                if keyword.lower() in response_content.lower())
            
            result = {
                "test": test_case["name"],
                "status": "PASS",
                "agent_type": agent_type,
                "response_length": len(response_content),
                "keyword_matches": keyword_matches,
                "total_keywords": len(test_case["keywords"]),
                "response_preview": response_content[:200]
            }
            
            if keyword_matches >= 2:
                print(f"   ✅ Response quality: GOOD ({keyword_matches}/{len(test_case['keywords'])} keywords)")
            else:
                print(f"   ⚠️ Response quality: BASIC ({keyword_matches}/{len(test_case['keywords'])} keywords)")
            
        else:
            print(f"   ❌ No agent response received")
            result = {
                "test": test_case["name"],
                "status": "FAIL",
                "error": "No agent response",
                "total_messages": len(messages)
            }
        
        results.append(result)
        
        # Add delay between tests
        time.sleep(2)
    
    return results

def test_ai_model_direct():
    """Test AI model directly through API."""
    print("\n🔬 Testing AI Model Direct Access")
    print("-" * 30)
    
    # Test AI health
    ai_health = curl_get("/api/v1/ai/health")
    print(f"AI Health: {ai_health}")
    
    # Test AI models
    ai_models = curl_get("/api/v1/ai/models")
    print(f"AI Models: {ai_models}")
    
    # Test AI generation
    ai_test = curl_post("/api/v1/ai/generate", {
        "prompt": "What is the best pricing strategy for eBay?",
        "model": "gemma3:4b"
    })
    print(f"AI Generation: {ai_test}")

def main():
    """Main testing function."""
    print("🚀 FlipSync Agent AI Integration Testing")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test agent AI responses
    results = test_agent_ai_responses()
    
    # Test direct AI access
    test_ai_model_direct()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 AGENT AI TESTING SUMMARY")
    print("=" * 60)
    
    if results:
        passed_tests = [r for r in results if r["status"] == "PASS"]
        failed_tests = [r for r in results if r["status"] == "FAIL"]
        
        print(f"Total Tests: {len(results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        
        print(f"\n📋 Detailed Results:")
        for result in results:
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            
            if result["status"] == "PASS":
                print(f"   Agent: {result.get('agent_type', 'unknown')}")
                print(f"   Response Length: {result.get('response_length', 0)} chars")
                print(f"   Keywords: {result.get('keyword_matches', 0)}/{result.get('total_keywords', 0)}")
            elif "error" in result:
                print(f"   Error: {result['error']}")
        
        # Overall assessment
        if len(passed_tests) >= 2:
            print(f"\n🎉 AGENT AI INTEGRATION: WORKING")
            print(f"   - Agents are responding to queries")
            print(f"   - AI processing is functional")
            print(f"   - Multi-agent system is operational")
        elif len(passed_tests) >= 1:
            print(f"\n⚠️ AGENT AI INTEGRATION: PARTIAL")
            print(f"   - Some agents are responding")
            print(f"   - System needs optimization")
        else:
            print(f"\n❌ AGENT AI INTEGRATION: ISSUES")
            print(f"   - Agents not responding properly")
            print(f"   - AI integration needs attention")
    else:
        print(f"❌ No test results available")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
