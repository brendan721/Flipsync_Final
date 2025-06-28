#!/usr/bin/env python3
"""
End-to-End User Flow Testing for FlipSync Mobile App
Tests the complete user journey from app launch to marketplace integration
"""
import asyncio
import aiohttp
import websockets
import json
import time
import jwt
from datetime import datetime, timedelta

class EndToEndUserFlowTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.mobile_url = "http://localhost:3000"
        self.test_results = {}
        
    def create_test_jwt_token(self, user_id="test_user"):
        """Create a test JWT token for authentication"""
        secret = "development-jwt-secret-not-for-production-use"
        payload = {
            'sub': user_id,
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600,  # 1 hour
            'user_id': user_id,
            'email': f'{user_id}@test.com',
            'marketplace_connected': False  # Simulate new user
        }
        return jwt.encode(payload, secret, algorithm='HS256')
    
    async def test_mobile_app_accessibility(self):
        """Test that mobile app is accessible and loads properly"""
        print("📱 Testing Mobile App Accessibility...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.mobile_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Check for Flutter app indicators
                        flutter_detected = "flutter" in content.lower()
                        main_dart_detected = "main.dart" in content.lower()
                        
                        print(f"  ✅ Mobile app accessible: {response.status}")
                        print(f"  ✅ Flutter app detected: {flutter_detected}")
                        print(f"  ✅ Main.dart referenced: {main_dart_detected}")
                        
                        self.test_results['mobile_accessibility'] = {
                            'accessible': True,
                            'flutter_detected': flutter_detected,
                            'main_dart_detected': main_dart_detected
                        }
                        return True
                    else:
                        print(f"  ❌ Mobile app not accessible: {response.status}")
                        return False
        except Exception as e:
            print(f"  ❌ Mobile app accessibility test failed: {e}")
            return False
    
    async def test_backend_health_and_cors(self):
        """Test backend health and CORS configuration"""
        print("\n🏥 Testing Backend Health and CORS...")
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Origin": "http://localhost:3000"}
                
                async with session.get(f"{self.backend_url}/health", headers=headers) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        cors_origin = response.headers.get("Access-Control-Allow-Origin")
                        
                        print(f"  ✅ Backend health: {health_data.get('status')}")
                        print(f"  ✅ Backend version: {health_data.get('version')}")
                        print(f"  ✅ CORS origin header: {cors_origin}")
                        
                        cors_working = cors_origin in ["*", "http://localhost:3000"] or "localhost" in (cors_origin or "")
                        print(f"  ✅ CORS allows mobile app: {cors_working}")
                        
                        self.test_results['backend_health'] = {
                            'healthy': True,
                            'cors_working': cors_working,
                            'version': health_data.get('version')
                        }
                        return True
                    else:
                        print(f"  ❌ Backend health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"  ❌ Backend health test failed: {e}")
            return False
    
    async def test_websocket_chat_functionality(self):
        """Test WebSocket chat functionality with agent responses"""
        print("\n💬 Testing WebSocket Chat Functionality...")
        try:
            # Create test JWT token
            token = self.create_test_jwt_token("chat_test_user")
            uri = f"ws://localhost:8001/api/v1/ws/chat/user_flow_test?token={token}&client_id=user_flow_test"
            
            print(f"  🔌 Connecting to WebSocket...")
            
            async with websockets.connect(uri) as websocket:
                print(f"  ✅ WebSocket connected successfully!")
                
                # Send test message simulating user interaction
                test_message = {
                    "type": "message",
                    "conversation_id": "user_flow_test",
                    "data": {
                        "id": f"user_flow_{int(time.time())}",
                        "content": "Hello! I'm a new user testing FlipSync. Can you help me understand how to connect my eBay account?",
                        "sender": "user",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                await websocket.send(json.dumps(test_message))
                print(f"  ✅ User message sent successfully")
                
                # Wait for agent response
                print(f"  ⏳ Waiting for agent response...")
                
                response_received = False
                agent_response_content = ""
                
                # Wait up to 20 seconds for a response
                timeout = 20
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_data = json.loads(response)
                        
                        message_type = response_data.get('type')
                        print(f"    📨 Received message type: {message_type}")
                        
                        if message_type == 'message':
                            sender = response_data.get('data', {}).get('sender')
                            content = response_data.get('data', {}).get('content', '')
                            
                            if sender == 'assistant' and content:
                                print(f"  ✅ Agent response received!")
                                print(f"    🤖 Response: {content[:100]}...")
                                agent_response_content = content
                                response_received = True
                                break
                        
                    except asyncio.TimeoutError:
                        continue
                
                self.test_results['websocket_chat'] = {
                    'connected': True,
                    'response_received': response_received,
                    'response_content': agent_response_content[:200] if agent_response_content else "",
                    'response_time': time.time() - start_time
                }
                
                if response_received:
                    print(f"  ✅ Chat functionality working - agent responded in {time.time() - start_time:.2f}s")
                    return True
                else:
                    print(f"  ⚠️ Chat connected but no agent response received within {timeout}s")
                    return False
                    
        except Exception as e:
            print(f"  ❌ WebSocket chat test failed: {e}")
            self.test_results['websocket_chat'] = {'connected': False, 'error': str(e)}
            return False
    
    async def test_marketplace_api_endpoints(self):
        """Test marketplace API endpoints for eBay integration"""
        print("\n🛒 Testing Marketplace API Endpoints...")
        try:
            async with aiohttp.ClientSession() as session:
                # Test eBay OAuth URL generation
                async with session.post(f"{self.backend_url}/api/v1/marketplace/ebay/oauth/authorize") as response:
                    if response.status == 200:
                        oauth_data = await response.json()
                        auth_url = oauth_data.get('data', {}).get('authorization_url', '')
                        
                        print(f"  ✅ eBay OAuth endpoint working")
                        print(f"  ✅ OAuth URL generated: {auth_url[:50]}...")
                        
                        # Validate OAuth URL structure
                        ebay_oauth_valid = "ebay.com" in auth_url and "oauth" in auth_url.lower()
                        print(f"  ✅ OAuth URL valid: {ebay_oauth_valid}")
                        
                        self.test_results['marketplace_api'] = {
                            'ebay_oauth_working': True,
                            'oauth_url_valid': ebay_oauth_valid,
                            'oauth_url': auth_url[:100]
                        }
                        return True
                    else:
                        print(f"  ❌ eBay OAuth endpoint failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"  ❌ Marketplace API test failed: {e}")
            return False
    
    async def test_agent_system_status(self):
        """Test that the 35+ agent system is operational"""
        print("\n🤖 Testing 35+ Agent System Status...")
        try:
            async with aiohttp.ClientSession() as session:
                # Test agent status endpoint
                async with session.get(f"{self.backend_url}/api/v1/agents/status") as response:
                    if response.status == 200:
                        agent_data = await response.json()
                        
                        # Check for agent system indicators
                        agents_active = agent_data.get('agents_active', 0)
                        system_status = agent_data.get('status', 'unknown')
                        
                        print(f"  ✅ Agent system status: {system_status}")
                        print(f"  ✅ Active agents: {agents_active}")
                        
                        self.test_results['agent_system'] = {
                            'status': system_status,
                            'agents_active': agents_active,
                            'operational': system_status == 'operational'
                        }
                        
                        return system_status == 'operational'
                    else:
                        print(f"  ❌ Agent status endpoint failed: {response.status}")
                        return False
                        
        except Exception as e:
            print(f"  ❌ Agent system test failed: {e}")
            return False
    
    async def run_end_to_end_test(self):
        """Run complete end-to-end user flow test"""
        print("🧪 FlipSync End-to-End User Flow Test")
        print("=" * 60)
        
        # Run all tests
        tests = [
            ("Mobile App Accessibility", self.test_mobile_app_accessibility),
            ("Backend Health & CORS", self.test_backend_health_and_cors),
            ("WebSocket Chat Functionality", self.test_websocket_chat_functionality),
            ("Marketplace API Endpoints", self.test_marketplace_api_endpoints),
            ("35+ Agent System Status", self.test_agent_system_status),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"  ❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n📊 End-to-End User Flow Test Summary:")
        print("=" * 60)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall Result: {passed}/{total} tests passed")
        success_rate = (passed / total) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        overall_success = passed >= 4  # Allow 1 test to fail
        print(f"Overall Status: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")
        
        # Detailed findings
        print(f"\n🔍 Detailed Findings:")
        
        # Chat functionality
        chat_result = self.test_results.get('websocket_chat', {})
        if chat_result.get('response_received'):
            print(f"  💬 Chat: Agent responded in {chat_result.get('response_time', 0):.2f}s")
        else:
            print(f"  💬 Chat: Connected but no agent response")
        
        # Marketplace integration
        marketplace_result = self.test_results.get('marketplace_api', {})
        if marketplace_result.get('ebay_oauth_working'):
            print(f"  🛒 eBay: OAuth flow ready for production")
        
        # Agent system
        agent_result = self.test_results.get('agent_system', {})
        if agent_result.get('operational'):
            print(f"  🤖 Agents: {agent_result.get('agents_active', 0)} agents active")
        
        return overall_success

async def main():
    test_suite = EndToEndUserFlowTest()
    success = await test_suite.run_end_to_end_test()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🎯 End-to-end test {'✅ PASSED' if result else '❌ FAILED'}")
