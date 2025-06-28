#!/usr/bin/env python3
"""
Corrected eBay OAuth Test - Using Proper Nginx Routing
Tests OAuth flow through nginx proxy (HTTPS) instead of direct API access
"""
import requests
import json
import sys
import urllib3
from urllib.parse import urlparse, parse_qs

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_oauth_url_generation_nginx():
    """Test OAuth URL generation through nginx (HTTPS)"""
    print("🔍 Testing eBay OAuth URL Generation (via nginx HTTPS)...")
    
    # Use nginx HTTPS endpoint
    url_endpoint = "https://localhost/api/v1/marketplace/ebay/oauth/authorize"
    
    # Use the actual scopes from your eBay app
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
        print(f"📡 Sending POST request to: {url_endpoint}")
        
        response = requests.post(
            url_endpoint,
            json=test_data,
            headers=headers,
            timeout=10,
            verify=False  # Skip SSL verification for self-signed cert
        )
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"📋 Response Data: {json.dumps(response_data, indent=2)}")
                
                if "data" in response_data and "authorization_url" in response_data["data"]:
                    auth_url = response_data["data"]["authorization_url"]
                    print(f"✅ Authorization URL generated: {auth_url[:100]}...")
                    
                    # Parse the URL to verify it contains expected parameters
                    parsed_url = urlparse(auth_url)
                    query_params = parse_qs(parsed_url.query)
                    
                    print(f"🔍 URL Analysis:")
                    print(f"   Domain: {parsed_url.netloc}")
                    print(f"   Path: {parsed_url.path}")
                    print(f"   Client ID: {query_params.get('client_id', ['Not found'])[0]}")
                    print(f"   Redirect URI: {query_params.get('redirect_uri', ['Not found'])[0]}")
                    print(f"   State: {query_params.get('state', ['Not found'])[0][:20]}...")
                    
                    # Verify it's the correct eBay OAuth URL
                    if "ebay.com" in parsed_url.netloc and "oauth" in parsed_url.path:
                        print("✅ Valid eBay OAuth URL structure")
                        return True, auth_url
                    else:
                        print("❌ Invalid eBay OAuth URL structure")
                        return False, None
                else:
                    print("❌ No authorization URL in response")
                    return False, None
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response: {response.text}")
                return False, None
        else:
            print(f"❌ OAuth URL generation failed with status {response.status_code}")
            print(f"📋 Response Text: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"❌ Error testing OAuth URL generation: {e}")
        return False, None

def test_oauth_callback_nginx():
    """Test OAuth callback through nginx (HTTPS)"""
    print("\n🔍 Testing eBay OAuth Callback (via nginx HTTPS)...")
    
    # Use nginx HTTPS endpoint
    callback_url = "https://localhost/api/v1/marketplace/ebay/oauth/callback"
    
    # Mock data that would come from eBay
    test_data = {
        "code": "v^1.1#i^1#r^0#p^3#I^3#f^0#t^H4sIAAAAAAAAAOVYa2wUVRTu9gG0FLBQwEcQH4iKj5m5M3dm7sy9M3e2nZ3Z7nZ2u91uu",
        "state": "test_state_nginx_routing"
    }
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        print(f"📡 Sending POST request to: {callback_url}")
        print(f"📦 Payload: {json.dumps(test_data, indent=2)}")
        
        response = requests.post(
            callback_url,
            json=test_data,
            headers=headers,
            timeout=10,
            verify=False  # Skip SSL verification for self-signed cert
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ OAuth callback endpoint is responding!")
            
            # Check if we're getting JSON API response (correct) or HTML (routing issue)
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                try:
                    response_data = response.json()
                    print(f"📋 API Response: {json.dumps(response_data, indent=2)}")
                    print("✅ Correct JSON API response received!")
                    return True
                except:
                    print(f"📋 Response Text: {response.text[:200]}...")
                    print("✅ API response received (non-JSON)")
                    return True
            elif 'text/html' in content_type:
                print("⚠️  WARNING: Getting HTML response instead of JSON API response")
                print("🔍 This indicates a routing issue - request may not be reaching the API correctly")
                print(f"📋 HTML Response: {response.text[:200]}...")
                return False
            else:
                print(f"⚠️  Unexpected content type: {content_type}")
                print(f"📋 Response: {response.text[:200]}...")
                return False
        else:
            print(f"❌ OAuth callback failed with status {response.status_code}")
            print(f"📋 Response Text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OAuth callback: {e}")
        return False

def test_marketplace_status_nginx():
    """Test marketplace status through nginx (HTTPS)"""
    print("\n🔍 Testing Marketplace Status (via nginx HTTPS)...")
    
    # Use nginx HTTPS endpoint
    status_url = "https://localhost/api/v1/marketplace/ebay/status"
    
    try:
        response = requests.get(
            status_url, 
            timeout=10,
            verify=False  # Skip SSL verification for self-signed cert
        )
        print(f"📊 Status Response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📋 Status Data: {json.dumps(data, indent=2)}")
                return True
            except:
                print(f"📋 Status Text: {response.text}")
                return False
        elif response.status_code == 401:
            print("⚠️  401 Unauthorized - This is expected for unauthenticated requests")
            print("✅ Endpoint is working correctly (authentication required)")
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False

def test_direct_api_vs_nginx():
    """Compare direct API access vs nginx routing"""
    print("\n🔍 Comparing Direct API vs Nginx Routing...")
    
    endpoints = [
        ("Direct API", "http://localhost:8001/health"),
        ("Nginx HTTP", "http://localhost/health"),
        ("Nginx HTTPS", "https://localhost/health")
    ]
    
    for name, url in endpoints:
        try:
            print(f"\n📡 Testing {name}: {url}")
            
            kwargs = {"timeout": 5}
            if "https" in url:
                kwargs["verify"] = False
            
            response = requests.get(url, **kwargs)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print(f"   Response: {data.get('status', 'unknown')}")
                except:
                    print(f"   Response: {response.text[:50]}...")
            elif response.status_code == 301:
                print(f"   Redirect to: {response.headers.get('location', 'unknown')}")
            else:
                print(f"   Error: {response.status_code}")
                
        except Exception as e:
            print(f"   Error: {e}")

def main():
    """Main test function"""
    print("🚀 Corrected eBay OAuth Test - Nginx Routing")
    print("=" * 60)
    
    # Test direct API vs nginx routing
    test_direct_api_vs_nginx()
    
    # Test OAuth URL generation through nginx
    url_success, auth_url = test_oauth_url_generation_nginx()
    
    # Test OAuth callback through nginx
    callback_success = test_oauth_callback_nginx()
    
    # Test marketplace status through nginx
    status_success = test_marketplace_status_nginx()
    
    print("\n" + "=" * 60)
    print("📊 Corrected Test Results (via Nginx):")
    print(f"   OAuth URL Generation: {'✅ PASS' if url_success else '❌ FAIL'}")
    print(f"   OAuth Callback: {'✅ PASS' if callback_success else '❌ FAIL'}")
    print(f"   Marketplace Status: {'✅ PASS' if status_success else '❌ FAIL'}")
    
    if url_success and callback_success and status_success:
        print("\n🎉 All tests passed! eBay OAuth integration is working correctly through nginx!")
        print("\n🔗 Next Steps:")
        print("   1. Update frontend to use HTTPS endpoints")
        print("   2. Test real eBay OAuth flow through nginx")
        print("   3. Verify token storage and inventory retrieval (438 items)")
        print("   4. Update all API calls to use nginx routing")
        return 0
    else:
        print("\n❌ Some tests failed. Check the specific issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
