#!/usr/bin/env python3
"""
eBay OAuth Code Exchange
Exchanges authorization code for refresh token
"""

import os
import sys
import asyncio
import aiohttp
import json
import base64
from typing import Dict, Any


async def exchange_code_for_token(auth_code: str) -> Dict[str, Any]:
    """Exchange authorization code for access and refresh tokens."""

    # Get sandbox credentials
    client_id = os.getenv("SB_EBAY_APP_ID")
    client_secret = os.getenv("SB_EBAY_CERT_ID")
    redirect_uri = "Brendan_Blomfie-BrendanB-Nashvi-pzkbhtbtg"  # Your working RuName

    if not client_id or not client_secret:
        raise ValueError(
            "Missing sandbox credentials: SB_EBAY_APP_ID or SB_EBAY_CERT_ID"
        )

    # eBay token endpoint
    token_endpoint = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"

    # Prepare credentials for Basic Auth
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    # Request headers
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    # Request data
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
    }

    print(f"🔄 Exchanging authorization code for tokens...")
    print(f"   Client ID: {client_id}")
    print(f"   Redirect URI: {redirect_uri}")
    print(f"   Token Endpoint: {token_endpoint}")
    print()

    async with aiohttp.ClientSession() as session:
        async with session.post(
            token_endpoint,
            data=data,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as response:
            response_text = await response.text()

            if response.status == 200:
                token_data = json.loads(response_text)
                return token_data
            else:
                print(f"❌ Token exchange failed: HTTP {response.status}")
                print(f"   Response: {response_text}")

                # Try to parse error details
                try:
                    error_data = json.loads(response_text)
                    if "error_description" in error_data:
                        print(f"   Error: {error_data['error_description']}")
                except:
                    pass

                raise Exception(f"Token exchange failed with status {response.status}")


def update_env_file(refresh_token: str):
    """Update .env file with the new refresh token."""

    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"❌ Error: {env_file} not found")
        return False

    # Read current .env content
    with open(env_file, "r") as f:
        lines = f.readlines()

    # Update or add the sandbox refresh token
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("SB_EBAY_REFRESH_TOKEN="):
            lines[i] = f"SB_EBAY_REFRESH_TOKEN={refresh_token}\n"
            updated = True
            break

    # If not found, add it after the other eBay credentials
    if not updated:
        for i, line in enumerate(lines):
            if line.startswith("SB_EBAY_CERT_ID="):
                lines.insert(i + 1, f"SB_EBAY_REFRESH_TOKEN={refresh_token}\n")
                updated = True
                break

    if updated:
        # Write back to file
        with open(env_file, "w") as f:
            f.writelines(lines)
        print(f"✅ Updated {env_file} with new refresh token")
        return True
    else:
        print(f"❌ Could not update {env_file}")
        return False


async def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("❌ Usage: python exchange_oauth_code.py <authorization_code>")
        print()
        print("Example:")
        print("   python exchange_oauth_code.py 'v^1.1#i^1#f^0#I^3#r^1#t^...'")
        print()
        print("💡 Get the authorization code by following the OAuth flow:")
        print("   1. Run: python generate_ebay_oauth_url.py")
        print("   2. Follow the instructions to get the authorization code")
        sys.exit(1)

    auth_code = sys.argv[1].strip()

    print("🔐 eBay OAuth Code Exchange for FlipSync")
    print("=" * 50)
    print()

    try:
        # Exchange code for tokens
        token_data = await exchange_code_for_token(auth_code)

        print("✅ Token exchange successful!")
        print()
        print("📋 Token Details:")
        print(f"   Access Token: {token_data.get('access_token', 'N/A')[:50]}...")
        print(f"   Refresh Token: {token_data.get('refresh_token', 'N/A')[:50]}...")
        print(f"   Token Type: {token_data.get('token_type', 'N/A')}")
        print(f"   Expires In: {token_data.get('expires_in', 'N/A')} seconds")

        if "scope" in token_data:
            print(f"   Scopes: {token_data['scope']}")

        print()

        # Update .env file
        refresh_token = token_data.get("refresh_token")
        if refresh_token:
            if update_env_file(refresh_token):
                print(
                    "🎉 Success! Your .env file has been updated with the new refresh token."
                )
                print()
                print("🧪 Next Steps:")
                print("   1. Run: python test_ebay_sandbox_connectivity.py")
                print("   2. Verify that all tests now pass")
                print("   3. Proceed with eBay agent integration testing")
            else:
                print("⚠️  Please manually add this refresh token to your .env file:")
                print(f"   SB_EBAY_REFRESH_TOKEN={refresh_token}")
        else:
            print("❌ No refresh token received in response")

    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("🔧 Troubleshooting:")
        print("   1. Ensure the authorization code is correct and not expired")
        print("   2. Check that your redirect URI matches your eBay app configuration")
        print("   3. Verify your sandbox credentials are correct")
        print("   4. Make sure you're using a sandbox eBay account")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
