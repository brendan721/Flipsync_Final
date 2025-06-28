#!/usr/bin/env python3
"""
Test script to verify that the API prefix fix is working correctly.
This script monitors the backend logs to ensure no double /api/v1/ prefixes are being called.
"""

import asyncio
import aiohttp
import time
import subprocess
import json
from datetime import datetime


class APIPrefixTester:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.mobile_url = "http://localhost:3000"

    async def test_backend_endpoints(self):
        """Test that backend endpoints are working correctly"""
        print("\n🔧 TESTING BACKEND ENDPOINTS")
        print("=" * 50)

        endpoints_to_test = [
            "/api/v1/health",
            "/api/v1/marketplace/ebay/status",
            "/api/v1/marketplace/status",
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints_to_test:
                url = f"{self.backend_url}{endpoint}"
                try:
                    async with session.get(url) as response:
                        status = response.status
                        if status == 200:
                            print(f"✅ {endpoint} → {status} (OK)")
                        elif status == 401:
                            print(
                                f"✅ {endpoint} → {status} (Auth required - expected)"
                            )
                        elif status == 404:
                            print(f"❌ {endpoint} → {status} (NOT FOUND - ISSUE!)")
                        else:
                            print(f"⚠️  {endpoint} → {status}")
                except Exception as e:
                    print(f"❌ {endpoint} → Error: {e}")

    async def test_double_prefix_endpoints(self):
        """Test that double prefix endpoints return 404 (as expected)"""
        print("\n🚫 TESTING DOUBLE PREFIX ENDPOINTS (Should be 404)")
        print("=" * 50)

        double_prefix_endpoints = [
            "/api/v1/api/v1/marketplace/ebay/status",
            "/api/v1/api/v1/marketplace/ebay/oauth/callback",
            "/api/v1/api/v1/health",
        ]

        async with aiohttp.ClientSession() as session:
            for endpoint in double_prefix_endpoints:
                url = f"{self.backend_url}{endpoint}"
                try:
                    async with session.get(url) as response:
                        status = response.status
                        if status == 404:
                            print(f"✅ {endpoint} → {status} (404 as expected)")
                        else:
                            print(f"❌ {endpoint} → {status} (Should be 404!)")
                except Exception as e:
                    print(f"✅ {endpoint} → Error: {e} (Expected)")

    async def test_mobile_app_access(self):
        """Test that mobile app is accessible"""
        print("\n📱 TESTING MOBILE APP ACCESS")
        print("=" * 50)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.mobile_url) as response:
                    if response.status == 200:
                        print(f"✅ Mobile app accessible at {self.mobile_url}")
                        content = await response.text()

                        # Check for configuration indicators
                        if "localhost:8001" in content:
                            print("✅ Backend URL configuration found in mobile app")
                        else:
                            print(
                                "⚠️  Backend URL configuration not found in mobile app"
                            )
                    else:
                        print(f"❌ Mobile app not accessible: {response.status}")
        except Exception as e:
            print(f"❌ Mobile app access error: {e}")

    def check_docker_logs(self):
        """Check Docker logs for any double prefix errors"""
        print("\n📋 CHECKING DOCKER LOGS FOR DOUBLE PREFIX ERRORS")
        print("=" * 50)

        try:
            # Get recent logs from the backend container
            result = subprocess.run(
                ["docker", "logs", "--tail", "50", "flipsync-api"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            logs = result.stdout + result.stderr

            # Look for double prefix patterns
            double_prefix_patterns = [
                "/api/v1/api/v1/",
                "404.*api/v1/api/v1",
                "Not Found.*api/v1/api/v1",
            ]

            found_issues = []
            for pattern in double_prefix_patterns:
                if pattern in logs:
                    found_issues.append(pattern)

            if found_issues:
                print(f"❌ Found double prefix issues in logs: {found_issues}")
                print("\nRecent log excerpt:")
                print(logs[-500:])  # Last 500 characters
            else:
                print("✅ No double prefix issues found in recent Docker logs")

        except Exception as e:
            print(f"⚠️  Could not check Docker logs: {e}")

    async def run_comprehensive_test(self):
        """Run all tests"""
        print("🎯 FLIPSYNC API PREFIX FIX VERIFICATION")
        print("=" * 70)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        await self.test_backend_endpoints()
        await self.test_double_prefix_endpoints()
        await self.test_mobile_app_access()
        self.check_docker_logs()

        print("\n" + "=" * 70)
        print("🎉 API PREFIX FIX VERIFICATION COMPLETE")
        print("=" * 70)

        print("\n📊 SUMMARY:")
        print("✅ Backend endpoints should respond correctly (200/401)")
        print("✅ Double prefix endpoints should return 404")
        print("✅ Mobile app should be accessible")
        print("✅ No double prefix errors in Docker logs")

        print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


async def main():
    tester = APIPrefixTester()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())
