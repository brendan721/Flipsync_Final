#!/usr/bin/env python3
"""
Test script to verify eBay OAuth fix
"""
import requests
import json
import sys


def test_oauth_callback():
    """Test the eBay OAuth callback endpoint with a sample auth code"""
    print("🔍 Testing eBay OAuth Callback Fix...")

    # Test the callback with a sample authorization code
    callback_url = "http://localhost:8001/api/v1/marketplace/ebay/oauth/callback"

    # Sample data (this would normally come from eBay)
    test_data = {"code": "test_auth_code_12345", "state": "test_state_67890"}

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
            print("✅ OAuth callback endpoint is responding correctly!")
            try:
                response_data = response.json()
                print(f"📋 Response Data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"📋 Response Text: {response.text}")
        else:
            print(f"❌ OAuth callback failed with status {response.status_code}")
            print(f"📋 Response Text: {response.text}")

            # Check if the old error is still present
            if (
                "exchange_authorization_code() got an unexpected keyword argument 'redirect_uri'"
                in response.text
            ):
                print(
                    "🚨 OLD ERROR STILL PRESENT: Function signature mismatch detected!"
                )
                return False
            elif "ebay_oauth_callback_redirect" in response.text:
                print("🚨 OLD ERROR STILL PRESENT: Old function name detected!")
                return False
            else:
                print("✅ Old error is resolved, but there may be other issues")

    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the API server running?")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

    return True


def test_oauth_url_generation():
    """Test the OAuth URL generation endpoint"""
    print("\n🔍 Testing eBay OAuth URL Generation...")

    url_endpoint = "http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize"

    test_data = {
        "scopes": [
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.marketing",
            "https://api.ebay.com/oauth/api_scope/sell.account",
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
            print("✅ OAuth URL generation is working!")
            try:
                response_data = response.json()
                if "authorization_url" in response_data.get("data", {}):
                    print("✅ Authorization URL generated successfully")
                    return True
                else:
                    print("❌ No authorization URL in response")
                    return False
            except:
                print(f"❌ Invalid JSON response: {response.text}")
                return False
        else:
            print(f"❌ OAuth URL generation failed with status {response.status_code}")
            print(f"📋 Response Text: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing OAuth URL generation: {e}")
        return False


def main():
    """Main test function"""
    print("🚀 Testing eBay OAuth Fix")
    print("=" * 50)

    # Test OAuth URL generation first
    url_test_passed = test_oauth_url_generation()

    # Test OAuth callback
    callback_test_passed = test_oauth_callback()

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   OAuth URL Generation: {'✅ PASS' if url_test_passed else '❌ FAIL'}")
    print(f"   OAuth Callback: {'✅ PASS' if callback_test_passed else '❌ FAIL'}")

    if url_test_passed and callback_test_passed:
        print("\n🎉 All tests passed! eBay OAuth fix appears to be working.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
