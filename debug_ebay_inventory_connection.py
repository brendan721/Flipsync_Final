#!/usr/bin/env python3
"""
Debug eBay Inventory Connection
==============================

This script tests the eBay inventory connection from the mobile app perspective
to identify why inventory items are not displaying despite showing "connected" status.

Usage:
    python debug_ebay_inventory_connection.py
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EbayInventoryDebugger:
    """Debug eBay inventory connection issues."""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.session = None
        self.auth_token = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def authenticate(self):
        """Authenticate with the backend to get access token."""
        try:
            # Use test credentials from mobile backend integration docs
            # Backend expects "email" field, not "username"
            login_data = {"email": "test@example.com", "password": "SecurePassword!"}

            logger.info("🔐 Authenticating with backend...")
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login", json=login_data, timeout=10
            ) as response:
                if response.status == 200:
                    auth_response = await response.json()
                    self.auth_token = auth_response.get("access_token")
                    logger.info("✅ Authentication successful")
                    logger.info(f"   Token type: {type(self.auth_token)}")
                    logger.info(
                        f"   Token length: {len(self.auth_token) if self.auth_token else 0}"
                    )
                    logger.info(
                        f"   Token preview: {self.auth_token[:50] if self.auth_token else 'None'}..."
                    )
                    return True
                else:
                    error_text = await response.text()
                    logger.error(
                        f"❌ Authentication failed: {response.status} - {error_text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"❌ Authentication error: {e}")
            return False

    async def test_ebay_connection_status(self):
        """Test eBay connection status endpoint."""
        try:
            headers = (
                {"Authorization": f"Bearer {self.auth_token}"}
                if self.auth_token
                else {}
            )

            logger.info("🔍 Testing eBay connection status...")
            async with self.session.get(
                f"{self.base_url}/api/v1/marketplace/ebay/status",
                headers=headers,
                timeout=10,
            ) as response:
                status_data = await response.json()

                logger.info(f"📊 eBay Connection Status Response:")
                logger.info(f"   Status Code: {response.status}")
                logger.info(f"   Response: {json.dumps(status_data, indent=2)}")

                return response.status == 200, status_data

        except Exception as e:
            logger.error(f"❌ eBay connection status error: {e}")
            return False, {}

    async def test_ebay_inventory_endpoint(self):
        """Test eBay inventory endpoint."""
        try:
            headers = (
                {"Authorization": f"Bearer {self.auth_token}"}
                if self.auth_token
                else {}
            )
            params = {"limit": 10, "offset": 0}

            logger.info("📦 Testing eBay inventory endpoint...")
            async with self.session.get(
                f"{self.base_url}/api/v1/marketplace/ebay/inventory",
                headers=headers,
                params=params,
                timeout=30,
            ) as response:
                inventory_data = await response.json()

                logger.info(f"📊 eBay Inventory Response:")
                logger.info(f"   Status Code: {response.status}")
                logger.info(f"   Response Type: {type(inventory_data)}")
                logger.info(
                    f"   Response Keys: {list(inventory_data.keys()) if isinstance(inventory_data, dict) else 'N/A'}"
                )

                if isinstance(inventory_data, dict):
                    data = inventory_data.get("data", [])
                    logger.info(f"   Data Type: {type(data)}")
                    logger.info(
                        f"   Data Length: {len(data) if isinstance(data, list) else 'N/A'}"
                    )

                    if isinstance(data, list) and data:
                        logger.info(
                            f"   Sample Item Keys: {list(data[0].keys()) if data[0] else 'Empty'}"
                        )
                        logger.info(
                            f"   Sample Item: {json.dumps(data[0], indent=2)[:500]}..."
                        )

                logger.info(
                    f"   Full Response: {json.dumps(inventory_data, indent=2)[:1000]}..."
                )

                return response.status == 200, inventory_data

        except Exception as e:
            logger.error(f"❌ eBay inventory endpoint error: {e}")
            return False, {}

    async def test_token_validation(self):
        """Test token validation with a simple endpoint."""
        try:
            headers = (
                {"Authorization": f"Bearer {self.auth_token}"}
                if self.auth_token
                else {}
            )

            logger.info("🔑 Testing token validation with dashboard endpoint...")
            async with self.session.get(
                f"{self.base_url}/api/v1/dashboard/",
                headers=headers,
                timeout=10,
            ) as response:
                dashboard_data = await response.json()

                logger.info(f"📊 Dashboard Response:")
                logger.info(f"   Status Code: {response.status}")
                logger.info(
                    f"   Response: {json.dumps(dashboard_data, indent=2)[:500]}..."
                )

                return response.status == 200, dashboard_data

        except Exception as e:
            logger.error(f"❌ Dashboard endpoint error: {e}")
            return False, {}

    async def test_marketplace_status_endpoint(self):
        """Test general marketplace status endpoint (no auth required)."""
        try:
            logger.info("🏪 Testing general marketplace status endpoint...")
            async with self.session.get(
                f"{self.base_url}/api/v1/marketplace/status",
                timeout=10,
            ) as response:
                status_data = await response.json()

                logger.info(f"📊 Marketplace Status Response:")
                logger.info(f"   Status Code: {response.status}")
                logger.info(f"   Response: {json.dumps(status_data, indent=2)}")

                return response.status == 200, status_data

        except Exception as e:
            logger.error(f"❌ Marketplace status endpoint error: {e}")
            return False, {}

    async def test_general_inventory_endpoint(self):
        """Test general inventory endpoint."""
        try:
            headers = (
                {"Authorization": f"Bearer {self.auth_token}"}
                if self.auth_token
                else {}
            )
            params = {"limit": 10, "offset": 0}

            logger.info("📋 Testing general inventory endpoint...")
            async with self.session.get(
                f"{self.base_url}/api/v1/inventory/items",
                headers=headers,
                params=params,
                timeout=30,
            ) as response:
                inventory_data = await response.json()

                logger.info(f"📊 General Inventory Response:")
                logger.info(f"   Status Code: {response.status}")
                logger.info(
                    f"   Response: {json.dumps(inventory_data, indent=2)[:1000]}..."
                )

                return response.status == 200, inventory_data

        except Exception as e:
            logger.error(f"❌ General inventory endpoint error: {e}")
            return False, {}

    async def run_debug_tests(self):
        """Run all debug tests."""
        logger.info("🚀 Starting eBay Inventory Debug Tests")
        logger.info("=" * 60)

        # Test 1: Authentication
        auth_success = await self.authenticate()
        if not auth_success:
            logger.error("❌ Cannot proceed without authentication")
            return

        # Test 2: Token Validation
        logger.info("\n" + "=" * 60)
        token_success, token_data = await self.test_token_validation()

        # Test 3: eBay Connection Status
        logger.info("\n" + "=" * 60)
        connection_success, connection_data = await self.test_ebay_connection_status()

        # Test 4: eBay Inventory Endpoint
        logger.info("\n" + "=" * 60)
        inventory_success, inventory_data = await self.test_ebay_inventory_endpoint()

        # Test 5: Marketplace Status (No Auth)
        logger.info("\n" + "=" * 60)
        marketplace_success, marketplace_data = (
            await self.test_marketplace_status_endpoint()
        )

        # Test 6: General Inventory Endpoint
        logger.info("\n" + "=" * 60)
        general_success, general_data = await self.test_general_inventory_endpoint()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("📋 DEBUG TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"✅ Authentication: {'SUCCESS' if auth_success else 'FAILED'}")
        logger.info(
            f"🔗 eBay Connection: {'SUCCESS' if connection_success else 'FAILED'}"
        )
        logger.info(
            f"📦 eBay Inventory: {'SUCCESS' if inventory_success else 'FAILED'}"
        )
        logger.info(
            f"📋 General Inventory: {'SUCCESS' if general_success else 'FAILED'}"
        )

        # Recommendations
        logger.info("\n🔧 RECOMMENDATIONS:")
        if not connection_success:
            logger.info("   1. Check eBay API credentials in .env file")
            logger.info("   2. Verify eBay OAuth token is valid")
            logger.info("   3. Check eBay sandbox/production environment settings")

        if not inventory_success:
            logger.info("   1. Check if eBay agent is properly initialized")
            logger.info("   2. Verify eBay API permissions for inventory access")
            logger.info(
                "   3. Check if there are actual inventory items in eBay account"
            )

        if connection_success and not inventory_success:
            logger.info("   1. eBay is connected but inventory endpoint is failing")
            logger.info(
                "   2. This suggests an issue with the inventory API call or data format"
            )
            logger.info("   3. Check backend logs for eBay agent errors")

        # Save results
        results = {
            "timestamp": datetime.now().isoformat(),
            "authentication": auth_success,
            "ebay_connection": {"success": connection_success, "data": connection_data},
            "ebay_inventory": {"success": inventory_success, "data": inventory_data},
            "general_inventory": {"success": general_success, "data": general_data},
        }

        with open("ebay_debug_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"\n📁 Debug results saved to: ebay_debug_results.json")


async def main():
    """Main debug function."""

    # Check if backend is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "http://localhost:8001/health", timeout=5
            ) as response:
                if response.status != 200:
                    logger.error("❌ Backend is not responding properly")
                    return
    except Exception:
        logger.error("❌ Backend is not running on localhost:8001")
        logger.info("   Please start the backend with: docker-compose up")
        return

    # Run debug tests
    async with EbayInventoryDebugger() as debugger:
        await debugger.run_debug_tests()


if __name__ == "__main__":
    asyncio.run(main())
