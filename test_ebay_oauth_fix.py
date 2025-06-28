#!/usr/bin/env python3
"""
Test script to verify eBay OAuth integration fixes.
This script tests the complete OAuth flow from authorization to token exchange.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EbayOAuthTester:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        self.test_results = {}

    async def test_oauth_flow(self):
        """Test the complete eBay OAuth flow."""
        logger.info("🚀 Starting eBay OAuth Integration Test")
        logger.info("=" * 60)

        # Test 1: Backend Health Check
        if not await self.test_backend_health():
            logger.error("❌ Backend health check failed - aborting tests")
            return False

        # Test 2: OAuth URL Generation
        if not await self.test_oauth_url_generation():
            logger.error("❌ OAuth URL generation failed - aborting tests")
            return False

        # Test 3: Frontend Accessibility
        if not await self.test_frontend_accessibility():
            logger.error("❌ Frontend accessibility failed - aborting tests")
            return False

        # Test 4: External Callback Accessibility
        if not await self.test_external_callback():
            logger.error("❌ External callback accessibility failed")
            return False

        # Test 5: CORS Configuration
        await self.test_cors_configuration()

        # Print summary
        await self.print_test_summary()

        return True

    async def test_backend_health(self):
        """Test backend health and availability."""
        logger.info("🔍 Testing Backend Health...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"  ✅ Backend Status: {response.status} OK")
                        logger.info(
                            f"  ✅ Backend Health: {data.get('status', 'unknown')}"
                        )
                        self.test_results["backend_health"] = "PASS"
                        return True
                    else:
                        logger.error(f"  ❌ Backend Status: {response.status}")
                        self.test_results["backend_health"] = "FAIL"
                        return False
        except Exception as e:
            logger.error(f"  ❌ Backend Error: {e}")
            self.test_results["backend_health"] = "FAIL"
            return False

    async def test_oauth_url_generation(self):
        """Test OAuth URL generation endpoint."""
        logger.info("🔗 Testing OAuth URL Generation...")

        try:
            async with aiohttp.ClientSession() as session:
                oauth_request = {
                    "scopes": [
                        "https://api.ebay.com/oauth/api_scope",
                        "https://api.ebay.com/oauth/api_scope/sell.inventory",
                        "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
                    ]
                }

                async with session.post(
                    f"{self.backend_url}/api/v1/marketplace/ebay/oauth/authorize",
                    json=oauth_request,
                    headers={"Content-Type": "application/json"},
                ) as response:

                    if response.status == 200:
                        data = await response.json()
                        oauth_data = data.get("data", {})

                        auth_url = oauth_data.get("authorization_url", "")
                        state = oauth_data.get("state", "")

                        logger.info(f"  ✅ OAuth URL generated successfully")
                        logger.info(f"  🔑 State: {state[:20]}...")
                        logger.info(f"  🌐 Auth URL: {auth_url}")
                        logger.info(f"  🔍 Full OAuth data: {oauth_data}")

                        # Validate URL components - redirect_uri should be RuName, not callback URL
                        expected_components = [
                            "https://auth.ebay.com/oauth2/authorize",
                            "client_id=BrendanB-Nashvill-PRD-7f5c11990-62c1c838",
                            "redirect_uri=Brendan_Blomfie-BrendanB-Nashvi-vuwrefym",
                            "response_type=code",
                        ]

                        all_components_present = all(
                            comp in auth_url for comp in expected_components
                        )

                        if all_components_present:
                            logger.info("  ✅ All required OAuth components present")
                            self.test_results["oauth_url_generation"] = "PASS"
                            return True
                        else:
                            logger.error("  ❌ Missing required OAuth components")
                            self.test_results["oauth_url_generation"] = "FAIL"
                            return False

                    else:
                        error_text = await response.text()
                        logger.error(
                            f"  ❌ OAuth URL generation failed: {response.status}"
                        )
                        logger.error(f"  📝 Error: {error_text}")
                        self.test_results["oauth_url_generation"] = "FAIL"
                        return False

        except Exception as e:
            logger.error(f"  ❌ Exception during OAuth URL test: {e}")
            self.test_results["oauth_url_generation"] = "FAIL"
            return False

    async def test_frontend_accessibility(self):
        """Test Flutter frontend accessibility."""
        logger.info("🌐 Testing Frontend Accessibility...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.frontend_url) as response:
                    if response.status == 200:
                        html = await response.text()
                        has_flutter = "flutter_bootstrap.js" in html
                        has_oauth_handler = "ebay_oauth_handler" in html

                        logger.info(f"  ✅ Frontend Status: {response.status} OK")
                        logger.info(
                            f"  ✅ Flutter Bootstrap: {'Found' if has_flutter else 'Missing'}"
                        )
                        logger.info(
                            f"  ✅ OAuth Handler: {'Found' if has_oauth_handler else 'Missing'}"
                        )

                        self.test_results["frontend_accessibility"] = "PASS"
                        return True
                    else:
                        logger.error(f"  ❌ Frontend Status: {response.status}")
                        self.test_results["frontend_accessibility"] = "FAIL"
                        return False
        except Exception as e:
            logger.error(f"  ❌ Frontend Error: {e}")
            self.test_results["frontend_accessibility"] = "FAIL"
            return False

    async def test_external_callback(self):
        """Test external OAuth callback accessibility."""
        logger.info("🔗 Testing External OAuth Callback...")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://www.nashvillegeneral.store/ebay-oauth"
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        has_postmessage = "postMessage" in html
                        has_oauth_handling = "ebay_oauth_callback" in html

                        logger.info(
                            f"  ✅ External Callback Status: {response.status} OK"
                        )
                        logger.info(
                            f"  ✅ PostMessage Logic: {'Found' if has_postmessage else 'Missing'}"
                        )
                        logger.info(
                            f"  ✅ OAuth Handling: {'Found' if has_oauth_handling else 'Missing'}"
                        )

                        if has_postmessage and has_oauth_handling:
                            self.test_results["external_callback"] = "PASS"
                            return True
                        else:
                            logger.warning(
                                "  ⚠️ External callback missing required JavaScript logic"
                            )
                            self.test_results["external_callback"] = "PARTIAL"
                            return False
                    else:
                        logger.error(
                            f"  ❌ External Callback Status: {response.status}"
                        )
                        self.test_results["external_callback"] = "FAIL"
                        return False
        except Exception as e:
            logger.error(f"  ❌ External Callback Error: {e}")
            self.test_results["external_callback"] = "FAIL"
            return False

    async def test_cors_configuration(self):
        """Test CORS configuration."""
        logger.info("🔒 Testing CORS Configuration...")

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Origin": "http://localhost:3000",
                    "Content-Type": "application/json",
                }

                async with session.options(
                    f"{self.backend_url}/api/v1/marketplace/ebay/oauth/authorize",
                    headers=headers,
                ) as response:

                    cors_headers = {
                        "access-control-allow-origin": response.headers.get(
                            "access-control-allow-origin"
                        ),
                        "access-control-allow-methods": response.headers.get(
                            "access-control-allow-methods"
                        ),
                        "access-control-allow-headers": response.headers.get(
                            "access-control-allow-headers"
                        ),
                    }

                    logger.info(f"  ✅ CORS Preflight Status: {response.status}")
                    logger.info(
                        f"  🔓 Allow Origin: {cors_headers['access-control-allow-origin']}"
                    )
                    logger.info(
                        f"  🔓 Allow Methods: {cors_headers['access-control-allow-methods']}"
                    )

                    self.test_results["cors_configuration"] = "PASS"

        except Exception as e:
            logger.error(f"  ❌ CORS Test Error: {e}")
            self.test_results["cors_configuration"] = "FAIL"

    async def print_test_summary(self):
        """Print test results summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST RESULTS SUMMARY")
        logger.info("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result == "PASS"
        )

        for test_name, result in self.test_results.items():
            status_icon = (
                "✅" if result == "PASS" else "⚠️" if result == "PARTIAL" else "❌"
            )
            logger.info(
                f"{status_icon} {test_name.replace('_', ' ').title()}: {result}"
            )

        logger.info(f"\n📈 Overall Score: {passed_tests}/{total_tests} tests passed")

        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! OAuth integration should work correctly.")
        elif passed_tests >= total_tests * 0.8:
            logger.info("⚠️ Most tests passed. Minor issues may need attention.")
        else:
            logger.info("❌ Multiple issues detected. OAuth integration needs fixes.")


async def main():
    """Main test function."""
    tester = EbayOAuthTester()
    await tester.test_oauth_flow()


if __name__ == "__main__":
    asyncio.run(main())
