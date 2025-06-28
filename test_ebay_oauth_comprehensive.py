#!/usr/bin/env python3
"""
Comprehensive eBay OAuth Integration Test
Tests the complete OAuth flow and investigates routing issues
"""
import requests
import json
import sys
import time
from urllib.parse import urlparse, parse_qs


def test_oauth_url_generation():
    """Test OAuth URL generation with real eBay scopes"""
    print("🔍 Testing eBay OAuth URL Generation...")

    url_endpoint = "http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize"

    # Use the actual scopes from your eBay app
    test_data = {
        "scopes": [
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.marketing",
            "https://api.ebay.com/oauth/api_scope/sell.account",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
            "https://api.ebay.com/oauth/api_scope/sell.analytics",
            "https://api.ebay.com/oauth/api_scope/sell.finances",
            "https://api.ebay.com/oauth/api_scope/commerce.identity",
        ]
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    try:
        print(f"📡 Sending POST request to: {url_endpoint}")

        response = requests.post(
            url_endpoint, json=test_data, headers=headers, timeout=10
        )

        print(f"📊 Response Status: {response.status_code}")

        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"📋 Response Data: {json.dumps(response_data, indent=2)}")

                if (
                    "data" in response_data
                    and "authorization_url" in response_data["data"]
                ):
                    auth_url = response_data["data"]["authorization_url"]
                    print(f"✅ Authorization URL generated: {auth_url[:100]}...")

                    # Parse the URL to verify it contains expected parameters
                    parsed_url = urlparse(auth_url)
                    query_params = parse_qs(parsed_url.query)

                    print(f"🔍 URL Analysis:")
                    print(f"   Domain: {parsed_url.netloc}")
                    print(f"   Path: {parsed_url.path}")
                    print(
                        f"   Client ID: {query_params.get('client_id', ['Not found'])[0]}"
                    )
                    print(
                        f"   Redirect URI: {query_params.get('redirect_uri', ['Not found'])[0]}"
                    )
                    print(
                        f"   State: {query_params.get('state', ['Not found'])[0][:20]}..."
                    )

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


def test_oauth_callback_with_mock_data():
    """Test OAuth callback with realistic mock data"""
    print("\n🔍 Testing eBay OAuth Callback with Mock Data...")

    callback_url = "http://localhost:8001/api/v1/marketplace/ebay/oauth/callback"

    # Mock data that would come from eBay
    test_data = {
        "code": "v^1.1#i^1#r^0#p^3#I^3#f^0#t^H4sIAAAAAAAAAOVYa2wUVRTu9gG0FLBQwEcQH4iKj5m5M3dm7sy9M3e2nZ3Z7nZ2u91uu",
        "state": "test_state_" + str(int(time.time())),
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    try:
        print(f"📡 Sending POST request to: {callback_url}")
        print(f"📦 Payload: {json.dumps(test_data, indent=2)}")

        response = requests.post(
            callback_url, json=test_data, headers=headers, timeout=10
        )

        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")

        if response.status_code == 200:
            print("✅ OAuth callback endpoint is responding!")

            # Check if we're getting the Flutter app (which means routing issue)
            if "flutter" in response.text.lower() or "<!DOCTYPE html>" in response.text:
                print("⚠️  WARNING: Getting Flutter app instead of API response")
                print(
                    "🔍 This indicates a routing issue - the request is not reaching the API"
                )
                return False
            else:
                try:
                    response_data = response.json()
                    print(f"📋 API Response: {json.dumps(response_data, indent=2)}")
                    return True
                except:
                    print(f"📋 Response Text: {response.text[:200]}...")
                    return True
        else:
            print(f"❌ OAuth callback failed with status {response.status_code}")
            print(f"📋 Response Text: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing OAuth callback: {e}")
        return False


def test_api_routing():
    """Test API routing to identify issues"""
    print("\n🔍 Testing API Routing...")

    test_endpoints = [
        "/health",
        "/api/v1/health",
        "/api/v1/marketplace/ebay/status",
        "/api/v1/marketplace/ebay/oauth/authorize",
        "/api/v1/marketplace/ebay/oauth/callback",
    ]

    base_url = "http://localhost:8001"

    for endpoint in test_endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"📡 Testing: {url}")

            response = requests.get(url, timeout=5)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                if (
                    "flutter" in response.text.lower()
                    or "<!DOCTYPE html>" in response.text
                ):
                    print("   Type: Flutter App (routing issue)")
                else:
                    try:
                        data = response.json()
                        print(
                            f"   Type: API Response - {data.get('status', 'unknown')}"
                        )
                    except:
                        print("   Type: API Response (non-JSON)")
            elif response.status_code == 404:
                print("   Type: Not Found")
            elif response.status_code == 405:
                print("   Type: Method Not Allowed (endpoint exists)")
            else:
                print(f"   Type: Error ({response.status_code})")

        except Exception as e:
            print(f"   Error: {e}")

        print()


def test_marketplace_status():
    """Test marketplace status endpoint"""
    print("🔍 Testing Marketplace Status...")

    status_url = "http://localhost:8001/api/v1/marketplace/ebay/status"

    try:
        response = requests.get(status_url, timeout=10)
        print(f"📊 Status Response: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📋 Status Data: {json.dumps(data, indent=2)}")
                return True
            except:
                print(f"📋 Status Text: {response.text}")
                return False
        else:
            print(f"❌ Status check failed: {response.status_code}")
            print(f"📋 Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error checking status: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Comprehensive eBay OAuth Integration Test")
    print("=" * 60)

    # Test API routing first
    test_api_routing()

    # Test OAuth URL generation
    url_success, auth_url = test_oauth_url_generation()

    # Test OAuth callback
    callback_success = test_oauth_callback_with_mock_data()

    # Test marketplace status
    status_success = test_marketplace_status()

    print("\n" + "=" * 60)
    print("📊 Comprehensive Test Results:")
    print(f"   OAuth URL Generation: {'✅ PASS' if url_success else '❌ FAIL'}")
    print(f"   OAuth Callback: {'✅ PASS' if callback_success else '❌ FAIL'}")
    print(f"   Marketplace Status: {'✅ PASS' if status_success else '❌ FAIL'}")

    if url_success and callback_success and status_success:
        print("\n🎉 All tests passed! eBay OAuth integration is working correctly.")
        print("\n🔗 Next Steps:")
        print("   1. Test with real eBay OAuth flow")
        print("   2. Verify token storage in Redis")
        print("   3. Test inventory retrieval (438 items)")
        return 0
    else:
        print("\n❌ Some tests failed. Issues identified:")
        if not url_success:
            print("   - OAuth URL generation issues")
        if not callback_success:
            print("   - OAuth callback routing issues")
        if not status_success:
            print("   - Marketplace status endpoint issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())
