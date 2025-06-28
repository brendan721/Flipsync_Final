#!/usr/bin/env python3
"""
eBay OAuth URL Generator
Generates the correct OAuth consent URL for your specific sandbox application
"""

import os
import sys
import urllib.parse
from typing import List


def generate_ebay_oauth_url() -> str:
    """Generate the correct eBay OAuth consent URL for sandbox."""

    # Get sandbox credentials
    client_id = os.getenv("SB_EBAY_APP_ID")
    if not client_id:
        print("❌ Error: SB_EBAY_APP_ID not found in environment")
        sys.exit(1)

    # eBay sandbox OAuth endpoint
    auth_base_url = "https://auth.sandbox.ebay.com/oauth2/authorize"

    # Redirect URI - using standard callback URL approach
    # This should match the "Auth Accepted URL" in your eBay RuName configuration
    redirect_uri = "https://nashvillegeneral.store/ebay-oauth"

    # Comprehensive scopes for FlipSync functionality
    scopes = [
        # Core API access
        "https://api.ebay.com/oauth/api_scope",
        # Inventory management (critical for FlipSync)
        "https://api.ebay.com/oauth/api_scope/sell.inventory",
        "https://api.ebay.com/oauth/api_scope/sell.inventory.readonly",
        # Order fulfillment (critical for FlipSync)
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
        "https://api.ebay.com/oauth/api_scope/sell.fulfillment.readonly",
        # Listing management (critical for FlipSync)
        "https://api.ebay.com/oauth/api_scope/sell.item",
        "https://api.ebay.com/oauth/api_scope/sell.item.draft",
        # Account management
        "https://api.ebay.com/oauth/api_scope/sell.account",
        "https://api.ebay.com/oauth/api_scope/sell.account.readonly",
        # Marketing and promotions
        "https://api.ebay.com/oauth/api_scope/sell.marketing",
        "https://api.ebay.com/oauth/api_scope/sell.marketing.readonly",
        # Analytics and insights
        "https://api.ebay.com/oauth/api_scope/sell.analytics.readonly",
        "https://api.ebay.com/oauth/api_scope/sell.marketplace.insights.readonly",
        # Commerce and catalog
        "https://api.ebay.com/oauth/api_scope/commerce.catalog.readonly",
        "https://api.ebay.com/oauth/api_scope/commerce.identity.readonly",
        # Financial data
        "https://api.ebay.com/oauth/api_scope/sell.finances",
        # Reputation management
        "https://api.ebay.com/oauth/api_scope/sell.reputation",
        "https://api.ebay.com/oauth/api_scope/sell.reputation.readonly",
    ]

    # Build OAuth parameters
    oauth_params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": "flipsync_sandbox_oauth",  # Custom state for tracking
    }

    # Build the complete URL
    query_string = urllib.parse.urlencode(oauth_params)
    oauth_url = f"{auth_base_url}?{query_string}"

    return oauth_url


def print_instructions(oauth_url: str):
    """Print detailed instructions for the OAuth flow."""

    print("🔐 eBay Sandbox OAuth Setup Instructions")
    print("=" * 60)
    print()
    print("STEP 1: Configure Redirect URI in eBay Developer Console")
    print("   1. Go to: https://developer.ebay.com/my/keys")
    print("   2. Select your sandbox application")
    print("   3. Under 'User tokens', add this redirect URI:")
    print(
        f"      {os.getenv('EBAY_REDIRECT_URI', 'https://nashvillegeneral.store/ebay-oauth')}"
    )
    print("   4. Save the configuration")
    print()

    print("STEP 2: Complete OAuth Flow")
    print("   1. Open this URL in your browser:")
    print()
    print(f"   {oauth_url}")
    print()
    print("   2. Sign in with your eBay sandbox test account")
    print("   3. Grant permissions to your application")
    print("   4. You'll be redirected to your callback URL with an authorization code")
    print("   5. Copy the 'code' parameter from the redirect URL")
    print()

    print("STEP 3: Exchange Code for Refresh Token")
    print("   1. Run: python exchange_oauth_code.py <authorization_code>")
    print("   2. This will give you a proper refresh token for your app")
    print()

    print("📋 What to look for in the redirect URL:")
    print("   https://nashvillegeneral.store/callback?code=v^1.1#i^1#...")
    print("   Copy everything after 'code=' and before any '&' character")
    print()

    print("⚠️  Important Notes:")
    print("   - Use a sandbox eBay account for testing")
    print("   - The authorization code expires quickly (use within 5 minutes)")
    print("   - The refresh token will be tied to your specific client credentials")
    print()


def main():
    """Main function."""
    print("🚀 Generating eBay OAuth URL for FlipSync Sandbox Integration")
    print()

    # Check environment
    client_id = os.getenv("SB_EBAY_APP_ID")
    if not client_id:
        print("❌ Error: Please ensure SB_EBAY_APP_ID is set in your .env file")
        sys.exit(1)

    print(f"✅ Using Client ID: {client_id}")
    print(
        f"✅ Using Redirect URI: {os.getenv('EBAY_REDIRECT_URI', 'https://nashvillegeneral.store/ebay-oauth')}"
    )
    print()

    # Generate OAuth URL
    oauth_url = generate_ebay_oauth_url()

    # Print instructions
    print_instructions(oauth_url)

    # Save URL to file for easy access
    with open("ebay_oauth_url.txt", "w") as f:
        f.write(oauth_url)

    print("💾 OAuth URL saved to: ebay_oauth_url.txt")
    print()
    print("🎯 Next Step: Follow the instructions above to complete the OAuth flow")


if __name__ == "__main__":
    main()
