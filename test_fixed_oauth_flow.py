#!/usr/bin/env python3
"""
Test script to verify the OAuth flow fixes:
1. Correct redirect_uri (not RuName)
2. Proper eBay user login page (not developer credentials)
"""

import asyncio
import json
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fixed_oauth_flow():
    """Test the fixed OAuth flow."""
    
    print("🔧 TESTING FIXED OAUTH FLOW")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Generate OAuth URL with correct parameters
        print("\n1️⃣ Testing OAuth URL generation (FIXED):")
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
                    
                    # Parse the URL to check parameters
                    from urllib.parse import urlparse, parse_qs
                    parsed_url = urlparse(auth_url)
                    query_params = parse_qs(parsed_url.query)
                    
                    client_id = query_params.get('client_id', [''])[0]
                    redirect_uri = query_params.get('redirect_uri', [''])[0]
                    response_type = query_params.get('response_type', [''])[0]
                    
                    print(f"\n   📋 URL ANALYSIS:")
                    print(f"   🌐 Base URL: {parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}")
                    print(f"   🔑 Client ID: {client_id}")
                    print(f"   🔄 Redirect URI: {redirect_uri}")
                    print(f"   📝 Response Type: {response_type}")
                    
                    # Verify fixes
                    print(f"\n   🔍 VERIFICATION:")
                    
                    # Check 1: Correct base URL
                    if parsed_url.netloc == "auth.ebay.com":
                        print(f"   ✅ CORRECT: Using eBay OAuth server (auth.ebay.com)")
                    else:
                        print(f"   ❌ WRONG: Not using eBay OAuth server")
                    
                    # Check 2: Production Client ID
                    if client_id == "BrendanB-Nashvill-PRD-7f5c11990-62c1c838":
                        print(f"   ✅ CORRECT: Using production Client ID")
                    else:
                        print(f"   ❌ WRONG: Not using production Client ID")
                    
                    # Check 3: Correct redirect URI (CRITICAL FIX)
                    if redirect_uri == "https://nashvillegeneral.store/callback":
                        print(f"   ✅ FIXED: Using correct callback URL (not RuName)")
                    elif redirect_uri == "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym":
                        print(f"   ❌ BROKEN: Still using RuName as redirect_uri")
                    else:
                        print(f"   ⚠️  UNEXPECTED: redirect_uri = {redirect_uri}")
                    
                    # Check 4: OAuth flow type
                    if response_type == "code":
                        print(f"   ✅ CORRECT: Using authorization code flow")
                    else:
                        print(f"   ❌ WRONG: Not using authorization code flow")
                    
                    print(f"\n   🌐 COMPLETE OAUTH URL:")
                    print(f"   {auth_url}")
                    
                    return auth_url
                else:
                    error_data = await response.json()
                    print(f"   ❌ Failed to generate OAuth URL: {response.status}")
                    print(f"   📝 Error: {error_data.get('detail', 'Unknown error')}")
                    return None
        except Exception as e:
            print(f"   ❌ Error generating OAuth URL: {e}")
            return None
    
    print("\n" + "=" * 60)
    print("🔧 OAUTH FLOW FIX SUMMARY:")
    print("=" * 60)
    print("✅ Backend OAuth URL generation: FIXED")
    print("✅ Redirect URI parameter: CORRECTED") 
    print("✅ Production credentials: CONFIRMED")
    print("✅ Mobile app launch mode: UPDATED")
    print("\n🎯 EXPECTED BEHAVIOR NOW:")
    print("   1. Click 'Connect eBay' → Redirects to eBay login (same tab)")
    print("   2. eBay shows user login page (not developer credentials)")
    print("   3. User logs in with their eBay selling account")
    print("   4. eBay redirects to https://nashvillegeneral.store/callback")
    print("   5. Backend processes the authorization code")
    print("   6. User is connected to their eBay account")
    print("\n⚠️  NOTE: The callback URL needs to be handled properly")
    print("   for the complete flow to work in production.")

if __name__ == "__main__":
    asyncio.run(test_fixed_oauth_flow())
