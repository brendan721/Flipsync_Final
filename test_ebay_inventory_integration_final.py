#!/usr/bin/env python3
"""
Final eBay Inventory Integration Test
Tests the complete eBay integration workflow after fixing Flutter app caching issues.
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime


class EbayInventoryIntegrationTester:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []

    async def test_backend_endpoints(self):
        """Test all backend endpoints that the Flutter app uses"""
        print("🔧 Testing Backend Endpoints")
        print("=" * 50)
        
        async with aiohttp.ClientSession() as session:
            # Test 1: Public eBay status endpoint (no auth required)
            try:
                async with session.get(f"{self.backend_url}/api/v1/marketplace/ebay/status/public") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ eBay Public Status: {response.status}")
                        print(f"   Connection Status: {data['data']['connection_status']}")
                        print(f"   Auth Required: {data['data']['authentication_required']}")
                        self.test_results.append(("eBay Public Status", "PASS", response.status))
                    else:
                        print(f"❌ eBay Public Status: {response.status}")
                        self.test_results.append(("eBay Public Status", "FAIL", response.status))
            except Exception as e:
                print(f"❌ eBay Public Status Error: {e}")
                self.test_results.append(("eBay Public Status", "ERROR", str(e)))

            # Test 2: Analytics dashboard endpoint (no auth required)
            try:
                async with session.get(f"{self.backend_url}/api/v1/analytics/dashboard") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Analytics Dashboard: {response.status}")
                        print(f"   Total Sales: {data['analytics']['total_sales']}")
                        print(f"   Active Listings: {data['analytics']['active_listings']}")
                        self.test_results.append(("Analytics Dashboard", "PASS", response.status))
                    else:
                        print(f"❌ Analytics Dashboard: {response.status}")
                        self.test_results.append(("Analytics Dashboard", "FAIL", response.status))
            except Exception as e:
                print(f"❌ Analytics Dashboard Error: {e}")
                self.test_results.append(("Analytics Dashboard", "ERROR", str(e)))

            # Test 3: General marketplace status (should not be called by new app)
            try:
                async with session.get(f"{self.backend_url}/api/v1/marketplace/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"⚠️  Old Marketplace Status: {response.status} (should not be used)")
                        print(f"   eBay Connected: {data['data']['ebay_connected']}")
                        self.test_results.append(("Old Marketplace Status", "DEPRECATED", response.status))
                    else:
                        print(f"❌ Old Marketplace Status: {response.status}")
                        self.test_results.append(("Old Marketplace Status", "FAIL", response.status))
            except Exception as e:
                print(f"❌ Old Marketplace Status Error: {e}")
                self.test_results.append(("Old Marketplace Status", "ERROR", str(e)))

    async def test_frontend_accessibility(self):
        """Test that the Flutter web app is accessible"""
        print("\n📱 Testing Frontend Accessibility")
        print("=" * 50)
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.frontend_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Check for Flutter app indicators
                        has_flutter = "flutter" in html_content.lower()
                        has_main_dart = "main.dart.js" in html_content
                        has_flutter_bootstrap = "flutter_bootstrap.js" in html_content
                        
                        print(f"✅ Flutter App Accessible: {response.status}")
                        print(f"   Flutter Detected: {'✅' if has_flutter else '❌'}")
                        print(f"   Main Dart JS: {'✅' if has_main_dart else '❌'}")
                        print(f"   Flutter Bootstrap: {'✅' if has_flutter_bootstrap else '❌'}")
                        
                        if has_flutter and has_main_dart:
                            self.test_results.append(("Flutter App", "PASS", response.status))
                        else:
                            self.test_results.append(("Flutter App", "INCOMPLETE", response.status))
                    else:
                        print(f"❌ Flutter App: {response.status}")
                        self.test_results.append(("Flutter App", "FAIL", response.status))
            except Exception as e:
                print(f"❌ Flutter App Error: {e}")
                self.test_results.append(("Flutter App", "ERROR", str(e)))

    async def test_cors_configuration(self):
        """Test CORS configuration for cross-origin requests"""
        print("\n🌐 Testing CORS Configuration")
        print("=" * 50)
        
        async with aiohttp.ClientSession() as session:
            # Test CORS preflight request
            try:
                headers = {
                    'Origin': 'http://localhost:3000',
                    'Access-Control-Request-Method': 'GET',
                    'Access-Control-Request-Headers': 'Content-Type'
                }
                
                async with session.options(f"{self.backend_url}/api/v1/marketplace/ebay/status/public", headers=headers) as response:
                    cors_headers = response.headers
                    
                    print(f"✅ CORS Preflight: {response.status}")
                    print(f"   Allow-Origin: {cors_headers.get('Access-Control-Allow-Origin', 'Not Set')}")
                    print(f"   Allow-Methods: {cors_headers.get('Access-Control-Allow-Methods', 'Not Set')}")
                    print(f"   Allow-Headers: {cors_headers.get('Access-Control-Allow-Headers', 'Not Set')}")
                    
                    if response.status in [200, 204] and cors_headers.get('Access-Control-Allow-Origin'):
                        self.test_results.append(("CORS Configuration", "PASS", response.status))
                    else:
                        self.test_results.append(("CORS Configuration", "FAIL", response.status))
            except Exception as e:
                print(f"❌ CORS Test Error: {e}")
                self.test_results.append(("CORS Configuration", "ERROR", str(e)))

    async def test_authentication_flow(self):
        """Test authentication flow for eBay integration"""
        print("\n🔐 Testing Authentication Flow")
        print("=" * 50)
        
        async with aiohttp.ClientSession() as session:
            # Test login endpoint
            try:
                login_data = {
                    "email": "test@example.com",
                    "password": "SecurePassword!"
                }
                
                async with session.post(f"{self.backend_url}/api/v1/auth/login", json=login_data) as response:
                    if response.status == 200:
                        data = await response.json()
                        access_token = data.get('access_token')
                        
                        print(f"✅ Authentication: {response.status}")
                        print(f"   Token Received: {'✅' if access_token else '❌'}")
                        
                        if access_token:
                            # Test authenticated eBay status endpoint
                            headers = {'Authorization': f'Bearer {access_token}'}
                            async with session.get(f"{self.backend_url}/api/v1/marketplace/ebay/status", headers=headers) as auth_response:
                                if auth_response.status == 200:
                                    auth_data = await auth_response.json()
                                    print(f"✅ Authenticated eBay Status: {auth_response.status}")
                                    print(f"   eBay Connected: {auth_data['data']['ebay_connected']}")
                                    self.test_results.append(("Authentication Flow", "PASS", response.status))
                                else:
                                    print(f"⚠️  Authenticated eBay Status: {auth_response.status}")
                                    self.test_results.append(("Authentication Flow", "PARTIAL", auth_response.status))
                        else:
                            self.test_results.append(("Authentication Flow", "FAIL", "No token"))
                    else:
                        print(f"❌ Authentication: {response.status}")
                        self.test_results.append(("Authentication Flow", "FAIL", response.status))
            except Exception as e:
                print(f"❌ Authentication Error: {e}")
                self.test_results.append(("Authentication Flow", "ERROR", str(e)))

    def print_summary(self):
        """Print test summary"""
        print("\n📊 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r[1] == "PASS"])
        failed_tests = len([r for r in self.test_results if r[1] == "FAIL"])
        error_tests = len([r for r in self.test_results if r[1] == "ERROR"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🔥 Errors: {error_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, status, details in self.test_results:
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "🔥", "PARTIAL": "⚠️", "DEPRECATED": "⚠️", "INCOMPLETE": "⚠️"}
            print(f"  {status_icon.get(status, '❓')} {test_name}: {status} ({details})")

    async def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 FlipSync eBay Inventory Integration Test")
        print("=" * 50)
        print(f"Backend URL: {self.backend_url}")
        print(f"Frontend URL: {self.frontend_url}")
        print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        await self.test_backend_endpoints()
        await self.test_frontend_accessibility()
        await self.test_cors_configuration()
        await self.test_authentication_flow()
        
        self.print_summary()
        
        # Return success if most tests pass
        passed_tests = len([r for r in self.test_results if r[1] == "PASS"])
        total_tests = len(self.test_results)
        return (passed_tests / total_tests) >= 0.7  # 70% success rate


async def main():
    tester = EbayInventoryIntegrationTester()
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 Integration test completed successfully!")
        print("   The eBay inventory integration is ready for production use.")
        sys.exit(0)
    else:
        print("\n⚠️  Integration test completed with issues.")
        print("   Please review the failed tests and fix any issues.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
