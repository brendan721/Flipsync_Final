#!/usr/bin/env python3
"""
Debug eBay OAuth Configuration
Helps identify the exact configuration mismatch
"""

import asyncio
import os
import sys
import aiohttp
import json
import base64
from typing import Dict, Any


async def test_multiple_redirect_uris(auth_code: str) -> Dict[str, Any]:
    """Test token exchange with different redirect URIs to find the correct one."""

    client_id = os.getenv("SB_EBAY_APP_ID")
    client_secret = os.getenv("SB_EBAY_CERT_ID")
    token_endpoint = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

    # Different redirect URIs to test
    redirect_uris_to_test = [
        "https://nashvillegeneral.store/callback",
        "Brendan_Blomfie-BrendanB-Nashvi-vedxxymbs",
        "Brendan_Blomfie-BrendanB-Nashvi-lkajdgn",
        "https://nashvillegeneral.store/ebay-oauth",
        "https://signin.sandbox.ebay.com/ws/eBayISAPI.dll",
    ]

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    results = {}

    print("🔍 Testing different redirect URIs...")
    print(f"   Client ID: {client_id}")
    print(f"   Auth Code: {auth_code[:30]}...")
    print()

    async with aiohttp.ClientSession() as session:
        for redirect_uri in redirect_uris_to_test:
            print(f"🧪 Testing redirect URI: {redirect_uri}")

            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": redirect_uri,
            }

            try:
                async with session.post(
                    token_endpoint,
                    data=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    response_text = await response.text()

                    if response.status == 200:
                        print(f"   ✅ SUCCESS with {redirect_uri}")
                        token_data = json.loads(response_text)
                        results[redirect_uri] = {
                            "status": "success",
                            "data": token_data,
                        }
                        break  # Found the working one
                    else:
                        print(f"   ❌ Failed: {response.status}")
                        try:
                            error_data = json.loads(response_text)
                            error_msg = error_data.get(
                                "error_description", "Unknown error"
                            )
                            print(f"      Error: {error_msg}")
                            results[redirect_uri] = {
                                "status": "failed",
                                "error": error_msg,
                            }
                        except:
                            results[redirect_uri] = {
                                "status": "failed",
                                "error": response_text,
                            }

            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results[redirect_uri] = {"status": "exception", "error": str(e)}

    return results


async def get_fresh_oauth_url_from_console():
    """Help user get the exact OAuth URL from their eBay console."""

    print("🔗 Let's get the exact OAuth URL from your eBay developer console")
    print("=" * 60)
    print()
    print("📋 STEPS:")
    print("1. Go to: https://developer.ebay.com/my/keys")
    print("2. Select your sandbox application")
    print("3. Find your RuName: Brendan_Blomfie-BrendanB-Nashvi-vedxxymbs")
    print("4. Look for 'Your branded eBay Sandbox Sign In (OAuth)'")
    print("5. Copy the COMPLETE OAuth URL (click 'See all' if truncated)")
    print()

    oauth_url = input("🔗 Paste the complete OAuth URL from your console: ").strip()

    if oauth_url and "oauth2/authorize" in oauth_url:
        print("✅ OAuth URL received!")

        # Extract redirect_uri from the URL
        try:
            from urllib.parse import urlparse, parse_qs

            parsed = urlparse(oauth_url)
            params = parse_qs(parsed.query)
            redirect_uri = params.get("redirect_uri", [""])[0]

            print(f"📊 Extracted redirect_uri: {redirect_uri}")
            return redirect_uri
        except Exception as e:
            print(f"⚠️ Could not parse URL: {e}")
            return None
    else:
        print("❌ Invalid OAuth URL")
        return None


async def main():
    """Main diagnostic function."""
    if len(sys.argv) < 2:
        print("❌ Usage: python debug_ebay_oauth.py <authorization_code>")
        print("   Or: python debug_ebay_oauth.py --get-console-url")
        sys.exit(1)

    if sys.argv[1] == "--get-console-url":
        redirect_uri = await get_fresh_oauth_url_from_console()
        if redirect_uri:
            print(f"💡 Use this redirect_uri in your exchange script: {redirect_uri}")
        return

    auth_code = sys.argv[1].strip()

    print("🔍 eBay OAuth Configuration Debugger")
    print("=" * 50)
    print()

    # Test multiple redirect URIs
    results = await test_multiple_redirect_uris(auth_code)

    print()
    print("📊 RESULTS SUMMARY:")
    print("=" * 30)

    success_found = False
    for redirect_uri, result in results.items():
        status = result["status"]
        if status == "success":
            print(f"✅ WORKING: {redirect_uri}")
            print(
                f"   Refresh Token: {result['data'].get('refresh_token', 'N/A')[:50]}..."
            )
            success_found = True
        else:
            print(f"❌ FAILED: {redirect_uri}")
            print(f"   Error: {result.get('error', 'Unknown')}")

    if not success_found:
        print()
        print("🔧 TROUBLESHOOTING:")
        print("1. The authorization code might be expired (they expire in ~5 minutes)")
        print("2. There might be a configuration mismatch in your eBay console")
        print("3. Try getting a fresh authorization code")
        print()
        print("💡 To get the exact OAuth URL from your console:")
        print("   python debug_ebay_oauth.py --get-console-url")
    else:
        print()
        print("🎉 Found working configuration! Update your scripts accordingly.")


if __name__ == "__main__":
    asyncio.run(main())
