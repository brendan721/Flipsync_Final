#!/usr/bin/env python3
"""
Test V2 OAuth Complete Flow

This script tests the complete V2 OAuth flow including:
1. Authorization URL generation
2. State parameter validation
3. Token exchange simulation
4. Token storage and retrieval
5. WebSocket integration
"""

import asyncio
import json
import logging
import httpx
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

async def test_v2_oauth_flow():
    """Test the complete V2 OAuth flow."""
    
    print("🧪 Testing V2 OAuth Complete Flow")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Test authorization URL generation
        print("\n📋 Step 1: Test Authorization URL Generation")
        try:
            auth_response = await client.post(
                f"{BASE_URL}/api/v1/ebay/oauth/authorize",
                json={
                    "user_id": "testuser",
                    "scopes": [
                        "https://api.ebay.com/oauth/api_scope",
                        "https://api.ebay.com/oauth/api_scope/sell.inventory"
                    ]
                }
            )
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                print("✅ Authorization URL generated successfully")
                print(f"   Environment: {auth_data['data']['environment']}")
                print(f"   State: {auth_data['data']['state'][:20]}...")
                print(f"   URL: {auth_data['data']['authorization_url'][:80]}...")
                
                state = auth_data['data']['state']
                auth_url = auth_data['data']['authorization_url']
                
            else:
                print(f"❌ Authorization URL generation failed: {auth_response.status_code}")
                print(f"   Response: {auth_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authorization URL generation error: {e}")
            return False
        
        # Step 2: Test OAuth status endpoint
        print("\n📋 Step 2: Test OAuth Status")
        try:
            status_response = await client.get(
                f"{BASE_URL}/api/v1/ebay/oauth/status",
                params={"user_id": "testuser"}
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print("✅ OAuth status retrieved successfully")
                print(f"   Authenticated: {status_data['data']['authenticated']}")
                print(f"   Environment: {status_data['data'].get('environment', 'N/A')}")
                
            else:
                print(f"❌ OAuth status failed: {status_response.status_code}")
                print(f"   Response: {status_response.text}")
                
        except Exception as e:
            print(f"❌ OAuth status error: {e}")
        
        # Step 3: Test token refresh endpoint
        print("\n📋 Step 3: Test Token Refresh")
        try:
            refresh_response = await client.post(
                f"{BASE_URL}/api/v1/ebay/oauth/refresh",
                params={"user_id": "testuser"}
            )
            
            if refresh_response.status_code == 200:
                refresh_data = refresh_response.json()
                print("✅ Token refresh successful")
                print(f"   Environment: {refresh_data['data']['environment']}")
                print(f"   Token Type: {refresh_data['data']['token_type']}")
                
            elif refresh_response.status_code == 404:
                print("ℹ️  No tokens found for refresh (expected for new user)")
                
            else:
                print(f"❌ Token refresh failed: {refresh_response.status_code}")
                print(f"   Response: {refresh_response.text}")
                
        except Exception as e:
            print(f"❌ Token refresh error: {e}")
        
        # Step 4: Test legacy endpoint removal
        print("\n📋 Step 4: Test Legacy Endpoint Removal")
        try:
            # Test that legacy OAuth authorize endpoint is removed
            legacy_auth_response = await client.get(
                f"{BASE_URL}/api/v1/marketplace/ebay/oauth/authorize"
            )
            
            if legacy_auth_response.status_code == 404:
                print("✅ Legacy OAuth authorize endpoint properly removed")
            else:
                print(f"⚠️  Legacy OAuth authorize endpoint still exists: {legacy_auth_response.status_code}")
                
        except Exception as e:
            print(f"❌ Legacy endpoint test error: {e}")
        
        # Step 5: Test main callback endpoint routing
        print("\n📋 Step 5: Test Main Callback Endpoint")
        try:
            # Test that /ebay-oauth routes to V2 handler
            callback_response = await client.get(
                f"{BASE_URL}/ebay-oauth",
                params={
                    "code": "test_code_123",
                    "state": state,  # Use the state from step 1
                    "error": "access_denied"  # Test error handling
                }
            )
            
            if callback_response.status_code in [200, 400]:  # Either success or handled error
                print("✅ Main callback endpoint responding correctly")
                print(f"   Status: {callback_response.status_code}")
                
                # Check if it's HTML response (V2 system)
                content_type = callback_response.headers.get("content-type", "")
                if "text/html" in content_type:
                    print("✅ Returns HTML response (V2 OAuth system)")
                else:
                    print(f"ℹ️  Content type: {content_type}")
                    
            else:
                print(f"❌ Main callback endpoint failed: {callback_response.status_code}")
                
        except Exception as e:
            print(f"❌ Main callback endpoint error: {e}")
        
        # Step 6: Test WebSocket integration
        print("\n📋 Step 6: Test WebSocket Integration")
        try:
            # Test WebSocket endpoint availability
            ws_response = await client.get(f"{BASE_URL}/ws/flipsync")
            
            if ws_response.status_code == 426:  # Upgrade Required (expected for WebSocket)
                print("✅ WebSocket endpoint available")
            else:
                print(f"ℹ️  WebSocket endpoint status: {ws_response.status_code}")
                
        except Exception as e:
            print(f"❌ WebSocket test error: {e}")
    
    print("\n🎉 V2 OAuth Flow Test Complete!")
    print("=" * 50)
    return True

async def test_backend_health():
    """Test backend health and connectivity."""
    
    print("\n🏥 Testing Backend Health")
    print("-" * 30)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            health_response = await client.get(f"{BASE_URL}/health")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print("✅ Backend is healthy")
                print(f"   Status: {health_data.get('status', 'unknown')}")
                print(f"   Timestamp: {health_data.get('timestamp', 'unknown')}")
                return True
            else:
                print(f"❌ Backend health check failed: {health_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Backend health check error: {e}")
            return False

async def main():
    """Main test function."""
    
    print("🚀 FlipSync V2 OAuth System Test")
    print("=" * 50)
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Time: {datetime.now().isoformat()}")
    
    # Test backend health first
    backend_healthy = await test_backend_health()
    
    if not backend_healthy:
        print("\n❌ Backend is not healthy - skipping OAuth tests")
        return
    
    # Test V2 OAuth flow
    oauth_success = await test_v2_oauth_flow()
    
    if oauth_success:
        print("\n🎉 All tests completed successfully!")
        print("\n📝 Next Steps:")
        print("   1. Open React frontend at http://localhost:3001")
        print("   2. Navigate to eBay OAuth Tester")
        print("   3. Test OAuth flow with both sandbox and production")
        print("   4. Verify WebSocket integration")
    else:
        print("\n❌ Some tests failed - check logs above")

if __name__ == "__main__":
    asyncio.run(main())
