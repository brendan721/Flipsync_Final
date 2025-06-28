#!/usr/bin/env python3
"""
Test Mobile App Connectivity After CORS/WebSocket Fixes
Validates that the connectivity issues have been resolved
"""
import asyncio
import aiohttp
import websockets
import json
import time
from datetime import datetime

class PostFixConnectivityTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.mobile_url = "http://localhost:3000"
        
    async def test_cors_headers(self):
        """Test that CORS headers are now properly configured"""
        print("🔒 Testing CORS Headers After Fix...")
        try:
            async with aiohttp.ClientSession() as session:
                # Test CORS preflight request
                headers = {
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "Content-Type"
                }
                
                async with session.options(f"{self.backend_url}/health", headers=headers) as response:
                    cors_headers = {
                        "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                        "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                        "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
                        "Access-Control-Allow-Credentials": response.headers.get("Access-Control-Allow-Credentials"),
                    }
                    
                    print(f"  📋 CORS Headers Response:")
                    for header, value in cors_headers.items():
                        status = "✅" if value else "❌"
                        print(f"    {status} {header}: {value or 'Not set'}")
                    
                    # Check if localhost:3000 is allowed
                    origin_header = cors_headers.get("Access-Control-Allow-Origin")
                    localhost_allowed = (
                        origin_header == "*" or 
                        "localhost:3000" in (origin_header or "") or
                        "localhost" in (origin_header or "")
                    )
                    
                    print(f"  🎯 Mobile app origin allowed: {'✅ YES' if localhost_allowed else '❌ NO'}")
                    return localhost_allowed
                    
        except Exception as e:
            print(f"  ❌ CORS test failed: {e}")
            return False
    
    async def test_websocket_connectivity(self):
        """Test WebSocket connectivity with mobile app simulation"""
        print("\n🔌 Testing WebSocket Connectivity After Fix...")
        
        websocket_endpoints = [
            ("Chat WebSocket", "ws://localhost:8001/api/v1/ws/chat/test_mobile"),
            ("Basic WebSocket", "ws://localhost:8001/api/v1/ws"),
        ]
        
        results = {}
        
        for name, ws_url in websocket_endpoints:
            try:
                print(f"  🔌 Testing {name}: {ws_url}")
                
                # Add Origin header to simulate mobile app
                extra_headers = {
                    "Origin": "http://localhost:3000"
                }
                
                async with websockets.connect(ws_url, extra_headers=extra_headers) as websocket:
                    print(f"    ✅ Connection established with mobile origin")
                    
                    # Send test message
                    test_message = {
                        "type": "message",
                        "conversation_id": "test_mobile",
                        "data": {
                            "id": f"mobile_test_{int(time.time())}",
                            "content": "Test message from mobile app after connectivity fix",
                            "sender": "user",
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    print(f"    ✅ Test message sent successfully")
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        response_data = json.loads(response)
                        print(f"    ✅ Response received: {response_data.get('type', 'unknown')}")
                        
                        results[name] = {
                            "connected": True,
                            "response_received": True,
                            "response_type": response_data.get('type')
                        }
                        
                    except asyncio.TimeoutError:
                        print(f"    ⚠️ No response received (connection works, but no agent response)")
                        results[name] = {
                            "connected": True,
                            "response_received": False,
                            "note": "Connection successful but no agent response"
                        }
                        
            except Exception as e:
                print(f"    ❌ Connection failed: {e}")
                results[name] = {
                    "connected": False,
                    "error": str(e)
                }
        
        return results
    
    async def test_mobile_app_access(self):
        """Test mobile app accessibility"""
        print("\n📱 Testing Mobile App Access...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.mobile_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"  ✅ Mobile app accessible: {response.status}")
                        print(f"  ✅ Content length: {len(content)} bytes")
                        
                        # Check for Flutter indicators
                        flutter_indicators = ["flutter", "main.dart", "canvaskit"]
                        found_indicators = [ind for ind in flutter_indicators if ind.lower() in content.lower()]
                        print(f"  ✅ Flutter indicators found: {found_indicators}")
                        
                        return True
                    else:
                        print(f"  ❌ Mobile app not accessible: {response.status}")
                        return False
        except Exception as e:
            print(f"  ❌ Mobile app access test failed: {e}")
            return False
    
    async def test_backend_health(self):
        """Test backend health and API accessibility"""
        print("\n🏥 Testing Backend Health...")
        try:
            async with aiohttp.ClientSession() as session:
                # Test with mobile origin header
                headers = {"Origin": "http://localhost:3000"}
                
                async with session.get(f"{self.backend_url}/health", headers=headers) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print(f"  ✅ Backend health: {health_data.get('status')}")
                        print(f"  ✅ Backend version: {health_data.get('version')}")
                        
                        # Check CORS headers in response
                        cors_origin = response.headers.get("Access-Control-Allow-Origin")
                        print(f"  ✅ CORS Origin header: {cors_origin or 'Not set'}")
                        
                        return True
                    else:
                        print(f"  ❌ Backend health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"  ❌ Backend health test failed: {e}")
            return False
    
    async def run_post_fix_validation(self):
        """Run complete post-fix validation"""
        print("🧪 Mobile App Connectivity Post-Fix Validation")
        print("=" * 60)
        
        # Run all tests
        cors_working = await self.test_cors_headers()
        websocket_results = await self.test_websocket_connectivity()
        mobile_accessible = await self.test_mobile_app_access()
        backend_healthy = await self.test_backend_health()
        
        # Analyze WebSocket results
        websocket_connections = sum(1 for result in websocket_results.values() if result.get("connected"))
        total_websocket_tests = len(websocket_results)
        
        # Summary
        print("\n📊 Post-Fix Validation Summary:")
        print("=" * 60)
        
        print(f"🔒 CORS Configuration: {'✅ WORKING' if cors_working else '❌ FAILED'}")
        print(f"🔌 WebSocket Connectivity: {websocket_connections}/{total_websocket_tests} endpoints working")
        print(f"📱 Mobile App Access: {'✅ WORKING' if mobile_accessible else '❌ FAILED'}")
        print(f"🏥 Backend Health: {'✅ WORKING' if backend_healthy else '❌ FAILED'}")
        
        # Overall assessment
        critical_tests = [cors_working, websocket_connections > 0, mobile_accessible, backend_healthy]
        passed_tests = sum(critical_tests)
        total_tests = len(critical_tests)
        
        print(f"\n🎯 Overall Connectivity Status: {passed_tests}/{total_tests} critical tests passed")
        
        if passed_tests == total_tests:
            print("✅ SUCCESS: All connectivity fixes working correctly!")
            print("🚀 Ready for end-to-end user testing")
        elif passed_tests >= 3:
            print("⚠️ PARTIAL SUCCESS: Most fixes working, minor issues remain")
            print("🔧 Ready for testing with monitoring")
        else:
            print("❌ FAILURE: Critical connectivity issues remain")
            print("🛠️ Additional fixes required")
        
        return passed_tests >= 3

async def main():
    test_suite = PostFixConnectivityTest()
    success = await test_suite.run_post_fix_validation()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🔍 Post-fix validation {'✅ PASSED' if result else '❌ FAILED'}")
