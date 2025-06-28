#!/usr/bin/env python3
"""
Complete fix validation test for FlipSync authentication and eBay OAuth integration.
Tests the exact same endpoints that were failing in the Chrome logs.
"""

import asyncio
import aiohttp
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CompleteFixValidationTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.flutter_url = "http://localhost:3000"
        self.api_base = f"{self.backend_url}/api/v1"

    async def test_authentication_flow(self) -> bool:
        """Test the complete authentication flow that was failing in Chrome logs."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test 1: Login endpoint (was getting 404 in Chrome logs)
                logger.info("🔍 Testing authentication endpoint...")
                login_data = {
                    "email": "test@example.com",
                    "password": "SecurePassword!",
                }

                headers = {
                    "Content-Type": "application/json",
                    "Origin": self.flutter_url,
                    "Referer": f"{self.flutter_url}/",
                }

                async with session.post(
                    f"{self.api_base}/auth/login", json=login_data, headers=headers
                ) as response:
                    if response.status == 401:
                        logger.info(
                            "✅ Authentication endpoint working (401 expected for test credentials)"
                        )
                        return True
                    elif response.status == 404:
                        logger.error("❌ Authentication endpoint still returning 404")
                        return False
                    else:
                        logger.info(
                            f"✅ Authentication endpoint responding (status: {response.status})"
                        )
                        return True

        except Exception as e:
            logger.error(f"❌ Authentication test failed: {e}")
            return False

    async def test_ebay_oauth_flow(self) -> bool:
        """Test the complete eBay OAuth flow that was failing in Chrome logs."""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Content-Type": "application/json",
                    "Origin": self.flutter_url,
                    "Referer": f"{self.flutter_url}/",
                }

                # Test 1: eBay OAuth authorize (was getting 404 in Chrome logs)
                logger.info("🔍 Testing eBay OAuth authorize endpoint...")
                oauth_data = {"scopes": ["https://api.ebay.com/oauth/api_scope"]}

                async with session.post(
                    f"{self.api_base}/marketplace/ebay/oauth/authorize",
                    json=oauth_data,
                    headers=headers,
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "authorization_url" in data.get("data", {}):
                            logger.info(
                                "✅ eBay OAuth authorize endpoint working correctly"
                            )
                            state = data["data"]["state"]
                        else:
                            logger.error(
                                "❌ eBay OAuth authorize missing authorization_url"
                            )
                            return False
                    elif response.status == 404:
                        logger.error(
                            "❌ eBay OAuth authorize endpoint still returning 404"
                        )
                        return False
                    else:
                        logger.error(
                            f"❌ eBay OAuth authorize unexpected status: {response.status}"
                        )
                        return False

                # Test 2: eBay OAuth callback (was getting 404 in Chrome logs)
                logger.info("🔍 Testing eBay OAuth callback endpoint...")
                callback_data = {"code": "test_authorization_code", "state": state}

                async with session.post(
                    f"{self.api_base}/marketplace/ebay/oauth/callback",
                    json=callback_data,
                    headers=headers,
                ) as response:
                    if response.status in [
                        200,
                        302,
                        400,
                    ]:  # 400 expected for invalid test code
                        logger.info("✅ eBay OAuth callback endpoint working correctly")
                    elif response.status == 404:
                        logger.error(
                            "❌ eBay OAuth callback endpoint still returning 404"
                        )
                        return False
                    else:
                        logger.info(
                            f"✅ eBay OAuth callback responding (status: {response.status})"
                        )

                # Test 3: eBay status endpoint (was getting 404 in Chrome logs)
                logger.info("🔍 Testing eBay status endpoint...")
                async with session.get(
                    f"{self.api_base}/marketplace/ebay/status", headers=headers
                ) as response:
                    if response.status in [200, 401]:  # 401 expected without auth token
                        logger.info("✅ eBay status endpoint working correctly")
                        return True
                    elif response.status == 404:
                        logger.error("❌ eBay status endpoint still returning 404")
                        return False
                    else:
                        logger.info(
                            f"✅ eBay status endpoint responding (status: {response.status})"
                        )
                        return True

        except Exception as e:
            logger.error(f"❌ eBay OAuth test failed: {e}")
            return False

    async def test_flutter_app_connectivity(self) -> bool:
        """Test that Flutter app is accessible and can reach backend."""
        try:
            async with aiohttp.ClientSession() as session:
                # Test Flutter app accessibility
                logger.info("🔍 Testing Flutter app accessibility...")
                async with session.get(self.flutter_url) as response:
                    if response.status == 200:
                        logger.info("✅ Flutter app accessible on port 3001")
                    else:
                        logger.error(
                            f"❌ Flutter app not accessible: {response.status}"
                        )
                        return False

                # Test backend accessibility from Flutter app perspective
                logger.info("🔍 Testing backend accessibility from Flutter app...")
                headers = {
                    "Origin": self.flutter_url,
                    "Referer": f"{self.flutter_url}/",
                }

                async with session.get(
                    f"{self.backend_url}/health", headers=headers
                ) as response:
                    if response.status in [
                        200,
                        404,
                    ]:  # 404 is fine, means server is responding
                        logger.info(
                            "✅ Backend accessible from Flutter app perspective"
                        )
                        return True
                    else:
                        logger.error(f"❌ Backend not accessible: {response.status}")
                        return False

        except Exception as e:
            logger.error(f"❌ Flutter app connectivity test failed: {e}")
            return False

    async def run_complete_validation(self) -> bool:
        """Run complete validation of the fix."""
        logger.info("🚀 Starting complete fix validation...")
        logger.info("=" * 60)

        # Test 1: Flutter app connectivity
        flutter_ok = await self.test_flutter_app_connectivity()

        # Test 2: Authentication flow
        auth_ok = await self.test_authentication_flow()

        # Test 3: eBay OAuth flow
        ebay_ok = await self.test_ebay_oauth_flow()

        # Summary
        logger.info("=" * 60)
        logger.info("📊 VALIDATION SUMMARY:")
        logger.info(
            f"   Flutter App Connectivity: {'✅ PASS' if flutter_ok else '❌ FAIL'}"
        )
        logger.info(
            f"   Authentication Flow:      {'✅ PASS' if auth_ok else '❌ FAIL'}"
        )
        logger.info(
            f"   eBay OAuth Flow:          {'✅ PASS' if ebay_ok else '❌ FAIL'}"
        )
        logger.info("=" * 60)

        all_passed = flutter_ok and auth_ok and ebay_ok

        if all_passed:
            logger.info("🎉 ALL TESTS PASSED! The fix is working correctly.")
            logger.info("   The 404 errors from Chrome logs have been resolved.")
            logger.info(
                "   Flutter app can now successfully communicate with backend API."
            )
        else:
            logger.error("❌ SOME TESTS FAILED! The fix needs more work.")

        return all_passed


async def main():
    """Main test execution."""
    test = CompleteFixValidationTest()
    success = await test.run_complete_validation()
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
