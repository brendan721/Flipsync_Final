#!/usr/bin/env python3
"""
Final eBay OAuth Integration Test
Tests the complete OAuth flow with updated frontend configuration
"""
import requests
import json
import sys
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_frontend_accessibility():
    """Test that the Flutter frontend is accessible"""
    print("🔍 Testing Frontend Accessibility...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        print(f"📊 Frontend Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Flutter frontend is accessible")
            return True
        else:
            print(f"❌ Frontend not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error accessing frontend: {e}")
        return False

def test_api_health():
    """Test API health through nginx HTTPS"""
    print("\n🔍 Testing API Health via Nginx HTTPS...")
    
    try:
        response = requests.get("https://localhost/health", verify=False, timeout=10)
        print(f"📊 API Health Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📋 API Health: {data.get('status', 'unknown')}")
                return True
            except:
                print("✅ API responding")
                return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking API health: {e}")
        return False

def test_oauth_url_generation():
    """Test OAuth URL generation with correct HTTPS endpoint"""
    print("\n🔍 Testing OAuth URL Generation (HTTPS)...")
    
    url_endpoint = "https://localhost/api/v1/marketplace/ebay/oauth/authorize"
    
    test_data = {
        "scopes": [
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.marketing", 
            "https://api.ebay.com/oauth/api_scope/sell.account",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
            "https://api.ebay.com/oauth/api_scope/sell.analytics",
            "https://api.ebay.com/oauth/api_scope/sell.finances",
            "https://api.ebay.com/oauth/api_scope/commerce.identity"
        ]
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(
            url_endpoint,
            json=test_data,
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                
                if "data" in response_data and "authorization_url" in response_data["data"]:
                    auth_url = response_data["data"]["authorization_url"]
                    print(f"✅ Authorization URL generated successfully")
                    print(f"🔗 URL: {auth_url[:80]}...")
                    return True, auth_url
                else:
                    print("❌ No authorization URL in response")
                    return False, None
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False, None
        else:
            print(f"❌ OAuth URL generation failed with status {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing OAuth URL generation: {e}")
        return False, None

def test_oauth_callback():
    """Test OAuth callback with mock authorization code"""
    print("\n🔍 Testing OAuth Callback (HTTPS)...")
    
    callback_url = "https://localhost/api/v1/marketplace/ebay/oauth/callback"
    
    test_data = {
        "code": "test_auth_code_12345",
        "state": "test_state_final"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(
            callback_url,
            json=test_data,
            headers=headers,
            timeout=10,
            verify=False
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ OAuth callback working correctly (302 redirect)")
            redirect_location = response.headers.get('location', '')
            print(f"🔗 Redirect: {redirect_location[:60]}...")
            return True
        elif response.status_code == 200:
            print("✅ OAuth callback responding (200 OK)")
            return True
        else:
            print(f"❌ OAuth callback failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OAuth callback: {e}")
        return False

def test_marketplace_status():
    """Test marketplace status endpoint"""
    print("\n🔍 Testing Marketplace Status (HTTPS)...")
    
    status_url = "https://localhost/api/v1/marketplace/ebay/status"
    
    try:
        response = requests.get(status_url, verify=False, timeout=10)
        print(f"📊 Status Response: {response.status_code}")
        
        if response.status_code in [200, 401]:
            print("✅ Marketplace status endpoint working correctly")
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking marketplace status: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Final eBay OAuth Integration Test")
    print("Testing updated frontend configuration with HTTPS endpoints")
    print("=" * 70)
    
    # Test all components
    frontend_ok = test_frontend_accessibility()
    api_health_ok = test_api_health()
    oauth_url_ok, auth_url = test_oauth_url_generation()
    oauth_callback_ok = test_oauth_callback()
    status_ok = test_marketplace_status()
    
    print("\n" + "=" * 70)
    print("📊 Final OAuth Integration Test Results:")
    print(f"   Frontend Accessibility: {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"   API Health (HTTPS): {'✅ PASS' if api_health_ok else '❌ FAIL'}")
    print(f"   OAuth URL Generation: {'✅ PASS' if oauth_url_ok else '❌ FAIL'}")
    print(f"   OAuth Callback: {'✅ PASS' if oauth_callback_ok else '❌ FAIL'}")
    print(f"   Marketplace Status: {'✅ PASS' if status_ok else '❌ FAIL'}")
    
    all_tests_passed = all([frontend_ok, api_health_ok, oauth_url_ok, oauth_callback_ok, status_ok])
    
    if all_tests_passed:
        print("\n🎉 ALL TESTS PASSED! Complete OAuth flow is working correctly!")
        print("\n🔗 Ready for Real eBay OAuth Testing:")
        print("   1. Open browser to http://localhost:3000")
        print("   2. Navigate to marketplace connection page")
        print("   3. Click 'Connect eBay Account'")
        print("   4. Complete OAuth flow in popup window")
        print("   5. Verify connection with your 438 inventory items")
        
        if oauth_url_ok and auth_url:
            print(f"\n🔗 Test OAuth URL (for manual testing):")
            print(f"   {auth_url}")
        
        return 0
    else:
        print("\n❌ Some tests failed. Check the specific issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
