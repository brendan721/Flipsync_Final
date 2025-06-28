#!/usr/bin/env python3
"""
eBay Client Credentials Grant Test
Tests eBay API connectivity using Client Credentials Grant (simpler than refresh tokens)
"""

import asyncio
import os
import sys
import logging
import aiohttp
import json
import base64
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class eBayClientCredentialsTest:
    """Test eBay API using Client Credentials Grant flow."""
    
    def __init__(self):
        """Initialize with sandbox credentials."""
        self.client_id = os.getenv("SB_EBAY_APP_ID")
        self.client_secret = os.getenv("SB_EBAY_CERT_ID")
        self.sandbox_base_url = "https://api.sandbox.ebay.com"
        self.token_endpoint = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        
    async def get_client_credentials_token(self) -> Optional[str]:
        """Get access token using Client Credentials Grant."""
        logger.info("🔑 Testing Client Credentials Grant...")
        
        try:
            # Prepare credentials for Basic Auth
            credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
            
            headers = {
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json"
            }
            
            # Client credentials grant data
            data = {
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope"
            }
            
            logger.info(f"   Client ID: {self.client_id}")
            logger.info(f"   Token Endpoint: {self.token_endpoint}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.token_endpoint,
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        token_data = json.loads(response_text)
                        access_token = token_data.get("access_token")
                        expires_in = token_data.get("expires_in", 0)
                        
                        logger.info("✅ Client Credentials Grant successful!")
                        logger.info(f"   Access Token: {access_token[:30]}...")
                        logger.info(f"   Expires In: {expires_in} seconds")
                        
                        return access_token
                    else:
                        logger.error(f"❌ Client Credentials Grant failed: HTTP {response.status}")
                        logger.error(f"   Response: {response_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Client Credentials Grant error: {e}")
            return None
    
    async def test_api_call(self, access_token: str) -> bool:
        """Test a simple API call with the access token."""
        logger.info("🌐 Testing eBay API call...")
        
        try:
            # Test the Browse API (public data)
            api_url = f"{self.sandbox_base_url}/buy/browse/v1/item_summary/search"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
            }
            
            params = {
                "q": "iPhone",
                "limit": 3
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    api_url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    
                    logger.info(f"   API Response Status: {response.status}")
                    
                    if response.status == 200:
                        data = json.loads(response_text)
                        item_summaries = data.get("itemSummaries", [])
                        
                        logger.info("✅ eBay API call successful!")
                        logger.info(f"   Found {len(item_summaries)} items")
                        
                        if item_summaries:
                            sample_item = item_summaries[0]
                            logger.info(f"   Sample Item: {sample_item.get('title', 'N/A')}")
                            logger.info(f"   Price: {sample_item.get('price', {}).get('value', 'N/A')}")
                        
                        return True
                    else:
                        logger.error(f"❌ API call failed: HTTP {response.status}")
                        logger.error(f"   Response: {response_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ API call error: {e}")
            return False
    
    async def test_marketplace_specific_calls(self, access_token: str) -> Dict[str, bool]:
        """Test various eBay API endpoints."""
        logger.info("🔍 Testing multiple eBay API endpoints...")
        
        results = {}
        
        # Test endpoints that work with Client Credentials
        test_endpoints = [
            {
                "name": "Browse API - Search",
                "url": f"{self.sandbox_base_url}/buy/browse/v1/item_summary/search",
                "params": {"q": "laptop", "limit": 1}
            },
            {
                "name": "Browse API - Categories",
                "url": f"{self.sandbox_base_url}/commerce/taxonomy/v1/category_tree/0",
                "params": {}
            }
        ]
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US"
        }
        
        async with aiohttp.ClientSession() as session:
            for endpoint in test_endpoints:
                try:
                    async with session.get(
                        endpoint["url"],
                        params=endpoint["params"],
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        success = response.status == 200
                        results[endpoint["name"]] = success
                        
                        if success:
                            logger.info(f"   ✅ {endpoint['name']}: Working")
                        else:
                            logger.warning(f"   ❌ {endpoint['name']}: Failed ({response.status})")
                            
                except Exception as e:
                    logger.error(f"   ❌ {endpoint['name']}: Error - {e}")
                    results[endpoint["name"]] = False
        
        return results
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive Client Credentials test."""
        logger.info("🚀 Starting eBay Client Credentials Test Suite")
        logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        # Validate credentials
        if not self.client_id or not self.client_secret:
            logger.error("❌ Missing sandbox credentials")
            return {"status": "failed", "reason": "Missing credentials"}
        
        logger.info("✅ Sandbox credentials present")
        
        # Test 1: Get access token
        access_token = await self.get_client_credentials_token()
        if not access_token:
            return {"status": "failed", "reason": "Token acquisition failed"}
        
        # Test 2: Basic API call
        api_success = await self.test_api_call(access_token)
        
        # Test 3: Multiple endpoints
        endpoint_results = await self.test_marketplace_specific_calls(access_token)
        
        # Calculate results
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        successful_endpoints = sum(1 for success in endpoint_results.values() if success)
        total_endpoints = len(endpoint_results)
        
        summary = {
            "status": "success" if api_success and successful_endpoints > 0 else "partial",
            "token_acquisition": True,
            "basic_api_call": api_success,
            "endpoint_results": endpoint_results,
            "successful_endpoints": f"{successful_endpoints}/{total_endpoints}",
            "duration_seconds": duration,
            "timestamp": end_time.isoformat(),
            "access_token_preview": access_token[:30] + "..." if access_token else None
        }
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 CLIENT CREDENTIALS TEST SUMMARY")
        logger.info(f"   Status: {'✅ SUCCESS' if summary['status'] == 'success' else '⚠️ PARTIAL'}")
        logger.info(f"   Token Acquisition: {'✅' if summary['token_acquisition'] else '❌'}")
        logger.info(f"   Basic API Call: {'✅' if summary['basic_api_call'] else '❌'}")
        logger.info(f"   Endpoints Working: {summary['successful_endpoints']}")
        logger.info(f"   Duration: {duration:.2f} seconds")
        
        if summary['status'] == 'success':
            logger.info("🎉 eBay Client Credentials authentication is working!")
            logger.info("💡 This proves your eBay sandbox credentials are valid.")
        else:
            logger.warning("⚠️ Some issues found. Check the logs above for details.")
        
        return summary

async def main():
    """Main test execution."""
    tester = eBayClientCredentialsTest()
    results = await tester.run_comprehensive_test()
    
    # Print next steps
    if results.get("status") == "success":
        print("\n🎯 NEXT STEPS:")
        print("1. ✅ Your eBay sandbox credentials are working!")
        print("2. 🔧 The refresh token issue is separate from basic connectivity")
        print("3. 🚀 FlipSync can proceed with eBay integration using Client Credentials")
        print("4. 📝 Consider implementing Client Credentials as fallback for agent authentication")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
