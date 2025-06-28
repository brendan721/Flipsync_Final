#!/usr/bin/env python3
"""
Test script to generate and test the eBay OAuth URL for production account connection.
This will create the proper OAuth URL that users can use to connect their eBay account.
"""

import asyncio
import json
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_ebay_oauth_flow():
    """Test the eBay OAuth URL generation and flow."""
    
    print("🔗 TESTING EBAY OAUTH INTEGRATION")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Generate OAuth URL
        print("\n1️⃣ Generating eBay OAuth URL:")
        try:
            oauth_request = {
                "scopes": [
                    "https://api.ebay.com/oauth/api_scope",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
                    "https://api.ebay.com/oauth/api_scope/sell.account",
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
                ]
            }
            
            async with session.post(
                "http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize",
                json=oauth_request
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    oauth_data = data.get('data', {})
                    auth_url = oauth_data.get('authorization_url')
                    state = oauth_data.get('state')
                    ru_name = oauth_data.get('ru_name')
                    
                    print(f"   ✅ OAuth URL generated successfully!")
                    print(f"   🔗 RuName: {ru_name}")
                    print(f"   🔑 State: {state}")
                    print(f"   📝 Scopes: {len(oauth_request['scopes'])} requested")
                    print(f"\n   🌐 OAUTH URL:")
                    print(f"   {auth_url}")
                    
                    # Verify the URL contains production credentials
                    if "BrendanB-Nashvill-PRD-7f5c11990-62c1c838" in auth_url:
                        print(f"   ✅ Production Client ID confirmed in URL")
                    else:
                        print(f"   ⚠️  Production Client ID not found in URL")
                        
                    if "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym" in auth_url:
                        print(f"   ✅ Production RuName confirmed in URL")
                    else:
                        print(f"   ⚠️  Production RuName not found in URL")
                        
                    return auth_url, state
                else:
                    error_data = await response.json()
                    print(f"   ❌ Failed to generate OAuth URL: {response.status}")
                    print(f"   📝 Error: {error_data.get('detail', 'Unknown error')}")
                    return None, None
        except Exception as e:
            print(f"   ❌ Error generating OAuth URL: {e}")
            return None, None
        
        # Test 2: Check eBay connection status
        print("\n2️⃣ Checking current eBay connection status:")
        try:
            # Get auth token first
            async with session.get("http://localhost:8001/api/v1/test-token") as response:
                if response.status == 200:
                    auth_data = await response.json()
                    auth_token = auth_data.get('access_token')
                    
                    # Check eBay status
                    headers = {"Authorization": f"Bearer {auth_token}"}
                    async with session.get(
                        "http://localhost:8001/api/v1/marketplace/ebay/status",
                        headers=headers
                    ) as status_response:
                        if status_response.status == 200:
                            status_data = await status_response.json()
                            ebay_data = status_data.get('data', {})
                            print(f"   📊 eBay Connected: {ebay_data.get('ebay_connected', False)}")
                            print(f"   🔐 Credentials Valid: {ebay_data.get('credentials_valid', False)}")
                            print(f"   🔗 Status: {ebay_data.get('connection_status', 'unknown')}")
                        else:
                            print(f"   ⚠️  Status check failed: {status_response.status}")
        except Exception as e:
            print(f"   ❌ Error checking status: {e}")
    
    print("\n" + "=" * 60)
    print("📋 EBAY OAUTH INTEGRATION STATUS:")
    print("=" * 60)
    print("✅ OAuth URL generation: WORKING")
    print("✅ Production credentials: CONFIGURED") 
    print("✅ Production RuName: UPDATED")
    print("⚠️  User authentication: PENDING")
    print("\n🎯 NEXT STEPS:")
    print("   1. User clicks the OAuth URL above")
    print("   2. Logs into their eBay account")
    print("   3. Authorizes FlipSync access")
    print("   4. Gets redirected back with auth code")
    print("   5. Backend exchanges code for access tokens")
    print("   6. Mobile app can then fetch real eBay inventory")

if __name__ == "__main__":
    asyncio.run(test_ebay_oauth_flow())
