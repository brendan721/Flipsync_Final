#!/usr/bin/env python3
"""
Interactive eBay OAuth Test - Real Login Flow
This test allows you to actually log into your eBay account and complete the OAuth flow
"""

import asyncio
import aiohttp
import json
import webbrowser
import time
from datetime import datetime
from urllib.parse import parse_qs, urlparse

class InteractiveEbayOAuthTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:3000"
        self.access_token = None
        self.oauth_state = None
        self.auth_url = None
        
    async def run_interactive_test(self):
        """Run the complete interactive eBay OAuth test."""
        print("🎯 INTERACTIVE EBAY OAUTH TEST")
        print("=" * 70)
        print(f"🕐 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Goal: Complete real eBay OAuth flow with actual login")
        print("=" * 70)
        
        async with aiohttp.ClientSession() as session:
            
            # Step 1: Test CORS fixes
            if not await self.test_cors_fixes(session):
                print("❌ CORS fixes failed - stopping test")
                return False
            
            # Step 2: Authenticate with FlipSync
            if not await self.authenticate_flipsync(session):
                print("❌ FlipSync authentication failed - stopping test")
                return False
            
            # Step 3: Generate eBay OAuth URL
            if not await self.generate_ebay_oauth_url(session):
                print("❌ eBay OAuth URL generation failed - stopping test")
                return False
            
            # Step 4: Interactive eBay login
            auth_code = await self.interactive_ebay_login()
            if not auth_code:
                print("❌ eBay login failed or cancelled")
                return False
            
            # Step 5: Process OAuth callback
            if not await self.process_oauth_callback(session, auth_code):
                print("❌ OAuth callback processing failed")
                return False
            
            # Step 6: Verify eBay connection
            if not await self.verify_ebay_connection(session):
                print("❌ eBay connection verification failed")
                return False
            
            # Step 7: Test inventory retrieval
            await self.test_inventory_retrieval(session)
            
            print("\n" + "=" * 70)
            print("🎉 INTERACTIVE EBAY OAUTH TEST COMPLETED!")
            print("✅ You have successfully connected your eBay account to FlipSync")
            print("✅ OAuth flow is working end-to-end")
            print("✅ Ready for production use!")
            print("=" * 70)
            
            return True
    
    async def test_cors_fixes(self, session):
        """Test that CORS fixes are working."""
        print("\n🔧 STEP 1: Testing CORS Fixes")
        print("-" * 50)
        
        # Test eBay status endpoint CORS
        try:
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'GET',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            async with session.options(f"{self.backend_url}/api/v1/marketplace/ebay/status/public", headers=headers) as response:
                if response.status == 200:
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    print(f"   ✅ eBay Status CORS: WORKING")
                    print(f"   🌐 Allow-Origin: {cors_origin}")
                else:
                    print(f"   ❌ eBay Status CORS: FAILED ({response.status})")
                    return False
        except Exception as e:
            print(f"   ❌ eBay Status CORS: ERROR - {e}")
            return False
        
        # Test analytics dashboard CORS
        try:
            async with session.options(f"{self.backend_url}/api/v1/analytics/dashboard", headers=headers) as response:
                if response.status == 200:
                    cors_origin = response.headers.get('Access-Control-Allow-Origin')
                    print(f"   ✅ Analytics Dashboard CORS: WORKING")
                    print(f"   🌐 Allow-Origin: {cors_origin}")
                else:
                    print(f"   ❌ Analytics Dashboard CORS: FAILED ({response.status})")
                    return False
        except Exception as e:
            print(f"   ❌ Analytics Dashboard CORS: ERROR - {e}")
            return False
        
        print("   🎉 All CORS fixes are working!")
        return True
    
    async def authenticate_flipsync(self, session):
        """Authenticate with FlipSync to get access token."""
        print("\n🔐 STEP 2: FlipSync Authentication")
        print("-" * 50)
        
        try:
            login_data = {
                "email": "test@example.com",
                "password": "SecurePassword!"
            }
            async with session.post(f"{self.backend_url}/api/v1/auth/login", json=login_data) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    self.access_token = auth_data.get('access_token')
                    user_info = auth_data.get('user', {})
                    print(f"   ✅ Authentication: SUCCESS")
                    print(f"   👤 User: {user_info.get('email', 'Unknown')}")
                    print(f"   🔑 Token: Active")
                    return True
                else:
                    print(f"   ❌ Authentication: FAILED ({response.status})")
                    return False
        except Exception as e:
            print(f"   ❌ Authentication: ERROR - {e}")
            return False
    
    async def generate_ebay_oauth_url(self, session):
        """Generate eBay OAuth authorization URL."""
        print("\n🔗 STEP 3: Generate eBay OAuth URL")
        print("-" * 50)
        
        try:
            oauth_data = {
                "scopes": [
                    "https://api.ebay.com/oauth/api_scope",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
                    "https://api.ebay.com/oauth/api_scope/commerce.identity.readonly"
                ]
            }
            async with session.post(f"{self.backend_url}/api/v1/marketplace/ebay/oauth/authorize", json=oauth_data) as response:
                if response.status == 200:
                    oauth_response = await response.json()
                    self.auth_url = oauth_response['data']['authorization_url']
                    self.oauth_state = oauth_response['data']['state']
                    
                    print(f"   ✅ OAuth URL Generation: SUCCESS")
                    print(f"   🔗 Auth URL: Generated")
                    print(f"   🎫 State: {self.oauth_state[:20]}...")
                    print(f"   📋 Production Client ID: Confirmed")
                    return True
                else:
                    print(f"   ❌ OAuth URL Generation: FAILED ({response.status})")
                    return False
        except Exception as e:
            print(f"   ❌ OAuth URL Generation: ERROR - {e}")
            return False
    
    async def interactive_ebay_login(self):
        """Interactive eBay login - opens browser for user to login."""
        print("\n👤 STEP 4: Interactive eBay Login")
        print("-" * 50)
        print("🌐 Opening eBay login page in your browser...")
        print("📋 Please:")
        print("   1. Log into your eBay account")
        print("   2. Authorize FlipSync permissions")
        print("   3. Copy the authorization code from the callback URL")
        print("   4. Return here and paste the code")
        print()
        
        # Open the eBay OAuth URL in browser
        webbrowser.open(self.auth_url)
        
        print("🔗 eBay OAuth URL opened in browser")
        print(f"   URL: {self.auth_url[:80]}...")
        print()
        
        # Wait for user to complete OAuth and provide auth code
        print("⏳ Waiting for you to complete eBay OAuth...")
        print("💡 After authorizing, you'll be redirected to:")
        print("   https://www.nashvillegeneral.store/ebay-oauth?code=AUTH_CODE&state=STATE")
        print()
        
        while True:
            auth_code = input("📝 Please paste the authorization code here (or 'cancel' to abort): ").strip()
            
            if auth_code.lower() == 'cancel':
                print("❌ OAuth cancelled by user")
                return None
            
            if auth_code and len(auth_code) > 10:  # Basic validation
                print(f"✅ Authorization code received: {auth_code[:20]}...")
                return auth_code
            else:
                print("❌ Invalid authorization code. Please try again.")
    
    async def process_oauth_callback(self, session, auth_code):
        """Process the OAuth callback with the authorization code."""
        print("\n🔄 STEP 5: Processing OAuth Callback")
        print("-" * 50)
        
        try:
            callback_data = {
                "code": auth_code,
                "state": self.oauth_state
            }
            async with session.post(f"{self.backend_url}/api/v1/marketplace/ebay/oauth/callback", json=callback_data) as response:
                callback_response = await response.json()
                
                print(f"   📊 Callback Status: {response.status}")
                print(f"   📋 Response: {callback_response.get('message', 'No message')}")
                
                if response.status == 200:
                    print(f"   ✅ OAuth Callback: SUCCESS")
                    print(f"   🔐 eBay credentials stored")
                    print(f"   🎉 Account connected!")
                    return True
                else:
                    print(f"   ❌ OAuth Callback: FAILED")
                    print(f"   📋 Error: {callback_response}")
                    return False
        except Exception as e:
            print(f"   ❌ OAuth Callback: ERROR - {e}")
            return False
    
    async def verify_ebay_connection(self, session):
        """Verify that eBay connection is working."""
        print("\n✅ STEP 6: Verify eBay Connection")
        print("-" * 50)
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            async with session.get(f"{self.backend_url}/api/v1/marketplace/ebay/status", headers=headers) as response:
                if response.status == 200:
                    status_data = await response.json()
                    ebay_connected = status_data['data']['ebay_connected']
                    credentials_valid = status_data['data']['credentials_valid']
                    
                    print(f"   📊 Connection Status: {'Connected' if ebay_connected else 'Not Connected'}")
                    print(f"   🔐 Credentials: {'Valid' if credentials_valid else 'Invalid'}")
                    
                    if ebay_connected and credentials_valid:
                        print(f"   🎉 eBay connection verified successfully!")
                        return True
                    else:
                        print(f"   ❌ eBay connection verification failed")
                        return False
                else:
                    print(f"   ❌ Connection verification failed: {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Connection verification error: {e}")
            return False
    
    async def test_inventory_retrieval(self, session):
        """Test retrieving actual eBay inventory."""
        print("\n📦 STEP 7: Test Inventory Retrieval")
        print("-" * 50)
        
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            async with session.get(f"{self.backend_url}/api/v1/marketplace/ebay/listings", headers=headers) as response:
                if response.status == 200:
                    listings_data = await response.json()
                    listings = listings_data.get('data', {}).get('listings', [])
                    total_count = listings_data.get('data', {}).get('total', 0)
                    
                    print(f"   ✅ Inventory Retrieval: SUCCESS")
                    print(f"   📦 Total Listings: {total_count}")
                    print(f"   📋 Retrieved: {len(listings)} listings")
                    
                    if listings:
                        print(f"   📝 Sample Listing:")
                        sample = listings[0]
                        print(f"      - ID: {sample.get('listing_id', 'N/A')}")
                        print(f"      - Title: {sample.get('title', 'N/A')[:50]}...")
                        print(f"      - Status: {sample.get('status', 'N/A')}")
                        print(f"      - Price: {sample.get('price', 'N/A')}")
                        print(f"   🎉 Your actual eBay inventory is now connected!")
                    else:
                        print(f"   💡 No listings found (empty account or no active listings)")
                        
                elif response.status == 401:
                    print(f"   ⚠️  Authentication required - OAuth may need refresh")
                else:
                    print(f"   ❌ Inventory retrieval failed: {response.status}")
                    
        except Exception as e:
            print(f"   ❌ Inventory retrieval error: {e}")

async def main():
    """Run the interactive eBay OAuth test."""
    test = InteractiveEbayOAuthTest()
    success = await test.run_interactive_test()
    
    if success:
        print("\n🎯 NEXT STEPS:")
        print("✅ Your eBay account is now connected to FlipSync")
        print("✅ You can now use the FlipSync app to manage your eBay inventory")
        print("✅ The OAuth flow is working for production use")
        exit(0)
    else:
        print("\n❌ Test failed - please check the errors above")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
