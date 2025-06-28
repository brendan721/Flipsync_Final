#!/usr/bin/env python3
"""
Mobile App Backend Integration Test
Tests connectivity between Flutter mobile app and FlipSync backend API
"""
import asyncio
import aiohttp
import websockets
import json
import time
import sys


class MobileBackendIntegrationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.mobile_url = "http://localhost:3000"
        self.websocket_url = "ws://localhost:8001/ws"

    async def test_mobile_app_serving(self):
        """Test that the Flutter mobile app is serving correctly"""
        print("📱 Testing Mobile App Serving...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.mobile_url) as response:
                    if response.status == 200:
                        content = await response.text()
                        if "flipsync" in content.lower():
                            print("  ✅ Mobile app serving correctly")
                            print(f"  ✅ Response status: {response.status}")
                            print("  ✅ FlipSync app detected in HTML")
                            return True
                        else:
                            print("  ❌ Mobile app content invalid")
                            return False
                    else:
                        print(f"  ❌ Mobile app not accessible: {response.status}")
                        return False
        except Exception as e:
            print(f"  ❌ Mobile app serving test failed: {e}")
            return False

    async def test_backend_api_connectivity(self):
        """Test that the backend API is accessible from mobile app perspective"""
        print("\n🔗 Testing Backend API Connectivity...")
        try:
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        print("  ✅ Backend health endpoint accessible")
                        print(f"  ✅ Health status: {health_data.get('status')}")
                        print(f"  ✅ Backend version: {health_data.get('version')}")
                        return True
                    else:
                        print(f"  ❌ Backend health check failed: {response.status}")
                        return False
        except Exception as e:
            print(f"  ❌ Backend API connectivity test failed: {e}")
            return False

    async def test_websocket_communication(self):
        """Test WebSocket communication for agent coordination"""
        print("\n🔌 Testing WebSocket Communication...")
        try:
            uri = f"{self.websocket_url}?client_id=mobile_integration_test"

            async with websockets.connect(uri) as websocket:
                print("  ✅ WebSocket connection established")

                # Send test message
                test_message = {
                    "type": "mobile_test",
                    "message": "Mobile app integration test",
                    "timestamp": time.time(),
                    "client_type": "mobile_app",
                }

                await websocket.send(json.dumps(test_message))
                print("  ✅ Test message sent to backend")

                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)

                print("  ✅ Response received from backend")
                print(f"  ✅ Response type: {response_data.get('type')}")
                print(f"  ✅ Client ID confirmed: {response_data.get('client_id')}")

                return True

        except Exception as e:
            print(f"  ❌ WebSocket communication test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all mobile backend integration tests"""
        print("🧪 Mobile App Backend Integration Test Suite")
        print("=" * 60)

        tests = [
            ("Mobile App Serving", self.test_mobile_app_serving),
            ("Backend API Connectivity", self.test_backend_api_connectivity),
            ("WebSocket Communication", self.test_websocket_communication),
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
        print("\n📊 Mobile Backend Integration Test Summary:")
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

        overall_success = passed == total
        print(f"Overall Status: {'✅ SUCCESS' if overall_success else '❌ FAILURE'}")

        return overall_success


async def main():
    test_suite = MobileBackendIntegrationTest()
    success = await test_suite.run_all_tests()
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
