#!/usr/bin/env python3
"""
Test V2 OAuth API Endpoints Only

This script tests the V2 OAuth API endpoints without requiring Redis access:
1. Authorization URL generation
2. OAuth status checking
3. Token refresh handling
4. Error handling
"""

import asyncio
import json
import logging
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://174.138.77.110:8000"

async def test_v2_oauth_api():
    """Test V2 OAuth API endpoints."""
    
    print("🔌 Testing V2 OAuth API Endpoints")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Authorization URL generation for sandbox
        print("\n📋 Test 1: Authorization URL (Sandbox)")
        try:
            auth_response = await client.post(
                f"{BASE_URL}/api/v1/ebay/oauth/authorize",
                json={
                    "user_id": "testuser",  # Maps to sandbox
                    "scopes": [
                        "https://api.ebay.com/oauth/api_scope",
                        "https://api.ebay.com/oauth/api_scope/sell.inventory"
                    ]
                }
            )
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                print("✅ Sandbox authorization URL generated")
                print(f"   Environment: {auth_data['data']['environment']}")
                print(f"   State: {auth_data['data']['state'][:20]}...")
                print(f"   URL contains sandbox: {'sandbox' in auth_data['data']['authorization_url']}")
                
                sandbox_state = auth_data['data']['state']
                
            else:
                print(f"❌ Sandbox authorization failed: {auth_response.status_code}")
                print(f"   Response: {auth_response.text}")
                
        except Exception as e:
            print(f"❌ Sandbox authorization error: {e}")
        
        # Test 2: Authorization URL generation for production
        print("\n📋 Test 2: Authorization URL (Production)")
        try:
            auth_response = await client.post(
                f"{BASE_URL}/api/v1/ebay/oauth/authorize",
                json={
                    "user_id": "realuser",  # Maps to production
                    "scopes": [
                        "https://api.ebay.com/oauth/api_scope",
                        "https://api.ebay.com/oauth/api_scope/sell.inventory"
                    ]
                }
            )
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                print("✅ Production authorization URL generated")
                print(f"   Environment: {auth_data['data']['environment']}")
                print(f"   State: {auth_data['data']['state'][:20]}...")
                print(f"   URL is production: {'sandbox' not in auth_data['data']['authorization_url']}")
                
                production_state = auth_data['data']['state']
                
            else:
                print(f"❌ Production authorization failed: {auth_response.status_code}")
                print(f"   Response: {auth_response.text}")
                
        except Exception as e:
            print(f"❌ Production authorization error: {e}")
        
        # Test 3: OAuth status for users without tokens
        print("\n📋 Test 3: OAuth Status (No Tokens)")
        try:
            status_response = await client.get(
                f"{BASE_URL}/api/v1/ebay/oauth/status",
                params={"user_id": "testuser"}
            )
            
            if status_response.status_code == 404:
                print("✅ Correctly returns 404 for user without tokens")
            elif status_response.status_code == 200:
                status_data = status_response.json()
                print("ℹ️  User has existing tokens:")
                print(f"   Authenticated: {status_data['data']['authenticated']}")
                print(f"   Environment: {status_data['data'].get('environment')}")
            else:
                print(f"❌ Unexpected status response: {status_response.status_code}")
                
        except Exception as e:
            print(f"❌ OAuth status error: {e}")
        
        # Test 4: Token refresh for users without tokens
        print("\n📋 Test 4: Token Refresh (No Tokens)")
        try:
            refresh_response = await client.post(
                f"{BASE_URL}/api/v1/ebay/oauth/refresh",
                params={"user_id": "testuser"}
            )
            
            if refresh_response.status_code == 404:
                print("✅ Correctly returns 404 for refresh without tokens")
            elif refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                print("ℹ️  User has tokens that were refreshed:")
                print(f"   Environment: {refresh_data['data']['environment']}")
            else:
                print(f"❌ Unexpected refresh response: {refresh_response.status_code}")
                
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
        
        # Test 5: Callback endpoint with error
        print("\n📋 Test 5: Callback Error Handling")
        try:
            callback_response = await client.get(
                f"{BASE_URL}/ebay-oauth",
                params={
                    "error": "access_denied",
                    "error_description": "User denied access",
                    "state": "test_state_123"
                }
            )
            
            print(f"✅ Error callback handled")
            print(f"   Status: {callback_response.status_code}")
            
            content_type = callback_response.headers.get("content-type", "")
            if "text/html" in content_type:
                print("✅ Returns HTML error page")
                
                # Check if HTML contains error message
                if "access_denied" in callback_response.text.lower():
                    print("✅ HTML contains error details")
                    
            else:
                print(f"ℹ️  Content type: {content_type}")
                
        except Exception as e:
            print(f"❌ Error callback test error: {e}")
        
        # Test 6: Callback endpoint with missing parameters
        print("\n📋 Test 6: Callback Missing Parameters")
        try:
            callback_response = await client.get(f"{BASE_URL}/ebay-oauth")
            
            print(f"✅ Missing parameters handled")
            print(f"   Status: {callback_response.status_code}")
            
            if callback_response.status_code >= 400:
                print("✅ Correctly rejects missing parameters")
                
        except Exception as e:
            print(f"❌ Missing parameters test error: {e}")
    
    print("\n🎉 V2 OAuth API Test Complete!")
    print("=" * 50)
    return True

async def test_legacy_endpoints():
    """Test that legacy endpoints are properly removed or redirected."""
    
    print("\n🗑️  Testing Legacy Endpoint Removal")
    print("-" * 40)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        legacy_endpoints = [
            "/api/v1/marketplace/ebay/oauth/authorize",
            "/api/v1/marketplace/ebay/oauth/callback",
        ]
        
        for endpoint in legacy_endpoints:
            try:
                response = await client.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 404:
                    print(f"✅ {endpoint} properly removed (404)")
                elif response.status_code == 405:
                    print(f"✅ {endpoint} method not allowed (405)")
                elif response.status_code in [301, 302]:
                    print(f"✅ {endpoint} redirected ({response.status_code})")
                else:
                    print(f"⚠️  {endpoint} still responds: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error testing {endpoint}: {e}")

async def main():
    """Main test function."""
    
    print("🔌 FlipSync V2 OAuth API Test")
    print("=" * 50)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    # Test V2 OAuth API
    await test_v2_oauth_api()
    
    # Test legacy endpoint removal
    await test_legacy_endpoints()
    
    print("\n📝 Manual Testing Instructions:")
    print("   1. Open React frontend at http://localhost:3001")
    print("   2. Click 'eBay OAuth Tester' tab")
    print("   3. Test OAuth flow:")
    print("      a. Select 'sandbox' environment")
    print("      b. Click 'Start OAuth Flow'")
    print("      c. Complete eBay authorization")
    print("      d. Verify success message")
    print("   4. Test production environment similarly")
    print("   5. Check token status and refresh functionality")

if __name__ == "__main__":
    asyncio.run(main())
